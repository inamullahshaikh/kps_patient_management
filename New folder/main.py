from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from datetime import date
from app import App
from medical_history import *
from person import *
from insurance import *
from patient import Patient
app = FastAPI(title="Patient Management API")
core_app = App()

# ---------- Request Models ----------

class PatientCreate(BaseModel):
    name: str
    dob: str
    gender: str
    email: EmailStr
    phone: str
    address: str
    blood_group: str
    insurance_type: str


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    insurance_type: Optional[str] = None


class MedicationCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    price: float


class AllergyCreate(BaseModel):
    substance: str
    severity: str
    reaction: str


class ConditionCreate(BaseModel):
    name: str
    diagnosed_date: date
    status: str


class SurgeryCreate(BaseModel):
    name: str
    surgery_date: date
    hospital: str
    price: float


# ---------- Response Models ----------

class MedicationResponse(BaseModel):
    name: str
    dosage: str
    frequency: str
    price: float


class AllergyResponse(BaseModel):
    substance: str
    severity: str
    reaction: str


class ConditionResponse(BaseModel):
    name: str
    diagnosed_date: date
    status: str


class SurgeryResponse(BaseModel):
    name: str
    surgery_date: date
    hospital: str
    price: float


class PatientResponse(BaseModel):
    code: int
    message: str
    patient: dict

class PatientsListResponse(BaseModel):
    code: int
    message: str
    patients: List = []


class MedicalHistoryUpdate(BaseModel):
    add_medication: Optional[List[MedicationCreate]] = None
    remove_medication: Optional[List[str]] = None
    add_allergy: Optional[List[AllergyCreate]] = None
    remove_allergy: Optional[List[str]] = None
    add_surgery: Optional[List[SurgeryCreate]] = None
    remove_surgery: Optional[List[str]] = None
    add_condition: Optional[List[ConditionCreate]] = None
    remove_condition: Optional[List[str]] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    insurance_type: Optional[str] = None
    medical_history: Optional[MedicalHistoryUpdate] = None



@app.post("/patients/")
def create_patient(patient_data: PatientCreate):
    contact = ContactInfo(
        email=patient_data.email,
        phone=patient_data.phone,
        address=patient_data.address
    )

    if patient_data.insurance_type == "Basic":
        insurance = BasicInsurance("ABC Insurance", "P123")
    elif patient_data.insurance_type == "Good":
        insurance = GoodInsurance("XYZ Insurance", "P456")
    elif patient_data.insurance_type == "Best":
        insurance = BestInsurance("Premium Insurance", "P789")
    else:
        raise HTTPException(status_code=400, detail="Invalid insurance type")

    patient = Patient(
        name=patient_data.name,
        DOB=patient_data.dob,
        gender=patient_data.gender,
        contact_info=contact,
        blood_group=patient_data.blood_group,
        insurance=insurance,
        medical_history=MedicalHistory()
    )

    return core_app.add_patient(patient)

@app.post("/patients/{email}/medications/")
def add_medication(email: str, medication_data: MedicationCreate):
    medication = Medication(**medication_data.dict())
    result = core_app.add_medication(email, medication)
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@app.post("/patients/{email}/allergies/")
def add_allergy(email: str, allergy_data: AllergyCreate):
    allergy = Allergy(**allergy_data.dict())
    result = core_app.add_allergy(email, allergy)
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@app.post("/patients/{email}/conditions/")
def add_condition(email: str, condition_data: ConditionCreate):
    condition = Condition(**condition_data.dict())
    result = core_app.add_chronic_condition(email, condition)
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@app.post("/patients/{email}/surgeries/")
def add_surgery(email: str, surgery_data: SurgeryCreate):
    surgery = Surgery(**surgery_data.dict())
    result = core_app.add_surgery(email, surgery)
    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@app.get("/patients/", response_model=PatientsListResponse)
def get_all_patients():
    return core_app.get_all_patients()

@app.get("/patients/{email}", response_model=PatientResponse)
def get_patient(email: str):
    result = core_app.get_patient(email)
    if result.get("code") == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.put("/patients/{email}")
def update_patient(email: str, patient_data: PatientUpdate):
    update_fields = patient_data.dict(exclude_unset=True)
    if "insurance_type" in update_fields:
        insurance_type = update_fields.pop("insurance_type")
        if insurance_type == "Basic":
            update_fields["insurance"] = BasicInsurance("ABC Insurance", "P123")
        elif insurance_type == "Good":
            update_fields["insurance"] = GoodInsurance("XYZ Insurance", "P456")
        elif insurance_type == "Best":
            update_fields["insurance"] = BestInsurance("Premium Insurance", "P789")
        else:
            raise HTTPException(status_code=400, detail="Invalid insurance type")

    if "medical_history" in update_fields:
        mh = update_fields["medical_history"]
        update_fields["medical_history"] = mh
    result = core_app.update_patient(email, **update_fields)

    if result["code"] == 404:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@app.delete("/patient/{email}")
def remove_patient(email: str):
    return core_app.remove_patient(email)