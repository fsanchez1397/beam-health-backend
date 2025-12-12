import os
import json
import traceback
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import  Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to data directory
DATA_DIR = Path(__file__).parent / "data"

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Beam Health Backend API is running",
        "endpoints": {
            "transcribe": "/transcribe",
            "patients": "/api/patients",
            "insurances": "/api/insurances",
            "appointments": "/api/appointments",
            "active_appointment": "/api/appointments/active"
        }
    }

@app.get("/api/debug/appointments")
async def debug_appointments():
    """Debug endpoint to check appointments data"""
    try:
        appointments = load_json_data("appointments.json")
        booked = [a for a in appointments if a.get("status") == "booked" and a.get("patient_id")]
        now = datetime.now()
        return {
            "total_appointments": len(appointments),
            "booked_appointments": len(booked),
            "current_time": now.isoformat(),
            "sample_booked": booked[:5] if booked else []
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

# Helper function to load JSON data
def load_json_data(filename: str):
    """Load JSON data from data directory"""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=500, detail=f"Data file {filename} not found")
    with open(file_path, 'r') as f:
        return json.load(f)

# Patients endpoints
@app.get("/api/patients")
async def get_patients():
    """Get all patients"""
    return load_json_data("patients.json")

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: int):
    """Get a specific patient by ID"""
    patients = load_json_data("patients.json")
    patient = next((p for p in patients if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found")
    return patient


@app.get("/api/appointments/active")
async def get_active_appointment():
    """Get the currently active appointment based on current time"""
    try:
        appointments = load_json_data("appointments.json")
        # Use UTC for consistent timezone handling across servers (Render uses UTC)
        # Appointments are stored as naive datetimes (assumed to be in local timezone, e.g., EST)
        # Convert server UTC time to EST (UTC-5) for comparison with appointment times
        from datetime import timezone
        utc_now = datetime.now(timezone.utc)
        # Convert UTC to EST (UTC-5) - adjust offset as needed for your timezone
        est_offset = timedelta(hours=-5)
        now = (utc_now + est_offset).replace(tzinfo=None)  # Convert to naive EST time
        
        print(f"[DEBUG] UTC time: {utc_now.isoformat()}, EST time: {now.isoformat()}")
        
        # Find appointments that are currently active
        # Active = current time is between start and end (start + duration)
        active_appointments = []
        booked_count = 0
        for apt in appointments:
            if apt.get("status") == "booked" and apt.get("patient_id"):
                booked_count += 1
                try:
                    # Parse appointment time as naive datetime (assumed to be in EST)
                    start_time = datetime.fromisoformat(apt["start"])
                    duration_minutes = apt.get("slot_duration", 30)
                    end_time = start_time + timedelta(minutes=duration_minutes)
                    
                    # Check if current time is within the appointment window
                    if start_time <= now < end_time:
                        print(f"[DEBUG] Found active appointment: {apt['id']} for patient {apt.get('patient_id')} ({start_time.isoformat()} - {end_time.isoformat()})")
                        active_appointments.append(apt)
                except (ValueError, KeyError) as e:
                    # Skip invalid appointment entries
                    print(f"Warning: Skipping invalid appointment entry: {e}")
                    continue
        
        print(f"[DEBUG] Total booked appointments: {booked_count}, Active: {len(active_appointments)}")
        
        if not active_appointments:
            print("[DEBUG] No active appointments found, returning empty dict")
            # Return empty dict instead of None to ensure consistent JSON response
            return {}
        
        # Return the first active appointment (should only be one, but just in case)
        active_appointments.sort(key=lambda x: x.get("start", ""))
        result = active_appointments[0]
        print(f"[DEBUG] Returning active appointment: {result['id']}")
        return result
    except Exception as e:
        print(f"Error in get_active_appointment: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching active appointment: {str(e)}")


@app.get("/api/patients/{patient_id}/current-appointment")
async def get_current_appointment(patient_id: int):
    """Get the current/upcoming appointment for a patient"""
    appointments = load_json_data("appointments.json")
    now = datetime.now()
    
    # Find upcoming booked appointments for this patient
    upcoming = []
    for apt in appointments:
        if apt.get("patient_id") == patient_id and apt.get("status") == "booked":
            start_time = datetime.fromisoformat(apt["start"])
            if start_time >= now:
                upcoming.append(apt)
    
    if not upcoming:
        return None
    
    # Return the earliest upcoming appointment
    upcoming.sort(key=lambda x: x.get("start", ""))
    return upcoming[0]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TranscriptionRequest(BaseModel):
    patient_id: Optional[int] = None
    appointment_id: Optional[int] = None

class EncounterSummaryRequest(BaseModel):
    transcription: Dict[str, Any]
    patient_id: int
    appointment_id: Optional[int] = None

class EmailRequest(BaseModel):
    to_email: str
    subject: str
    body: str

@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    patient_id: Optional[int] = None,
    appointment_id: Optional[int] = None
):
    """Transcribe audio file and optionally associate with patient/appointment"""
    try:
        print(f"📥 Received audio file: {file.filename}, content_type: {file.content_type}")
        print(f"👤 Patient ID: {patient_id}, Appointment ID: {appointment_id}")
        audio_bytes = await file.read()
        print(f"📊 Audio file size: {len(audio_bytes)} bytes")
        
        # Create a file-like object for OpenAI API
        audio_file = BytesIO(audio_bytes)
        audio_file.name = file.filename or "audio.webm"

        print("🔄 Sending to OpenAI API...")
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-transcribe-diarize",
            file=audio_file,
            response_format="diarized_json",
            chunking_strategy="auto"
        )

        # Add metadata
        result = transcription.model_dump() if hasattr(transcription, 'model_dump') else dict(transcription)
        result["patient_id"] = patient_id
        result["appointment_id"] = appointment_id
        result["timestamp"] = datetime.now().isoformat()

        print("✅ Transcription successful")
        return result
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/api/encounter-summary")
async def generate_encounter_summary(request: EncounterSummaryRequest):
    """Generate encounter summary from transcription using AI"""
    try:
        # Extract text from transcription
        transcription_text = ""
        if isinstance(request.transcription, dict):
            # Handle diarized JSON format
            if "segments" in request.transcription:
                transcription_text = "\n".join([
                    f"{seg.get('speaker', 'Unknown')}: {seg.get('text', '')}"
                    for seg in request.transcription.get("segments", [])
                ])
            elif "text" in request.transcription:
                transcription_text = request.transcription["text"]
        else:
            transcription_text = str(request.transcription)

        # Get patient info
        patients = load_json_data("patients.json")
        patient = next((p for p in patients if p["id"] == request.patient_id), None)
        patient_name = f"{patient['first_name']} {patient['last_name']}" if patient else "Patient"

        # Generate encounter summary using OpenAI
        prompt = f"""Based on the following medical consultation transcription, generate a comprehensive encounter summary.

Patient: {patient_name}
Transcription:
{transcription_text}

Please provide a structured encounter summary with the following sections:
1. Visit Summary - Brief overview of the visit
2. Diagnostic Assessment - Assessment and diagnosis
3. Treatment & Care Plan - Treatment plan and medications
4. Automatic Follow-Up - Recommended follow-up duration (e.g., "2 weeks", "1 month", "3 days", "6 months") and reason
5. Patient Instructions - Clear instructions for the patient
6. Follow-Up Questions - Suggest 3-5 relevant questions the doctor can ask the patient during follow-up visits to assess progress, monitor symptoms, or gather additional information

Format as JSON with these exact keys: visit_summary, diagnostic_assessment, treatment_care_plan, follow_up_duration, follow_up_reason, patient_instructions, follow_up_questions

Note: 
- follow_up_duration should be a duration string like "2 weeks" or "1 month", NOT a specific date.
- follow_up_questions should be an array of strings, each representing a suggested question."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical assistant that creates structured encounter summaries from consultation transcriptions."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )

        summary_text = response.choices[0].message.content
        summary = json.loads(summary_text)

        # Add metadata
        summary["patient_id"] = request.patient_id
        summary["appointment_id"] = request.appointment_id
        summary["generated_at"] = datetime.now().isoformat()

        return summary
    except Exception as e:
        print(f"❌ Error generating encounter summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating encounter summary: {str(e)}")

@app.post("/api/send-email")
async def send_email(request: EmailRequest):
    """Send email to patient (mock implementation - in production use proper email service)"""
    try:
        # In production, use proper email service (SendGrid, AWS SES, etc.)
        # For now, just log the email
        print(f"📧 Email would be sent:")
        print(f"   To: {request.to_email}")
        print(f"   Subject: {request.subject}")
        print(f"   Body: {request.body}")
        
        # Mock success response
        return {
            "success": True,
            "message": "Email sent successfully (mock)",
            "to": request.to_email,
            "sent_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")
