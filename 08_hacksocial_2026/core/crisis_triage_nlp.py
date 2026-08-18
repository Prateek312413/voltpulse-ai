"""
ResilioNet AI - Crisis Triage NLP & Intent Classification Engine
Multilingual distress parser, named-entity extraction, and dynamic urgency calculator.
"""

import re
import math
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DistressCategory(str, Enum):
    CRITICAL_MEDICAL = "CRITICAL_MEDICAL"
    TRAPPED_SEARCH_RESCUE = "TRAPPED_SEARCH_RESCUE"
    VULNERABLE_POPULATION = "VULNERABLE_POPULATION"
    WATER_FOOD_DEFICIT = "WATER_FOOD_DEFICIT"
    SHELTER_EXPOSURE = "SHELTER_EXPOSURE"
    POWER_INFRASTRUCTURE = "POWER_INFRASTRUCTURE"
    GENERAL_ASSISTANCE = "GENERAL_ASSISTANCE"


class ExtractedEntities(BaseModel):
    headcount: int = 1
    vulnerable_infants: int = 0
    vulnerable_elderly: int = 0
    medical_conditions: List[str] = Field(default_factory=list)
    specific_supplies_needed: List[str] = Field(default_factory=list)
    location_mentions: List[str] = Field(default_factory=list)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_info: Optional[str] = None
    hazard_type: Optional[str] = None


