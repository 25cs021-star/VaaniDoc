# VaaniDoc

VaaniDoc is a multilingual AI-powered health intake system that helps patients describe their symptoms in their preferred language and provides doctors with a structured English summary.

## Features

- Multilingual symptom input
- Voice-based symptom input
- AI-powered translation into English
- AI symptom extraction
- Duration extraction
- Symptom categorization
- Urgency estimation
- English clinical summary
- Separate patient and doctor interfaces
- Patient session sharing with the doctor dashboard
- Doctor review and session-ending controls
- Privacy-focused temporary sessions
- Responsive user interface

## Technologies Used

### Frontend
- HTML
- CSS
- JavaScript
- Web Speech API

### Backend
- Python
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv

### AI
- Google Gemini API

## Project Structure

```text
VaaniDoc/
├── frontend/
│   ├── index.html
│   ├── doctor.html
│   ├── style.css
│   ├── script.js
│   └── doctor.js
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── venv/
└── README.md
```

## How It Works

```text
Patient
   ↓
Select Language
   ↓
Type or Speak Symptoms
   ↓
FastAPI Backend
   ↓
Gemini AI
   ↓
Translate + Extract Symptoms
   ↓
Structured Patient Data
   ↓
Doctor Dashboard
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/VaaniDoc.git
cd VaaniDoc
```

### 2. Go to the backend

```bash
cd backend
```

### 3. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## API Key Setup

Create a `.env` file inside the `backend` folder:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Never upload your API key to GitHub.

Add the following to `.gitignore`:

```text
.env
venv/
__pycache__/
```

## Running the Backend

From the `backend` folder:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

Or, if the virtual environment is activated:

```powershell
python -m uvicorn main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

Test it at:

```text
http://127.0.0.1:8000
```

## Running the Frontend

Open the `frontend` folder in VS Code and run `index.html` using Live Server.

Patient page:

```text
http://127.0.0.1:5500/frontend/index.html
```

Doctor dashboard:

```text
http://127.0.0.1:5500/frontend/doctor.html
```

Make sure the backend is running before submitting patient information.

## Patient Workflow

1. Select the patient's language.
2. Enter symptoms by typing or speaking.
3. Press Continue.
4. The backend sends the statement to Gemini.
5. Gemini translates the statement into English.
6. Symptoms and duration are extracted.
7. A structured intake result is created.
8. The patient session becomes available to the doctor dashboard.

## Doctor Workflow

1. Open the Doctor Dashboard.
2. View active patient sessions.
3. Select a session.
4. Review the patient's language, symptoms, duration, urgency, category, and AI summary.
5. Mark the session as reviewed.
6. End the session when finished.

## Privacy

VaaniDoc is designed as a privacy-focused health intake system.

The system uses a randomly generated session ID instead of requiring a patient's name or phone number.

Example:

```text
VD-A81F32C9
```

Patient information is intended for temporary intake processing and doctor review.

## Medical Disclaimer

VaaniDoc is an AI-assisted health intake system and is not a replacement for a qualified medical professional.

The system:
- Does not diagnose diseases.
- Does not prescribe medicines.
- Does not replace a doctor's evaluation.
- Provides AI-generated information for intake assistance.

Doctors should independently evaluate the patient's condition before making medical decisions.

## Future Improvements

- More Indian and international languages
- Improved medical terminology extraction
- Better speech recognition
- Doctor authentication
- Patient authentication
- Secure database integration
- Encrypted storage
- Electronic health record integration
- Emergency symptom detection
- Appointment scheduling
- Medical report upload
- Improved accessibility

## Hackathon Goal

VaaniDoc aims to reduce language barriers between patients and healthcare professionals by allowing patients to communicate naturally in their preferred language while providing doctors with a clear, structured English intake summary.

---

**VaaniDoc — Breaking language barriers in healthcare with AI.**
