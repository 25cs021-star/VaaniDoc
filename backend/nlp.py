"""
VaaniDoc NLP Engine
-------------------
Turns raw multilingual patient text into structured clinical intake data:
  - matched symptoms (canonical English names)
  - duration (automatically extracted from natural language)
  - severity
  - symptom category
  - an English clinical intake summary

Two modes (AI-first):
  1. AI-POWERED (primary) - if ANTHROPIC_API_KEY is set in the environment,
     Claude handles symptom detection, duration extraction, severity assessment,
     categorization, and summary generation with natural language understanding
     across English + 9 Indian languages.
  2. RULE-BASED FALLBACK (always available, no API key needed) - simplified
     keyword matching for symptoms with basic extraction. Used when AI is
     unavailable or fails.
"""

import os
import re
import json
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# 1. Symptom knowledge base
# ---------------------------------------------------------------------------
# Each entry: canonical symptom -> category, red_flag, keywords (multi-language)
SYMPTOM_DB = {
    "fever": {
        "category": "General / Fever",
        "red_flag": False,
        "keywords": [
            "fever", "high temperature", "बुखार", "તાવ", "ताप", "জ্বর",
            "காய்ச்சல்", "జ్వరం", "ಜ್ವರ", "പനി", "ਬੁਖਾਰ",
        ],
    },
    "cough": {
        "category": "Respiratory",
        "red_flag": False,
        "keywords": [
            "cough", "खांसी", "ખાંસી", "खोकला", "কাশি", "இருமல்",
            "దగ్గు", "ಕೆಮ್ಮು", "ചുമ", "ਖੰਘ",
        ],
    },
    "cold": {
        "category": "Respiratory",
        "red_flag": False,
        "keywords": [
            "cold", "runny nose", "सर्दी", "શરદી", "সর্দি", "সর্দি", "சளி",
            "జలుబు", "ಶೀತ", "ജലദോഷം", "ਜ਼ੁਕਾਮ",
        ],
    },
    "sore_throat": {
        "category": "Respiratory",
        "red_flag": False,
        "keywords": [
            "sore throat", "throat pain", "गला दर्द", "गले में खराश",
            "ગળામાં દુખાવો", "घसा दुखणे", "গলা ব্যথা", "தொண்டை வலி",
            "గొంతు నొప్పి", "ಗಂಟಲು ನೋವು", "തൊണ്ടവേദന", "ਗਲੇ ਵਿੱਚ ਦਰਦ",
        ],
    },
    "breathlessness": {
        "category": "Respiratory",
        "red_flag": True,
        "keywords": [
            "breathless", "shortness of breath", "difficulty breathing",
            "सांस लेने में तकलीफ", "सांस फूलना", "શ્વાસ લેવામાં તકલીફ",
            "श्वास घेण्यास त्रास", "শ্বাসকষ্ট", "மூச்சுத்திணறல்",
            "ఊపిరి ఆడకపోవడం", "ಉಸಿರಾಟದ ತೊಂದರೆ", "ശ്വാസതടസ്സം",
            "ਸਾਹ ਲੈਣ ਵਿੱਚ ਮੁਸ਼ਕਲ",
        ],
    },
    "chest_pain": {
        "category": "Cardiac",
        "red_flag": True,
        "keywords": [
            "chest pain", "सीने में दर्द", "छाती में दर्द", "છાતીમાં દુખાવો",
            "छातीत दुखणे", "বুকে ব্যথা", "மார்பு வலி", "ఛాతీ నొప్పి",
            "ಎದೆ ನೋವು", "നെഞ്ചുവേദന", "ਛਾਤੀ ਵਿੱਚ ਦਰਦ",
        ],
    },
    "vomiting": {
        "category": "Gastrointestinal",
        "red_flag": False,
        "keywords": [
            "vomiting", "vomit", "उल्टी", "ઉલટી", "उलटी", "বমি", "வாந்தி",
            "వాంతులు", "ವಾಂತಿ", "ഛർദ്ദി", "ਉਲਟੀ",
        ],
    },
    "diarrhea": {
        "category": "Gastrointestinal",
        "red_flag": False,
        "keywords": [
            "diarrhea", "loose motion", "दस्त", "ઝાડા", "जुलाब", "ডায়রিয়া",
            "வயிற்றுப்போக்கு", "విరేచనాలు", "ಭೇದಿ", "വയറിളക്കം", "ਦਸਤ",
        ],
    },
    "stomach_pain": {
        "category": "Gastrointestinal",
        "red_flag": False,
        "keywords": [
            "stomach pain", "abdominal pain", "पेट दर्द", "पेट में दर्द",
            "પેટમાં દુખાવો", "पोटदुखी", "পেট ব্যথা", "வயிற்று வலி",
            "కడుపు నొప్పి", "ಹೊಟ್ಟೆ ನೋವು", "വയറുവേദന", "ਪੇਟ ਦਰਦ",
        ],
    },
    "headache": {
        "category": "Neurological",
        "red_flag": False,
        "keywords": [
            "headache", "सिरदर्द", "सिर दर्द", "માથાનો દુખાવો", "डोकेदुखी",
            "মাথাব্যথা", "தலைவலி", "తలనొప్పి", "ತಲೆನೋವು", "തലവേദന",
            "ਸਿਰ ਦਰਦ",
        ],
    },
    "dizziness": {
        "category": "Neurological",
        "red_flag": False,
        "keywords": [
            "dizziness", "dizzy", "giddiness", "चक्कर", "ચક્કર", "चक्कर",
            "মাথা ঘোরা", "தலைசுற்றல்", "తలతిరగడం", "ತಲೆ ಸುತ್ತು",
            "തലകറക്കം", "ਚੱਕਰ",
        ],
    },
    "weakness": {
        "category": "General / Fever",
        "red_flag": False,
        "keywords": [
            "weakness", "fatigue", "कमजोरी", "નબળાઈ", "अशक्तपणा",
            "দুর্বলতা", "பலவீனம்", "బలహీనత", "ದೌರ್ಬಲ್ಯ", "ബലഹീനത",
            "ਕਮਜ਼ੋਰੀ",
        ],
    },
    "body_pain": {
        "category": "Musculoskeletal",
        "red_flag": False,
        "keywords": [
            "body pain", "body ache", "बदन दर्द", "शरीर दर्द",
            "શરીરમાં દુખાવો", "अंगदुखी", "শরীর ব্যথা", "உடல் வலி",
            "ఒళ్ళు నొప్పులు", "ಮೈ ನೋವು", "ദേഹവേദന", "ਸਰੀਰ ਦਰਦ",
        ],
    },
    "joint_pain": {
        "category": "Musculoskeletal",
        "red_flag": False,
        "keywords": [
            "joint pain", "जोड़ों में दर्द", "સાંધાનો દુખાવો", "सांधेदुखी",
            "গাঁটের ব্যথা", "மூட்டு வலி", "కీళ్ల నొప్పులు", "ಕೀಲು ನೋವು",
            "സന്ധിവേദന", "ਜੋੜਾਂ ਦਾ ਦਰਦ",
        ],
    },
    "rash": {
        "category": "Dermatological",
        "red_flag": False,
        "keywords": [
            "rash", "skin allergy", "खुजली", "चकत्ते", "ફોલ્લીઓ",
            "पुरळ", "ফুসকুড়ি", "தோல் அரிப்பு", "దద్దుర్లు", "ಚರ್ಮದ ಅಲರ್ಜಿ",
            "ചൊറിച്ചിൽ", "ਧੱਫੜ",
        ],
    },
}

