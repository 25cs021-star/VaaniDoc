import os
import json
import uuid
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(
    title="VaaniDoc API",
    description="Multilingual AI Health Intake System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


class IntakeRequest(BaseModel):
    language: str
    symptoms_text: str


sessions = {}

SESSION_DURATION_MINUTES = 30


def remove_expired_sessions():
    now = datetime.now(timezone.utc)

    expired_ids = []

    for session_id, session in sessions.items():
        expires_at = datetime.fromisoformat(session["expires_at"])

        if now >= expires_at:
            expired_ids.append(session_id)

    for session_id in expired_ids:
        del sessions[session_id]


@app.get("/")
def home():
    return {
        "message": "VaaniDoc backend is running"
    }


@app.get("/health")
def health():
    remove_expired_sessions()

    return {
        "status": "ok",
        "active_sessions": len(sessions)
    }


@app.post("/api/intake")
async def process_intake(request: IntakeRequest):

    language = request.language.strip()
    original_text = request.symptoms_text.strip()

    if not original_text:
        raise HTTPException(
            status_code=400,
            detail="Please enter or speak your symptoms."
        )

    prompt = f"""
You are the AI clinical intake engine for VaaniDoc.

The patient has described their health problem in:
{language}

Patient's original statement:
{original_text}

Your task is to understand the COMPLETE statement and convert it
into structured English clinical intake information.

IMPORTANT RULES:

1. Translate the COMPLETE patient statement into English.

2. Extract the ACTUAL symptoms mentioned by the patient.

3. NEVER return "Unspecified symptoms" when an actual symptom can
be understood.

4. Do not invent symptoms.

5. Extract ALL identifiable symptoms.

6. Extract the duration if mentioned.

7. If the patient says:
"I have fever and headache for two days"

return:

symptoms = ["Fever", "Headache"]
duration = "2 days"

8. If the patient says:
"मुझे तीन दिन से बुखार और खांसी है"

return:

symptoms = ["Fever", "Cough"]
duration = "3 days"

9. If the patient says:
"મને બે દિવસથી તાવ છે અને માથું દુખે છે"

return:

symptoms = ["Fever", "Headache"]
duration = "2 days"

10. If duration is not mentioned, return:
"Not specified"

11. Categorize symptoms using one of:

General
Respiratory
Digestive
Neurological
Pain
Fever-related
Skin
Other

12. Estimate urgency as:

Low
Medium
High

13. Do NOT diagnose a disease.

14. Do NOT prescribe medicines.

15. The summary must be in English.

16. Return ONLY valid JSON.

Return exactly:

{{
    "translated_text": "complete English translation",
    "symptoms": [
        "actual symptom 1",
        "actual symptom 2"
    ],
    "duration": "duration",
    "category": "category",
    "urgency": "Low",
    "summary": "short English clinical summary"
}}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

        raw_response = response.text.strip()

        data = json.loads(raw_response)

        symptoms = data.get("symptoms", [])

        if isinstance(symptoms, str):
            symptoms = [symptoms]

        symptoms = [
            str(symptom).strip()
            for symptom in symptoms
            if str(symptom).strip()
        ]

        if not symptoms:
            symptoms = ["No identifiable symptom"]

        translated_text = str(
            data.get("translated_text", original_text)
        ).strip()

        duration = str(
            data.get("duration", "Not specified")
        ).strip()

        category = str(
            data.get("category", "General")
        ).strip()

        urgency = str(
            data.get("urgency", "Low")
        ).strip()

        summary = str(
            data.get(
                "summary",
                "The patient's symptoms were processed successfully."
            )
        ).strip()

        now = datetime.now(timezone.utc)

        expires_at = now + timedelta(
            minutes=SESSION_DURATION_MINUTES
        )

        session_id = "VD-" + uuid.uuid4().hex[:8].upper()

        result = {
            "session_id": session_id,
            "language": language,
            "original_text": original_text,
            "translated_text": translated_text,
            "symptoms": symptoms,
            "duration": duration,
            "category": category,
            "urgency": urgency,
            "severity": urgency,
            "summary": summary,
            "status": "New",
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }

        sessions[session_id] = result

        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI returned an invalid response."
        )

    except Exception as e:

        print("GEMINI ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"AI processing failed: {str(e)}"
        )


@app.get("/api/sessions")
def get_sessions():

    remove_expired_sessions()

    session_list = []

    for session in sessions.values():

        session_list.append({
            "session_id": session["session_id"],
            "language": session["language"],
            "category": session["category"],
            "urgency": session["urgency"],
            "severity": session["severity"],
            "status": session["status"],
            "created_at": session["created_at"],
            "expires_at": session["expires_at"]
        })

    session_list.sort(
        key=lambda x: x["created_at"],
        reverse=True
    )

    return session_list


@app.get("/api/session/{session_id}")
def get_session(session_id: str):

    remove_expired_sessions()

    session = sessions.get(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    return session


@app.post("/api/session/{session_id}/review")
def review_session(session_id: str):

    remove_expired_sessions()

    session = sessions.get(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired."
        )

    session["status"] = "Reviewed"

    return {
        "message": "Session marked as reviewed",
        "session_id": session_id,
        "status": "Reviewed"
    }


@app.post("/api/session/{session_id}/end")
def end_session(session_id: str):

    session = sessions.get(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or already deleted."
        )

    del sessions[session_id]

    return {
        "message": "Session ended and data deleted",
        "session_id": session_id
    }