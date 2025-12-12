#!/usr/bin/env python3
"""Generate additional patients and appointments for 2025-12-12 and 2025-12-15"""
import json
from pathlib import Path
from datetime import datetime, timedelta

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PATIENTS_FILE = DATA_DIR / "patients.json"
APPOINTMENTS_FILE = DATA_DIR / "appointments.json"

# Additional patients to generate
ADDITIONAL_PATIENTS = [
    {"first_name": "Sarah", "last_name": "Johnson", "dob": "1988-03-15", "email": "sarah.johnson@example.com", "phone": "5553334444", "gender": "female"},
    {"first_name": "Michael", "last_name": "Chen", "dob": "1992-11-08", "email": "michael.chen@example.com", "phone": "5556667777", "gender": "male"},
    {"first_name": "Emily", "last_name": "Rodriguez", "dob": "1987-06-20", "email": "emily.rodriguez@example.com", "phone": "5558889999", "gender": "female"},
    {"first_name": "David", "last_name": "Kim", "dob": "1995-09-12", "email": "david.kim@example.com", "phone": "5550001111", "gender": "male"},
    {"first_name": "Jessica", "last_name": "Martinez", "dob": "1991-04-25", "email": "jessica.martinez@example.com", "phone": "5552223333", "gender": "female"},
    {"first_name": "Robert", "last_name": "Taylor", "dob": "1986-12-30", "email": "robert.taylor@example.com", "phone": "5554445555", "gender": "male"},
    {"first_name": "Amanda", "last_name": "Anderson", "dob": "1994-07-18", "email": "amanda.anderson@example.com", "phone": "5556668888", "gender": "female"},
    {"first_name": "James", "last_name": "Wilson", "dob": "1989-01-22", "email": "james.wilson@example.com", "phone": "5557778888", "gender": "male"},
    {"first_name": "Lisa", "last_name": "Brown", "dob": "1993-05-14", "email": "lisa.brown@example.com", "phone": "5559990000", "gender": "female"},
    {"first_name": "Christopher", "last_name": "Davis", "dob": "1990-08-07", "email": "chris.davis@example.com", "phone": "5551112222", "gender": "male"},
]

def generate_appointments_for_date(date_str: str, start_hour: int = 9, end_hour: int = 16, slot_duration: int = 30):
    """Generate appointments for a specific date"""
    appointments = []
    appointment_id = 1
    
    # Load existing appointments to get the highest ID
    if APPOINTMENTS_FILE.exists():
        with open(APPOINTMENTS_FILE, 'r') as f:
            existing = json.load(f)
            if existing:
                appointment_id = max(a.get("id", 0) for a in existing) + 1
    
    # Generate time slots
    base_date = datetime.fromisoformat(f"{date_str}T00:00:00")
    current_time = base_date.replace(hour=start_hour, minute=0, second=0)
    end_time = base_date.replace(hour=end_hour, minute=0, second=0)
    
    while current_time < end_time:
        appointments.append({
            "id": appointment_id,
            "status": "available",
            "start": current_time.isoformat(),
            "slot_duration": slot_duration,
            "patient_id": None
        })
        appointment_id += 1
        current_time += timedelta(minutes=slot_duration)
    
    return appointments

def main():
    # Load existing patients
    if PATIENTS_FILE.exists():
        with open(PATIENTS_FILE, 'r') as f:
            patients = json.load(f)
    else:
        patients = []
    
    # Add additional patients
    max_id = max((p.get("id", 0) for p in patients), default=0)
    for i, patient_data in enumerate(ADDITIONAL_PATIENTS, start=1):
        patients.append({
            "id": max_id + i,
            **patient_data
        })
    
    # Save updated patients
    with open(PATIENTS_FILE, 'w') as f:
        json.dump(patients, f, indent=2)
    
    print(f"✅ Generated {len(ADDITIONAL_PATIENTS)} additional patients")
    print(f"📊 Total patients: {len(patients)}")
    
    # Generate appointments for 2025-12-12 and 2025-12-15
    appointments_12_12 = generate_appointments_for_date("2025-12-12")
    appointments_12_15 = generate_appointments_for_date("2025-12-15")
    
    # Load existing appointments
    if APPOINTMENTS_FILE.exists():
        with open(APPOINTMENTS_FILE, 'r') as f:
            existing_appointments = json.load(f)
    else:
        existing_appointments = []
    
    # Combine all appointments
    all_appointments = existing_appointments + appointments_12_12 + appointments_12_15
    
    # Save appointments
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(all_appointments, f, indent=2)
    
    print(f"✅ Generated {len(appointments_12_12)} appointments for 2025-12-12")
    print(f"✅ Generated {len(appointments_12_15)} appointments for 2025-12-15")
    print(f"📊 Total appointments: {len(all_appointments)}")
    
    # Book some appointments (assign patients to some slots)
    patient_ids = [p["id"] for p in patients]
    booked_count = 0
    
    # Book appointments for 2025-12-12 (every other slot)
    for i, apt in enumerate(appointments_12_12):
        if i % 2 == 0 and patient_ids:  # Book every other slot
            apt["status"] = "booked"
            apt["patient_id"] = patient_ids[booked_count % len(patient_ids)]
            booked_count += 1
    
    # Book appointments for 2025-12-15 (every other slot)
    for i, apt in enumerate(appointments_12_15):
        if i % 2 == 0 and patient_ids:  # Book every other slot
            apt["status"] = "booked"
            apt["patient_id"] = patient_ids[booked_count % len(patient_ids)]
            booked_count += 1
    
    # Save updated appointments with bookings
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(all_appointments, f, indent=2)
    
    print(f"✅ Booked {booked_count} appointments")
    print(f"📅 Available appointments: {len(all_appointments) - booked_count}")

if __name__ == "__main__":
    main()