# Severity keyword sets (Indian language + English, best-effort)
SEVERE_WORDS = [
    "severe", "very high", "unbearable", "बहुत तेज़", "बहुत ज़्यादा", "गंभीर",
    "ખૂબ", "ગંભીર", "खूप", "গুরুতর", "கடுமையான", "తీవ్రమైన", "ತೀವ್ರ",
    "ഗുരുതരമായ", "ਗੰਭੀਰ", "unconscious", "बेहोश", "fainted", "bleeding heavily",
]
MILD_WORDS = [
    "mild", "slight", "little", "थोड़ा", "हल्का", "હળવું", "थोडं",
    "সামান্য", "லேசான", "తేలికపాటి", "ಸೌಮ್ಯ", "ചെറിയ", "ਹਲਕਾ",
]

# Duration regex: number + unit, across languages
DURATION_UNITS = (
    "day|days|din|दिन|દિવસ|दिवस|দিন|நாள்|நாட்கள்|రోజు|రోజులు|ದಿನ|ദിവസം|ਦਿਨ"
    "|week|weeks|हफ्ता|हफ्ते|सप्ताह|અઠવાડિયું|आठवडा|সপ্তাহ|வாரம்|వారం|ವಾರ|ആഴ്ച|ਹਫ਼ਤਾ"
    "|hour|hours|hr|hrs|घंटा|घंटे|કલાક|तास|ঘণ্টা|மணி நேரம்|గంట|ಗಂಟೆ|മണിക്കൂർ|ਘੰਟਾ"
    "|month|months|महीना|महीने|મહિનો|महिना|মাস|மாதம்|నెల|ತಿಂಗಳು|മാസം|ਮਹੀਨਾ"
)
DURATION_RE = re.compile(r"(\d+)\s*(?:" + DURATION_UNITS + r")", re.IGNORECASE)

