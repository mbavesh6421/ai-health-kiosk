"""
Static, no-network dataset that powers:
 - /offline (basic cached chatbot responses for the offline-mode toggle)
 - the fallback path of /symptom-checker when the HF model is unreachable
 - the fallback path of /education
 - the "urgent" safety-net keyword check that ALWAYS runs, even when the
   model is live, so a red-flag symptom is never missed because of a
   model hallucination.
"""

EMERGENCY_KEYWORDS = [
    "chest pain", "difficulty breathing", "can't breathe", "severe bleeding",
    "unconscious", "unresponsive", "seizure", "stroke", "face drooping",
    "slurred speech", "severe burn", "suicidal", "suicide", "poisoning",
    "snake bite", "high fever in infant", "blue lips", "not breathing",
    "severe chest pressure", "coughing blood", "vomiting blood",
]

EMERGENCY_ADVICE = (
    "This may be a medical emergency. Please go to the nearest hospital or "
    "call your local emergency number immediately. Do not wait for further advice."
)

OFFLINE_SYMPTOM_RESPONSES = {
    "fever": "Rest, drink plenty of fluids, and take paracetamol if needed for the fever. "
             "See a doctor if fever lasts more than 3 days, exceeds 103°F/39.4°C, or is "
             "accompanied by rash, stiff neck, or difficulty breathing.",
    "cough": "Warm fluids, honey (for adults), and rest usually help a mild cough. "
              "See a doctor if it lasts over 2 weeks, brings up blood, or comes with "
              "breathlessness or chest pain.",
    "headache": "Rest in a quiet, dark room, stay hydrated, and consider a mild pain reliever. "
                "Seek care urgently for a sudden 'worst-ever' headache, headache with fever and "
                "stiff neck, or after a head injury.",
    "diarrhea": "Focus on oral rehydration (ORS), light foods (rice, banana, toast), and hand "
                "hygiene. See a doctor if there's blood in stool, high fever, or signs of "
                "dehydration (very little urine, dizziness).",
    "stomach pain": "Mild stomach pain often eases with rest and light food. Seek care promptly "
                     "for severe or one-sided pain, pain with vomiting/fever, or a hard/swollen "
                     "abdomen.",
    "rash": "Keep the area clean and avoid scratching. See a doctor if the rash spreads quickly, "
            "blisters, or comes with fever or breathing difficulty.",
    "cold": "Rest, fluids, and steam inhalation typically help. Most colds resolve in 7-10 days; "
            "see a doctor if symptoms worsen or a high fever develops.",
    "back pain": "Gentle movement, rest from heavy activity, and a warm compress often help. "
                 "Seek care if there's numbness/weakness in the legs, loss of bladder control, "
                 "or pain after an injury.",
    "default": "Thanks for sharing your symptoms. For anything beyond mild, temporary "
               "discomfort, it's best to visit your nearest Primary Health Centre (PHC) for a "
               "proper check-up. Use the locator tab to find one near you.",
}

HEALTH_EDUCATION_TIPS = {
    "hygiene": "Wash your hands with soap for at least 20 seconds before eating and after using "
               "the toilet — this alone prevents many common infections.",
    "nutrition": "Aim for a plate that's half vegetables/fruit, a quarter whole grains, and a "
                 "quarter protein (dal, eggs, fish, or meat) at most meals.",
    "maternal_health": "Pregnant women should get at least 4 antenatal check-ups, take iron-folic "
                       "acid tablets as advised, and deliver at a health facility with a skilled "
                       "attendant present.",
    "child_health": "Follow the full immunization schedule for your child and monitor growth at "
                    "regular check-ups — most vaccines are free at government health centres.",
    "vector_borne": "Prevent dengue and malaria by removing stagnant water around your home and "
                    "using mosquito nets, especially from dusk to dawn.",
    "mental_health": "Feeling persistently low, anxious, or unable to cope is common and "
                     "treatable — talking to a counsellor or health worker is a sign of "
                     "strength, not weakness.",
    "hypertension_diabetes": "Get your blood pressure and blood sugar checked at least once a "
                              "year after age 30, especially with a family history of these "
                              "conditions.",
    "default": "Small daily habits — enough sleep, regular meals, clean water, and 30 minutes of "
               "movement — go a long way toward long-term health.",
}


def match_offline_symptom(text: str) -> str:
    text_lower = text.lower()
    for key, advice in OFFLINE_SYMPTOM_RESPONSES.items():
        if key != "default" and key in text_lower:
            return advice
    return OFFLINE_SYMPTOM_RESPONSES["default"]


def match_education_tip(topic: str) -> str:
    return HEALTH_EDUCATION_TIPS.get(topic.lower().strip(), HEALTH_EDUCATION_TIPS["default"])


def contains_emergency_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS)
