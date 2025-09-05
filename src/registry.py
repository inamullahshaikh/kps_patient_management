from typing import Dict, Type
from pydantic import BaseModel
from schema import (
    Medicine, Medication, Allergy, AllergyDiagnosis, Condition, ConditionDiagnosis,
    Surgery, PastSurgeries, MedicalHistory, Insurance, ContactDetails, Person,
    Doctor, Admin, Patient, PatientInsurance
)
from database import collections

Model = Type[BaseModel]

registry: Dict[str, dict] = {
    "medicine": {"model": Medicine, "collection": collections["medicine"]},
    "medication": {"model": Medication, "collection": collections["medication"]},
    "allergy": {"model": Allergy, "collection": collections["allergy"]},
    "allergy_diagnosis": {"model": AllergyDiagnosis, "collection": collections["allergy_diagnosis"]},
    "condition": {"model": Condition, "collection": collections["condition"]},
    "condition_diagnosis": {"model": ConditionDiagnosis, "collection": collections["condition_diagnosis"]},
    "surgery": {"model": Surgery, "collection": collections["surgery"]},
    "past_surgeries": {"model": PastSurgeries, "collection": collections["past_surgeries"]},
    "medical_history": {"model": MedicalHistory, "collection": collections["medical_history"]},
    "insurance": {"model": Insurance, "collection": collections["insurance"]},
    "contact_details": {"model": ContactDetails, "collection": collections["contact_details"]},
    "person": {"model": Person, "collection": collections["person"]},
    "doctor": {"model": Doctor, "collection": collections["doctor"]},
    "admin": {"model": Admin, "collection": collections["admin"]},
    "patient": {"model": Patient, "collection": collections["patient"]},
    "patient_insurance": {"model": PatientInsurance, "collection": collections["patient_insurance"]},
}