CATEGORY_PRIORITY = [
    "Cardiac", "Respiratory", "Gastrointestinal", "Neurological",
    "Musculoskeletal", "Dermatological", "General / Fever",
]


def _rule_based_extract(language: str, text: str) -> dict:
    lower_text = text.lower()

    matched = []
    for name, info in SYMPTOM_DB.items():
        for kw in info["keywords"]:
            if kw.lower() in lower_text:
                matched.append(name)
                break

    # Extract duration using numeric patterns (e.g., "2 days", "3 weeks")
    duration = "Not specified"
    
    # First, try to match numeric duration patterns
    duration_match = DURATION_RE.search(text)
    if duration_match:
        number = duration_match.group(1)
        unit_raw = duration_match.group(0)[len(number):].strip()
        unit_map = {
            "day": "days", "days": "days", "din": "days",
            "दिन": "days", "દિવસ": "days", "दिवस": "days",
            "week": "weeks", "weeks": "weeks", "haftah": "weeks", "haftay": "weeks",
            "हफ्ता": "weeks", "हफ्ते": "weeks", "सप्ताह": "weeks", "અઠવાડિયું": "weeks",
            "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours",
            "घंटा": "hours", "घंटे": "hours", "કલાક": "hours", "तास": "hours",
            "month": "months", "months": "months",
            "महीना": "months", "महीने": "months", "મહિનો": "months", "महिना": "months",
        }
        english_unit = unit_map.get(unit_raw.lower(), unit_map.get(unit_raw, ""))
        if english_unit:
            duration = f"{number} {english_unit}"
        else:
            duration = f"{number} {unit_raw}"
    else:
        # Try word-based number patterns (English only for now)
        # e.g., "two days", "three weeks"
        word_number_map = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
            "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
            "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
            "nineteen": "19", "twenty": "20",
        }
        
        # Check for patterns like "two days", "three weeks", etc.
        for word_num, digit_num in word_number_map.items():
            # Match: [word_number] [days|weeks|hours|months]
            pattern = rf'\b{word_num}\s+(?:day|days|din|दिन|દિવસ|दिवस|' \
                     rf'week|weeks|हफ्ता|हफ्ते|सप्ताह|અઠવાડિયું|' \
                     rf'hour|hours|hr|hrs|घंटा|घंटे|કલાક|तास|' \
                     rf'month|months|महीना|महीने|મહિનો|महिना)\b'
            match = re.search(pattern, lower_text, re.IGNORECASE)
            if match:
                matched_text = match.group(0).split()
                unit = matched_text[-1]  # Get the last word (the unit)
                unit_map = {
                    "day": "days", "days": "days", "din": "days",
                    "दिन": "days", "દિવસ": "days", "दिवस": "days",
                    "week": "weeks", "weeks": "weeks", "haftah": "weeks",
                    "हफ्ता": "weeks", "हफ्ते": "weeks", "सप्ताह": "weeks", "અઠવાડિયું": "weeks",
                    "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours",
                    "घंटा": "hours", "घंटे": "hours", "કલાક": "hours", "तास": "hours",
                    "month": "months", "months": "months",
                    "महीना": "months", "महीने": "months", "મહિનો": "months", "महिना": "months",
                }
                english_unit = unit_map.get(unit.lower(), "")
                if english_unit:
                    duration = f"{digit_num} {english_unit}"
                    break
    
    # If no numeric/word-based duration found, check for special phrases
    if duration == "Not specified":
        if re.search(r'\byesterday\b', lower_text):
            duration = "1 day"
        elif re.search(r'\blast\s+(night|week|month)\b', lower_text):
            # "last night" -> typically same-day, "last week" -> approximately 7 days
            match = re.search(r'\blast\s+(\w+)\b', lower_text)
            if match:
                period = match.group(1)
                if period == "night":
                    duration = "1 day"
                elif period == "week":
                    duration = "1 week"
                elif period == "month":
                    duration = "1 month"

    has_red_flag = any(SYMPTOM_DB[m]["red_flag"] for m in matched)

    if any(w.lower() in lower_text for w in SEVERE_WORDS) or has_red_flag:
        severity = "Severe"
    elif any(w.lower() in lower_text for w in MILD_WORDS):
        severity = "Mild"
    elif matched:
        severity = "Moderate"
    else:
        severity = "Unknown"

    categories = {SYMPTOM_DB[m]["category"] for m in matched}
    if categories:
        category = sorted(categories, key=lambda c: CATEGORY_PRIORITY.index(c)
                           if c in CATEGORY_PRIORITY else 99)[0]
    else:
        category = "General / Unclassified"

    symptom_labels = [m.replace("_", " ").title() for m in matched] or ["Unspecified symptoms"]

    # Build a clinical summary based on extracted data
    symptom_str = ", ".join(symptom_labels).lower()
    duration_str = "" if duration == "Not specified" else f" for approximately {duration}"
    summary = (
        f"The patient reports {symptom_str}{duration_str}. "
        f"Severity assessed as {severity.lower()}. "
        f"This is an automated clinical intake summary based on the patient's reported symptoms and is not a diagnosis."
    )

    return {
        "symptoms": symptom_labels,
        "duration": duration,
        "severity": severity,
        "category": category,
        "summary": summary,
        "engine": "rule-based",
    }


