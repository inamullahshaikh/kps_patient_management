from typing import Generic, TypeVar, List, Optional, Any
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception:
                raise ValueError("Invalid ObjectId")
        raise TypeError("ObjectId required")

class MongoBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

class ContactDetails(MongoBaseModel):
    email: EmailStr
    phone_num: str
    address: str

from datetime import date

class Admin(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    gender: str
    DOB: date   # <- FIXED
    contact_details: ContactDetails
    username: str
    password: str
    type: str = "Admin"

class Doctor(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    gender: str
    DOB: date   # <- FIXED
    contact_details: ContactDetails
    specialization: str
    working_hours: str
    type: str = "Doctor"

class Patient(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    gender: str
    DOB: date   # <- FIXED
    contact_details: ContactDetails
    blood_group: str
    emergency_contact: str
    type: str = "Patient"


class Medicine(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    strength: str
    manufacturer: str
    manufacturing_date: datetime
    expiry_date: datetime
    quantity: int

class Medication(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    medicine_id: PyObjectId
    medical_history_id: PyObjectId
    dosage: str
    starting_date: datetime
    ending_date: datetime
    prescribing_doctor_id: PyObjectId

class Allergy(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    type: str
    allergen: str

class AllergyDiagnosis(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    medical_history_id: PyObjectId
    allergy_id: PyObjectId
    severity: str
    diagnosing_doctor_id: PyObjectId
    diagnosis_date: datetime

class Condition(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    type: str
    description: str

class ConditionDiagnosis(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    medical_history_id: PyObjectId
    condition_id: PyObjectId
    severity: str
    diagnosing_doctor_id: PyObjectId
    diagnosis_date: datetime
    triggers: Optional[str]

class Surgery(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    category: str
    possible_risks: List[str]
    body_part: str
    description: str

class PastSurgery(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    medical_history_id: PyObjectId
    surgery_id: PyObjectId
    date: datetime
    surgeon_id: PyObjectId
    complications: Optional[List[str]] = []
    notes: Optional[str] = None
    outcome: str

class MedicalHistory(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    patient_id: PyObjectId

class Insurance(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    patient_id: PyObjectId
    annual_limit: float
    start_date: datetime
    end_date: datetime
    type: str
    hospitalization_coverage: float
    medicine_coverage: float
    provider_name: str

T = TypeVar("T")

class APIResponse(Generic[T], MongoBaseModel):
    code: int
    message: str
    data: Optional[T]

class CreateModel(Generic[T], MongoBaseModel):
    data: T

class UpdateModel(Generic[T], MongoBaseModel):
    id: PyObjectId
    data: dict

class GetModel(Generic[T], MongoBaseModel):
    data: T

class DeleteModel(MongoBaseModel):
    id: PyObjectId

DoctorCreate = CreateModel[Doctor]
DoctorUpdate = UpdateModel[Doctor]
DoctorGet = GetModel[Doctor]
DoctorDelete = DeleteModel

PatientCreate = CreateModel[Patient]
PatientUpdate = UpdateModel[Patient]
PatientGet = GetModel[Patient]
PatientDelete = DeleteModel

AdminCreate = CreateModel[Admin]
AdminUpdate = UpdateModel[Admin]
AdminGet = GetModel[Admin]
AdminDelete = DeleteModel

MedicineCreate = CreateModel[Medicine]
MedicineUpdate = UpdateModel[Medicine]
MedicineGet = GetModel[Medicine]
MedicineDelete = DeleteModel

MedicationCreate = CreateModel[Medication]
MedicationUpdate = UpdateModel[Medication]
MedicationGet = GetModel[Medication]
MedicationDelete = DeleteModel

AllergyCreate = CreateModel[Allergy]
AllergyUpdate = UpdateModel[Allergy]
AllergyGet = GetModel[Allergy]
AllergyDelete = DeleteModel

AllergyDiagnosisCreate = CreateModel[AllergyDiagnosis]
AllergyDiagnosisUpdate = UpdateModel[AllergyDiagnosis]
AllergyDiagnosisGet = GetModel[AllergyDiagnosis]
AllergyDiagnosisDelete = DeleteModel

ConditionCreate = CreateModel[Condition]
ConditionUpdate = UpdateModel[Condition]
ConditionGet = GetModel[Condition]
ConditionDelete = DeleteModel

ConditionDiagnosisCreate = CreateModel[ConditionDiagnosis]
ConditionDiagnosisUpdate = UpdateModel[ConditionDiagnosis]
ConditionDiagnosisGet = GetModel[ConditionDiagnosis]
ConditionDiagnosisDelete = DeleteModel

SurgeryCreate = CreateModel[Surgery]
SurgeryUpdate = UpdateModel[Surgery]
SurgeryGet = GetModel[Surgery]
SurgeryDelete = DeleteModel

PastSurgeryCreate = CreateModel[PastSurgery]
PastSurgeryUpdate = UpdateModel[PastSurgery]
PastSurgeryGet = GetModel[PastSurgery]
PastSurgeryDelete = DeleteModel

MedicalHistoryCreate = CreateModel[MedicalHistory]
MedicalHistoryUpdate = UpdateModel[MedicalHistory]
MedicalHistoryGet = GetModel[MedicalHistory]
MedicalHistoryDelete = DeleteModel

InsuranceCreate = CreateModel[Insurance]
InsuranceUpdate = UpdateModel[Insurance]
InsuranceGet = GetModel[Insurance]
InsuranceDelete = DeleteModel