class TriageResult(BaseModel):
    triage_id: str
    raw_text: str
    primary_category: DistressCategory
    secondary_categories: List[DistressCategory] = Field(default_factory=list)
    urgency_score: float = Field(..., ge=1.0, le=10.0, description="Urgency score from 1.0 (low) to 10.0 (maximum critical)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    sentiment_stress_score: float = Field(..., ge=0.0, le=1.0)
    entities: ExtractedEntities
    suggested_responder_skills: List[str] = Field(default_factory=list)
    recommended_kit_type: str
    actionable_summary: str


class CrisisNLPEngine:
    """
    High-performance multilingual crisis signal parser and urgency scoring engine.
    Designed for zero-latency edge parsing in humanitarian crisis ops centers.
    """

    # Keyword lexicons with weighted semantic scores
    CATEGORY_LEXICONS = {
        DistressCategory.CRITICAL_MEDICAL: {
            "keywords": [
                "bleeding", "blood", "hemorrhage", "heart attack", "cardiac", "stroke", "unconscious",
                "seizure", "insulin", "diabetic", "dialysis", "oxygen", "asthma", "inhaler", "fracture",
                "broken bone", "burns", "pregnant", "labor", "contractions", "wound", "infection", "medication",
                "sangrado", "ataque cardiaco", "inconsciente", "oxigeno", "sang", "blessure", "médicament",
                "खून", "दिल का दौरा", "बेहोश", "दवा", "ऑक्सीजन", "chấn thương", "mất máu"
            ],
            "base_urgency": 8.5,
            "responder": ["Paramedic", "Trauma EMT", "Mobile ICU", "Doctor"]
        },
        DistressCategory.TRAPPED_SEARCH_RESCUE: {
            "keywords": [
                "trapped", "stuck", "collapse", "debris", "rubble", "rising water", "roof", "rooftop",
                "attic", "landslide", "mudslide", "crushed", "cannot escape", "drowning", "flood level",
                "surrounded by water", "smoke inhalation", "fire spreading", "atrapado", "escombros", "techo",
                "inondation", "coincé", "décombres", "फंसे हुए", "मलबे", "बाढ़", "bị kẹt", "sập nhà"
            ],
            "base_urgency": 9.2,
            "responder": ["Search and Rescue (SAR)", "Swiftwater Rescue", "Heavy Urban Rigging", "Drone Recon"]
        },
        DistressCategory.VULNERABLE_POPULATION: {
            "keywords": [
                "baby", "infant", "newborn", "toddler", "formula", "diapers", "elderly", "grandma",
                "grandpa", "wheelchair", "bedridden", "disabled", "autistic", "child", "children", "nursing",
                "bebé", "anciano", "abuela", "silla de ruedas", "discapacitado", "nourrisson", "personne âgée",
                "बच्चा", "शिशु", "बुजुर्ग", "व्हीलचेयर", "trẻ sơ sinh", "người già"
            ],
            "base_urgency": 7.5,
            "responder": ["Pediatric Care", "Geriatric Assistance", "Accessible Transport", "Social Worker"]
        },
        DistressCategory.WATER_FOOD_DEFICIT: {
            "keywords": [
                "water", "drinking water", "dehydration", "thirsty", "food", "starving", "hunger",
                "no food", "rations", "potable", "clean water", "bottled water", "formula shortage",
                "agua potable", "sed", "hambre", "comida", "eau potable", "faim", "nourriture",
                "पानी", "पीने का पानी", "भूख", "खाना", "nước uống", "thức ăn"
            ],
            "base_urgency": 6.0,
            "responder": ["Food Logistics", "Mobile Water Purification", "Mutual Aid Courier", "Supply Depot"]
        },
        DistressCategory.SHELTER_EXPOSURE: {
            "keywords": [
                "freezing", "hypothermia", "cold", "blankets", "sleeping bag", "tarps", "roof torn off",
                "heat stroke", "extreme heat", "no shelter", "homeless", "evacuated", "shivering",
                "frio", "hipotermia", "mantas", "sin refugio", "froid", "couvertures", "sans abri",
                "ठंड", "कंबल", "आश्रय", "be rét", "chỗ ở tạm"
            ],
            "base_urgency": 6.8,
            "responder": ["Emergency Shelter Ops", "Thermal Aid Supply", "Evacuation Transport"]
        },
        DistressCategory.POWER_INFRASTRUCTURE: {
            "keywords": [
                "power out", "blackout", "generator", "diesel fuel", "electricity", "battery dead",
                "downed power line", "grid down", "solar inverter", "no signal", "radio outage",
                "corte de luz", "generador", "combustible", "panne de courant", "générateur",
                "बिजली बंद", "जनरेटर", "ईंधन", "mất điện", "máy phát điện"
            ],
            "base_urgency": 5.5,
            "responder": ["Electrical Engineer", "Generator Tech", "Off-Grid Comms Specialist"]
        }
    }

    MEDICAL_CONDITIONS = [
        "diabetes", "diabetic", "asthma", "heart disease", "hypertension", "dialysis", "pregnancy",
        "post-surgery", "epilepsy", "allergies", "anaphylaxis", "fracture", "burn", "infection",
        "hypothermia", "dehydration", "smoke inhalation", "oxygen dependency"
    ]

    SUPPLY_KEYWORDS = {
        "potable_water": ["water", "drinking water", "hydration", "agua", "eau", "पानी"],
        "mre_food_rations": ["food", "rations", "canned food", "meals", "comida", "nourriture", "खाना"],
        "infant_formula_diapers": ["baby formula", "infant formula", "milk powder", "diapers", "bebé formula"],
        "insulin_cold_pack": ["insulin", "diabetic medicine", "insulina"],
        "oxygen_concentrator": ["oxygen tank", "oxygen", "inhaler", "breathing machine", "concentrator"],
        "trauma_first_aid_kit": ["bandages", "gauze", "tourniquet", "first aid", "antiseptic", "bleeding kit"],
        "thermal_blankets_tarp": ["blanket", "thermal blanket", "tarps", "tent", "sleeping bag", "manta"],
        "portable_generator_fuel": ["generator", "diesel", "fuel", "gasoline", "battery pack"]
    }

    def __init__(self):
        # Precompile regexes for fast matching
        self._coord_regex = re.compile(r'([-+]?\d{1,2}\.\d+)[,\s]+([-+]?\d{1,3}\.\d+)')
        self._phone_regex = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self._headcount_regexes = [
            re.compile(r'(\d+)\s*(?:people|persons|adults|individuals|family members|trapped|victims)', re.IGNORECASE),
            re.compile(r'family of\s*(\d+)', re.IGNORECASE),
            re.compile(r'group of\s*(\d+)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:kids|children|babies|toddlers)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:elderly|seniors|grandparents)', re.IGNORECASE)
        ]

    def analyze_message(self, text: str, triage_id: Optional[str] = None, timestamp_hours_ago: float = 0.0) -> TriageResult:
        """
        Parses raw distress text, computes multi-intent classification, extracts entities,
        and determines actionable urgency score with temporal escalation.
        """
        if not text or not text.strip():
            return self._create_fallback_triage(triage_id or "T-NULL")

        tid = triage_id or f"T-{abs(hash(text)) % 1000000:06d}"
        clean_text = text.lower()

        # 1. Score Categories
        category_scores: Dict[DistressCategory, float] = {}
        for category, config in self.CATEGORY_LEXICONS.items():
            matches = 0
            for kw in config["keywords"]:
                if kw in clean_text:
                    matches += 1
            if matches > 0:
                # Diminishing returns on multiple keyword hits
                category_scores[category] = config["base_urgency"] + math.log1p(matches) * 0.6

        # Assign primary and secondary categories
        if not category_scores:
            primary_cat = DistressCategory.GENERAL_ASSISTANCE
            secondary_cats = []
            base_score = 4.0
        else:
            sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            primary_cat = sorted_cats[0][0]
            secondary_cats = [c[0] for c in sorted_cats[1:3]]
            base_score = sorted_cats[0][1]

        # 2. Extract Entities
        entities = self._extract_entities(text, clean_text)

        # 3. Calculate Urgency Multipliers
        urgency = base_score

        # Vulnerable headcounts modifier
        if entities.vulnerable_infants > 0:
            urgency += min(1.8, entities.vulnerable_infants * 0.9)
        if entities.vulnerable_elderly > 0:
            urgency += min(1.4, entities.vulnerable_elderly * 0.7)
        if entities.headcount > 5:
            urgency += min(1.0, (entities.headcount - 5) * 0.15)

        # Medical conditions booster
        if entities.medical_conditions:
            urgency += min(1.5, len(entities.medical_conditions) * 0.5)

        # Trap / life threat boost
        if any(w in clean_text for w in ["rising water", "submerged", "no air", "crushed", "dying", "urgent sos", "bleed out", "cannot breathe"]):
            urgency = max(urgency, 9.5)

        # Temporal delay escalation (older unaddressed SOS gets higher priority)
        if timestamp_hours_ago > 0:
            time_escalation = min(1.5, timestamp_hours_ago * 0.25)
            urgency += time_escalation

        # Stress / Sentiment Score (heuristic density of distress exclamations & upper case)
        stress_score = self._compute_stress_score(text)
        urgency += stress_score * 0.6

        # Cap between 1.0 and 10.0
        final_urgency = round(max(1.0, min(10.0, urgency)), 2)

        # 4. Determine Recommended Kit & Responders
        responders = self.CATEGORY_LEXICONS.get(primary_cat, {}).get("responder", ["Community Volunteer", "Mutual Aid Lead"])
        if entities.vulnerable_infants > 0 and "Pediatric Care" not in responders:
            responders.append("Pediatric Supplies Unit")
        if "oxygen" in clean_text and "Mobile ICU" not in responders:
            responders.append("Oxygen Logistics Squad")

        recommended_kit = self._determine_kit_type(primary_cat, entities)

        confidence = 0.85 if len(category_scores) > 0 else 0.50
        if len(entities.specific_supplies_needed) > 0 or len(entities.medical_conditions) > 0:
            confidence = min(0.98, confidence + 0.10)

        summary = self._generate_summary(primary_cat, final_urgency, entities)

        return TriageResult(
            triage_id=tid,
            raw_text=text,
            primary_category=primary_cat,
            secondary_categories=secondary_cats,
            urgency_score=final_urgency,
            confidence=round(confidence, 2),
            sentiment_stress_score=round(stress_score, 2),
            entities=entities,
            suggested_responder_skills=responders,
            recommended_kit_type=recommended_kit,
            actionable_summary=summary
        )

    def _extract_entities(self, original_text: str, clean_text: str) -> ExtractedEntities:
        entities = ExtractedEntities()

        # Headcount parsing
        total_headcount = 1
        for rx in self._headcount_regexes:
            match = rx.search(clean_text)
            if match:
                try:
                    num = int(match.group(1))
                    if 1 <= num <= 200:
                        total_headcount = max(total_headcount, num)
                except ValueError:
                    pass
        entities.headcount = total_headcount

        # Vulnerable subgroups
        if any(w in clean_text for w in ["baby", "infant", "newborn", "toddler", "bebé", "nourrisson", "बच्चा"]):
            entities.vulnerable_infants = 1
            infant_rx = re.search(r'(\d+)\s*(?:babies|infants|toddlers|kids|children)', clean_text)
            if infant_rx:
                try:
                    entities.vulnerable_infants = int(infant_rx.group(1))
                except ValueError:
                    pass

        if any(w in clean_text for w in ["elderly", "grandma", "grandpa", "senior", "bedridden", "anciano", "बुजुर्ग"]):
            entities.vulnerable_elderly = 1
            elderly_rx = re.search(r'(\d+)\s*(?:elderly|seniors|grandparents)', clean_text)
            if elderly_rx:
                try:
                    entities.vulnerable_elderly = int(elderly_rx.group(1))
                except ValueError:
                    pass

        # Medical conditions
        for cond in self.MEDICAL_CONDITIONS:
            if cond in clean_text:
                entities.medical_conditions.append(cond.capitalize())

        # Specific supplies
        for supply_code, syns in self.SUPPLY_KEYWORDS.items():
            if any(syn in clean_text for syn in syns):
                entities.specific_supplies_needed.append(supply_code)

        # GPS Coordinates extraction
        coord_match = self._coord_regex.search(original_text)
        if coord_match:
            try:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    entities.latitude = lat
                    entities.longitude = lon
            except ValueError:
                pass

        # Phone extraction
        phone_match = self._phone_regex.search(original_text)
        if phone_match:
            entities.contact_info = phone_match.group(0).strip()

        # Location text extraction heuristic (e.g. "at 4th & Main", "near Sector 9", "behind City Hospital")
        loc_patterns = [
            re.compile(r'(?:at|near|behind|in front of|on|beside)\s+([0-9a-zA-Z\s,.-]{4,40})(?:\.|$|,|\band\b)', re.IGNORECASE),
            re.compile(r'location:\s*([^\n\r,]+)', re.IGNORECASE),
            re.compile(r'address:\s*([^\n\r,]+)', re.IGNORECASE)
        ]
        for pat in loc_patterns:
            loc_m = pat.search(original_text)
            if loc_m:
                loc_str = loc_m.group(1).strip()
                if len(loc_str) >= 3 and loc_str not in entities.location_mentions:
                    entities.location_mentions.append(loc_str)

        # Hazard detection
        for hazard in ["flood", "flooding", "earthquake", "wildfire", "fire", "hurricane", "tornado", "landslide", "blizzard", "explosion"]:
            if hazard in clean_text:
                entities.hazard_type = hazard.upper()
                break

        return entities

    def _compute_stress_score(self, text: str) -> float:
        """Calculates linguistic distress density."""
        if not text:
            return 0.0
        exclamation_count = text.count('!') + text.count('?')
        caps_count = sum(1 for c in text if c.isupper())
        total_letters = sum(1 for c in text if c.isalpha())

        caps_ratio = caps_count / max(1, total_letters) if total_letters > 0 else 0.0
        urgent_triggers = sum(1 for trigger in ["please help", "urgent", "emergency", "hurry", "asap", "save us", "sos", "dying", "danger"] if trigger in text.lower())

        score = min(1.0, (exclamation_count * 0.12) + (caps_ratio * 0.40) + (urgent_triggers * 0.25))
        return score

    def _determine_kit_type(self, primary_cat: DistressCategory, entities: ExtractedEntities) -> str:
        if primary_cat == DistressCategory.CRITICAL_MEDICAL:
            if any("insulin" in s.lower() for s in entities.specific_supplies_needed) or any("diabet" in m.lower() or "insulin" in m.lower() for m in entities.medical_conditions):
                return "KIT-MED-INSULIN-TRAUMA"
            if any("oxygen" in m.lower() for m in entities.medical_conditions) or any("oxygen" in s.lower() for s in entities.specific_supplies_needed):
                return "KIT-MED-O2-CONCENTRATOR"
            return "KIT-MED-TRAUMA-ADVANCED"
        elif primary_cat == DistressCategory.TRAPPED_SEARCH_RESCUE:
            return "KIT-SAR-RIGGING-RAFT"
        elif primary_cat == DistressCategory.VULNERABLE_POPULATION:
            if entities.vulnerable_infants > 0:
                return "KIT-PEDIATRIC-NUTRITION"
            return "KIT-GERIATRIC-MOBILITY"
        elif primary_cat == DistressCategory.WATER_FOOD_DEFICIT:
            return "KIT-WATER-MRE-COMMUNITY-PACK"
        elif primary_cat == DistressCategory.SHELTER_EXPOSURE:
            return "KIT-THERMAL-SHELTER-TARP"
        elif primary_cat == DistressCategory.POWER_INFRASTRUCTURE:
            return "KIT-GEN-SOLAR-OFFGRID"
        return "KIT-STANDARD-MUTUAL-AID"

    def _generate_summary(self, cat: DistressCategory, score: float, entities: ExtractedEntities) -> str:
        people_str = f"{entities.headcount} individual(s)"
        if entities.vulnerable_infants > 0 or entities.vulnerable_elderly > 0:
            people_str += f" (inc. {entities.vulnerable_infants} infant(s), {entities.vulnerable_elderly} senior(s))"

        medical_str = f" [Conditions: {', '.join(entities.medical_conditions)}]" if entities.medical_conditions else ""
        supplies_str = f" [Needs: {', '.join(entities.specific_supplies_needed)}]" if entities.specific_supplies_needed else ""

        return f"[{cat.value} | Priority {score}/10] {people_str}{medical_str}{supplies_str}"

    def _create_fallback_triage(self, tid: str) -> TriageResult:
        return TriageResult(
            triage_id=tid,
            raw_text="No text provided",
            primary_category=DistressCategory.GENERAL_ASSISTANCE,
            secondary_categories=[],
            urgency_score=2.0,
            confidence=0.1,
            sentiment_stress_score=0.0,
            entities=ExtractedEntities(),
            suggested_responder_skills=["General Volunteer"],
            recommended_kit_type="KIT-STANDARD-MUTUAL-AID",
            actionable_summary="[GENERAL_ASSISTANCE | Priority 2.0/10] Unspecified assistance request"
        )
