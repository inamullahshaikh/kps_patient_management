from typing import Generic, TypeVar, List, Optional, Any
from datetime import datetime, date
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
import uuid

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
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),  # for JSON responses
        }

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        for key, value in data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                data[key] = datetime.combine(value, datetime.min.time())
        return data

class ContactDetails(MongoBaseModel):
    email: EmailStr
    phone_num: str
    address: str

class RoleEnum(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"
    RECEPTIONIST = "receptionist"

class Person(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    gender: str
    DOB: date
    contact_details: ContactDetails
    username: str
    password: str
    specialization: Optional[str]
    working_hours: Optional[str]
    blood_group: Optional[str]
    emergency_contact: Optional[str]
    role: RoleEnum 
class Medicine(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    strength: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacturing_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class Medication(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    medicine_id: Optional[str] = None
    medical_history_id: Optional[str] = None
    dosage: Optional[str] = None
    starting_date: Optional[datetime] = None
    ending_date: Optional[datetime] = None
    prescribing_doctor_id: Optional[str] = None


class Allergy(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    type: Optional[str] = None
    allergen: Optional[str] = None


class AllergyDiagnosis(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    medical_history_id: Optional[str] = None
    allergy_id: Optional[str] = None
    severity: Optional[str] = None
    diagnosing_doctor_id: Optional[str] = None
    diagnosis_date: Optional[datetime] = None


class Condition(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None


class ConditionDiagnosis(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    medical_history_id: Optional[str] = None
    condition_id: Optional[str] = None
    severity: Optional[str] = None
    diagnosing_doctor_id: Optional[str] = None
    diagnosis_date: Optional[datetime] = None
    triggers: Optional[str] = None


class Surgery(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    category: Optional[str] = None
    possible_risks: Optional[List[str]] = None
    body_part: Optional[str] = None
    description: Optional[str] = None


class PastSurgery(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    medical_history_id: Optional[str] = None
    surgery_id: Optional[str] = None
    date: Optional[datetime] = None
    surgeon_id: Optional[str] = None
    complications: Optional[List[str]] = []
    notes: Optional[str] = None
    outcome: Optional[str] = None


class MedicalHistory(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: Optional[str] = None


class Insurance(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    uuid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: Optional[str] = None
    annual_limit: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    type: Optional[str] = None
    hospitalization_coverage: Optional[float] = None
    medicine_coverage: Optional[float] = None
    provider_name: Optional[str] = None



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

PersonCreate = CreateModel[Person]
PersonUpdate = UpdateModel[Person]
PersonGet = GetModel[Person]
PersonDelete = DeleteModel

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