def _ai_extract(language: str, text: str) -> dict | None:
    """Optional Claude-powered extraction. Returns None on any failure so the
    caller can fall back to the rule-based engine."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        system_prompt = (
            "You are a clinical intake assistant for an Indian multilingual "
            "telehealth triage tool. You are given patient-reported symptoms in "
            "an Indian language (or English). Extract and respond with ONLY a JSON object "
            "(no markdown fences, no extra text) with these exact keys: "
            '"symptoms" (array of short English symptom names), '
            '"duration" (short string, e.g. "2 days", or "Not specified"), '
            '"severity" (one of "Mild", "Moderate", "Severe", "Unknown"), '
            '"category" (one of "Respiratory", "Gastrointestinal", "Neurological", '
            '"Cardiac", "Musculoskeletal", "Dermatological", "General / Fever", '
            '"General / Unclassified"), '
            '"summary" (a concise 2-3 sentence English clinical intake summary '
            "based ONLY on the patient's original description. Include the symptoms, "
            "duration, and severity if mentioned. Accurately preserve the symptoms, "
            "duration, severity words, body location, frequency, triggers, and associated "
            "symptoms when explicitly mentioned. Do NOT invent, assume, or add any symptom, "
            "diagnosis, cause, medication, medical history, or other information that the "
            "patient did not provide. If a detail is not mentioned, do not guess it. "
            "Keep the patient's important details in the summary and use a neutral clinical "
            "tone. Clearly state that this is not a diagnosis)."
        )
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Language: {language}\nPatient text: {text}",
                }
            ],
        )
        raw = "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        )
        raw = raw.strip().strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
        data = json.loads(raw)

        # Guard against Claude returning valid-but-incomplete JSON (e.g. for
        # non-symptom input like "hello"). If any required field is missing
        # or of the wrong type, treat this as a failure and let the caller
        # fall back to the rule-based engine instead of crashing downstream.
        required_str_fields = ["duration", "severity", "category", "summary"]
        if not isinstance(data, dict):
            return None
        if not isinstance(data.get("symptoms"), list) or not data["symptoms"]:
            return None
        for field in required_str_fields:
            if not isinstance(data.get(field), str) or not data[field].strip():
                return None
        if data["severity"] not in ("Mild", "Moderate", "Severe", "Unknown"):
            return None

        data["engine"] = "claude-ai"
        return data
    except Exception as e:
        print("Claude AI error:", repr(e))
        return None


def process_intake(language: str, text: str) -> dict:
    """Main entry point used by the API layer."""
    result = _ai_extract(language, text)
    if result is None:
        result = _rule_based_extract(language, text)

    result["processed_at"] = datetime.now(timezone.utc).isoformat()
    return result
