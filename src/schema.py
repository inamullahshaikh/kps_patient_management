from pydantic import BaseModel
from pydantic.generics import GenericModel
from datetime import date
from typing import Generic, TypeVar, List, Optional

class Medicine(BaseModel):
    ID: int
    name: str
    strength: str
    manufacturer: str
    manufacturing_date: str
    expiry_date: str
    quantity: int

class Medication(BaseModel):
    medicine_id: int
    medical_history_id: int
    dosage: int
    starting_date: date
    ending_date: date
    prescribing_doctor_id: int

class Allergy(BaseModel):
    ID: int
    name: str
    type: str
    allergen: str

class AllergyDiagnosis(BaseModel):
    medical_history_id: int
    allergy_id: int
    severity: str
    diagnosing_doctor_id: int
    diagnosis_date: date

class Condition(BaseModel):
    ID: int
    name: str
    type: str
    description: str

class ConditionDiagnosis(BaseModel):
    medical_history_id: int
    severity: str
    diagnosing_doctor_id: int
    diagnosis_date: date
    condition_id: int
    triggers: str

class Surgery(BaseModel):
    ID: int
    name: str
    category: str
    possible_risks: List[str]
    body_part: str
    description: str

class PastSurgeries(BaseModel):
    medical_history_id: int
    surgery_id: int
    date: date
    complications: List[str]
    notes: str
    outcome: str

class MedicalHistory(BaseModel):
    patient_id: int
    ID: int
    medications: List[Medication]
    allergies: List[AllergyDiagnosis]
    conditions: List[ConditionDiagnosis]
    past_surgeries: List[PastSurgeries]

class Insurance(BaseModel):
    ID: int
    annual_limit: float
    start_date: date
    end_date: date
    type: str
    hospitalization_coverage: float
    medicine_coverage: float
    provider_name: str

class ContactDetails(BaseModel):
    email: str
    phone_number: str
    address: str
    person_id: int

class Person(BaseModel):
    ID: int
    name: str 
    gender: str
    DOB: date
    contact_details: ContactDetails

class Doctor(Person):
    specialization: str
    working_hours: str

class Admin(Person):
    username: str
    password: str

class Patient(Person):
    blood_group: str
    emergency_contact: str
    Insurance: Optional[Insurance]
    medical_history: MedicalHistory

class PatientInsurance(BaseModel):
    patient_id: int
    insurance_id: int
    
T = TypeVar("T")

class APIResponse(GenericModel, Generic[T]):
    code: int
    message: str
    data: T

class CreateModel(GenericModel, Generic[T]):
    data: T

class UpdateModel(GenericModel, Generic[T]):
    id: int
    data: T

class GetModel(GenericModel, Generic[T]):
    data: T

class DeleteModel(GenericModel, Generic[T]):
    id: int

DoctorCreate = CreateModel[Doctor]
DoctorUpdate = UpdateModel[Doctor]
DoctorGet = GetModel[Doctor]
DoctorDelete = DeleteModel[Doctor]

PatientCreate = CreateModel[Patient]
PatientUpdate = UpdateModel[Patient]
PatientGet = GetModel[Patient]
PatientDelete = DeleteModel[Patient]

AdminCreate = CreateModel[Admin]
AdminUpdate = UpdateModel[Admin]
AdminGet = GetModel[Admin]
AdminDelete = DeleteModel[Admin]

MedicineCreate = CreateModel[Medicine]
MedicineUpdate = UpdateModel[Medicine]
MedicineGet = GetModel[Medicine]
MedicineDelete = DeleteModel[Medicine]

MedicationCreate = CreateModel[Medication]
MedicationUpdate = UpdateModel[Medication]
MedicationGet = GetModel[Medication]
MedicationDelete = DeleteModel[Medication]

AllergyCreate = CreateModel[Allergy]
AllergyUpdate = UpdateModel[Allergy]
AllergyGet = GetModel[Allergy]
AllergyDelete = DeleteModel[Allergy]

AllergyDiagnosisCreate = CreateModel[AllergyDiagnosis]
AllergyDiagnosisUpdate = UpdateModel[AllergyDiagnosis]
AllergyDiagnosisGet = GetModel[AllergyDiagnosis]
AllergyDiagnosisDelete = DeleteModel[AllergyDiagnosis]

ConditionCreate = CreateModel[Condition]
ConditionUpdate = UpdateModel[Condition]
ConditionGet = GetModel[Condition]
ConditionDelete = DeleteModel[Condition]

ConditionDiagnosisCreate = CreateModel[ConditionDiagnosis]
ConditionDiagnosisUpdate = UpdateModel[ConditionDiagnosis]
ConditionDiagnosisGet = GetModel[ConditionDiagnosis]
ConditionDiagnosisDelete = DeleteModel[ConditionDiagnosis]

SurgeryCreate = CreateModel[Surgery]
SurgeryUpdate = UpdateModel[Surgery]
SurgeryGet = GetModel[Surgery]
SurgeryDelete = DeleteModel[Surgery]

PastSurgeriesCreate = CreateModel[PastSurgeries]
PastSurgeriesUpdate = UpdateModel[PastSurgeries]
PastSurgeriesGet = GetModel[PastSurgeries]
PastSurgeriesDelete = DeleteModel[PastSurgeries]

MedicalHistoryCreate = CreateModel[MedicalHistory]
MedicalHistoryUpdate = UpdateModel[MedicalHistory]
MedicalHistoryGet = GetModel[MedicalHistory]
MedicalHistoryDelete = DeleteModel[MedicalHistory]

InsuranceCreate = CreateModel[Insurance]
InsuranceUpdate = UpdateModel[Insurance]
InsuranceGet = GetModel[Insurance]
InsuranceDelete = DeleteModel[Insurance]

ContactDetailsCreate = CreateModel[ContactDetails]
ContactDetailsUpdate = UpdateModel[ContactDetails]
ContactDetailsGet = GetModel[ContactDetails]
ContactDetailsDelete = DeleteModel[ContactDetails]

PatientInsuranceCreate = CreateModel[PatientInsurance]
PatientInsuranceUpdate = UpdateModel[PatientInsurance]
PatientInsuranceGet = GetModel[PatientInsurance]
PatientInsuranceDelete = DeleteModel[PatientInsurance]