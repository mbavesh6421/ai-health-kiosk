import math
import re
import time
import httpx
from fastapi import APIRouter, HTTPException, Query
from ..config import settings

router = APIRouter(prefix="/locator", tags=["PHC Locator"])

# Several public Overpass mirrors. If one is busy we try the next.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

GOVT_HINT = re.compile(
    r"\b(phc|chc|uphc|primary health|community health|govt|government|district|civil hospital|"
    r"area hospital|general hospital|esi|urban health)\b", re.I)

_cache: dict[tuple, tuple[float, dict]] = {}   # small in-memory cache (10 min)
CACHE_TTL = 600


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _type_label(tags: dict) -> str:
    amenity, hc = tags.get("amenity"), tags.get("healthcare")
    if amenity == "hospital" or hc == "hospital":
        return "Hospital"
    if amenity == "clinic" or hc in ("clinic", "centre"):
        return "Clinic / Health centre"
    if amenity == "doctors" or hc == "doctor":
        return "Doctor"
    return "Health facility"


def _address(tags: dict) -> str | None:
    if tags.get("addr:full"):
        return tags["addr:full"]
    parts = [tags.get(k) for k in ("addr:housenumber", "addr:street", "addr:suburb",
                                   "addr:city", "addr:postcode") if tags.get(k)]
    return ", ".join(parts) or None


def _parse(elements: list, lat: float, lon: float) -> list[dict]:
    seen, out = set(), []
    for el in elements:
        tags = el.get("tags", {})
        flat = el.get("lat", (el.get("center") or {}).get("lat"))
        flon = el.get("lon", (el.get("center") or {}).get("lon"))
        if flat is None or flon is None:
            continue
        name = tags.get("name:en") or tags.get("name") or tags.get("operator")
        key = ((name or "").lower(), round(flat, 4), round(flon, 4))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "name": name or f"Unnamed {_type_label(tags).lower()}",
            "named": bool(name),
            "type": _type_label(tags),
            "lat": flat, "lon": flon,
            "distance_km": round(haversine_km(lat, lon, flat, flon), 2),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "address": _address(tags),
            "website": tags.get("website") or tags.get("contact:website"),
            "opening_hours": tags.get("opening_hours"),
            "emergency": tags.get("emergency") == "yes",
            "govt": bool(tags.get("operator:type") == "government" or GOVT_HINT.search(name or "")),
            "osm_id": f"{el.get('type', 'n')[0]}{el.get('id')}",
        })
    # named places first, then nearest
    out.sort(key=lambda f: (not f["named"], f["distance_km"]))
    return out


async def _overpass(lat: float, lon: float, radius_m: int) -> list[dict]:
    query = f"""
    [out:json][timeout:25];
    (
      nwr["amenity"~"^(hospital|clinic|doctors)$"](around:{radius_m},{lat},{lon});
      nwr["healthcare"~"^(hospital|clinic|centre|doctor)$"](around:{radius_m},{lat},{lon});
    );
    out center tags 150;
    """
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    last_exc = None
    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in OVERPASS_MIRRORS:
            try:
                resp = await client.post(url, data={"data": query}, headers=headers)
                resp.raise_for_status()
                return _parse(resp.json().get("elements", []), lat, lon)
            except Exception as exc:
                last_exc = exc
                print(f"[locator] Overpass mirror failed ({url}): {exc}")
    raise RuntimeError(f"All Overpass mirrors failed: {last_exc}")


async def _nominatim(lat: float, lon: float, radius_km: float) -> list[dict]:
    """Fallback: bounded Nominatim search inside a box around the user."""
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(math.cos(math.radians(lat)), 0.2))
    viewbox = f"{lon - dlon},{lat + dlat},{lon + dlon},{lat - dlat}"
    headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}
    results = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for q in ("hospital", "clinic", "primary health centre"):
            resp = await client.get(f"{settings.NOMINATIM_URL}/search", headers=headers, params={
                "q": q, "format": "jsonv2", "viewbox": viewbox, "bounded": 1, "limit": 10,
            })
            resp.raise_for_status()
            for item in resp.json():
                flat, flon = float(item["lat"]), float(item["lon"])
                name = item.get("name") or item.get("display_name", "").split(",")[0]
                results.append({
                    "name": name or "Health facility", "named": bool(name),
                    "type": (item.get("type") or "facility").replace("_", " ").title(),
                    "lat": flat, "lon": flon,
                    "distance_km": round(haversine_km(lat, lon, flat, flon), 2),
                    "phone": None, "address": item.get("display_name"), "website": None,
                    "opening_hours": None, "emergency": False,
                    "govt": bool(GOVT_HINT.search(name or "")),
                    "osm_id": f"{item.get('osm_type', 'n')[0]}{item.get('osm_id')}",
                })
    uniq = {(f["name"].lower(), round(f["lat"], 4), round(f["lon"], 4)): f for f in results}
    return sorted(uniq.values(), key=lambda f: f["distance_km"])


@router.get("")
async def locate_health_facilities(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10.0, ge=1, le=50),
):
    """
    Nearest hospitals / clinics / PHCs from OpenStreetMap (free, no key).
    Queries nodes AND building outlines (many Indian hospitals are mapped as areas),
    widens the search radius automatically if the first pass finds too little,
    and returns results sorted by real distance with phone / address when known.
    """
    ckey = (round(lat, 3), round(lon, 3), radius_km)
    hit = _cache.get(ckey)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return hit[1]

    used_radius, facilities, source, overpass_err = radius_km, [], "overpass", None
    try:
        for r in dict.fromkeys([radius_km, min(radius_km * 2, 50), 50.0]):
            used_radius = r
            facilities = await _overpass(lat, lon, int(r * 1000))
            if len(facilities) >= 5:
                break
    except Exception as exc:
        overpass_err = exc

    if not facilities:
        try:
            source = "nominatim"
            facilities = await _nominatim(lat, lon, max(radius_km, 15))
        except Exception as exc:
            if overpass_err:
                raise HTTPException(
                    status_code=503,
                    detail=f"Map services are busy right now, please retry in a minute. ({overpass_err}; {exc})",
                )
            facilities = []

    payload = {"source": source, "radius_km": used_radius,
               "count": len(facilities[:15]), "facilities": facilities[:15]}
    if facilities:
        _cache[ckey] = (time.time(), payload)
    return payload