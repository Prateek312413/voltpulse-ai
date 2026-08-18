"""
Predictive Intent & Contextual AAC Engine for NeuroAccess AI.
Synthesizes natural, grammatically complete phrases from low-bandwidth AAC tokens and environmental context.
"""
from typing import List, Dict, Any
import datetime

class AACIntentPredictor:
    """
    Context-aware Language Model engine that expands 1-2 AAC tokens
    into high-urgency or comfort communication sentences.
    """

    # Semantic template mapping with context weighting
    CONTEXTUAL_EXPANSIONS = {
        "WATER": [
            {"phrase": "May I please have a glass of water?", "urgency": "LOW", "category": "COMFORT"},
            {"phrase": "I am feeling very thirsty, could someone bring cold water?", "urgency": "MEDIUM", "category": "COMFORT"},
            {"phrase": "I need water immediately, my throat is dry.", "urgency": "HIGH", "category": "URGENT"}
        ],
        "PAIN": [
            {"phrase": "I am experiencing pain and need assistance.", "urgency": "HIGH", "category": "MEDICAL"},
            {"phrase": "My back and joints are hurting. Can we adjust my position?", "urgency": "MEDIUM", "category": "MEDICAL"},
            {"phrase": "Severe sudden pain! Please call my doctor or nurse right now.", "urgency": "CRITICAL", "category": "EMERGENCY"}
        ],
        "HELP": [
            {"phrase": "Could someone please come and assist me?", "urgency": "HIGH", "category": "ASSISTANCE"},
            {"phrase": "I need help adjusting my chair and pillows.", "urgency": "MEDIUM", "category": "COMFORT"},
            {"phrase": "EMERGENCY: I need immediate medical attention!", "urgency": "CRITICAL", "category": "EMERGENCY"}
        ],
        "DOCTOR": [
            {"phrase": "I would like to speak with the doctor on duty.", "urgency": "MEDIUM", "category": "MEDICAL"},
            {"phrase": "When is my next medical checkup or doctor visit scheduled?", "urgency": "LOW", "category": "INQUIRY"},
            {"phrase": "Please page the emergency physician immediately.", "urgency": "CRITICAL", "category": "EMERGENCY"}
        ],
        "TIRED": [
            {"phrase": "I am feeling tired and would like to rest now.", "urgency": "LOW", "category": "COMFORT"},
            {"phrase": "Could you please dim the room lights so I can sleep?", "urgency": "LOW", "category": "ENVIRONMENT"},
            {"phrase": "I am completely exhausted and cannot keep my eyes open.", "urgency": "MEDIUM", "category": "COMFORT"}
        ],
        "HUNGRY": [
            {"phrase": "I am feeling hungry. Is it time for a meal?", "urgency": "LOW", "category": "NUTRITION"},
            {"phrase": "Could I please have a light warm snack or soup?", "urgency": "MEDIUM", "category": "NUTRITION"}
        ],
        "FAMILY": [
            {"phrase": "I would love to call or see my family today.", "urgency": "LOW", "category": "SOCIAL"},
            {"phrase": "Please send a quick update to my loved ones that I am doing fine.", "urgency": "LOW", "category": "SOCIAL"},
            {"phrase": "Can someone dial my primary emergency contact?", "urgency": "HIGH", "category": "URGENT"}
        ],
        "RESTROOM": [
            {"phrase": "I urgently need assistance getting to the restroom.", "urgency": "HIGH", "category": "ASSISTANCE"},
            {"phrase": "Please assist me with sanitation and hygiene.", "urgency": "MEDIUM", "category": "CARE"}
        ],
        "MEDICINE": [
            {"phrase": "Is it time for my scheduled medication?", "urgency": "MEDIUM", "category": "MEDICAL"},
            {"phrase": "I missed my prescribed pills. Can we check the chart?", "urgency": "HIGH", "category": "MEDICAL"}
        ],
        "THANK YOU": [
            {"phrase": "Thank you so much for your kind help and patience.", "urgency": "LOW", "category": "COURTESY"},
            {"phrase": "I really appreciate your support today.", "urgency": "LOW", "category": "COURTESY"}
        ]
    }

    def predict_intents(
        self, 
        selected_tokens: List[str], 
        context_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates top candidate full phrases ranked by context relevance and token match.
        """
        if not selected_tokens:
            return [{
                "phrase": "I need assistance.",
                "confidence": 0.90,
                "urgency": "MEDIUM",
                "category": "GENERAL",
                "speech_rate": 1.0,
                "speech_pitch": 1.0
            }]

        context_metadata = context_metadata or {}
        time_hour = context_metadata.get("hour", datetime.datetime.now().hour)
        is_night = (time_hour < 6 or time_hour >= 21)

        primary_token = selected_tokens[-1].upper().strip()
        candidates = self.CONTEXTUAL_EXPANSIONS.get(primary_token, [
            {"phrase": f"I am indicating: {primary_token}.", "urgency": "MEDIUM", "category": "CUSTOM"}
        ])

        results = []
        for i, item in enumerate(candidates):
            base_confidence = 0.95 - (i * 0.08)
            
            # Context adjustments
            if is_night and item["category"] in ["COMFORT", "ENVIRONMENT"]:
                base_confidence += 0.04
            if item["urgency"] == "CRITICAL":
                speech_pitch = 1.15
                speech_rate = 1.10
            else:
                speech_pitch = 1.0
                speech_rate = 0.95

            results.append({
                "phrase": item["phrase"],
                "confidence": round(float(np.clip(base_confidence, 0.4, 0.99)), 2) if 'np' in globals() else round(min(0.99, max(0.4, base_confidence)), 2),
                "urgency": item["urgency"],
                "category": item["category"],
                "speech_rate": speech_rate,
                "speech_pitch": speech_pitch
            })

        return sorted(results, key=lambda x: x["confidence"], reverse=True)
