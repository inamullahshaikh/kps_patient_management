from typing import Dict
from schema import (
    Medicine, Medication, Allergy, AllergyDiagnosis, Condition, ConditionDiagnosis,
    Surgery, PastSurgery, MedicalHistory, Insurance, ContactDetails,
    Doctor, Admin, Patient
)
from database import collections

registry: Dict[str, dict] = {
    "medicine": {"model": Medicine, "collection": collections["medicine"]},
    "medication": {"model": Medication, "collection": collections["medication"]},
    "allergy": {"model": Allergy, "collection": collections["allergy"]},
    "allergy_diagnosis": {"model": AllergyDiagnosis, "collection": collections["allergy_diagnosis"]},
    "condition": {"model": Condition, "collection": collections["condition"]},
    "condition_diagnosis": {"model": ConditionDiagnosis, "collection": collections["condition_diagnosis"]},
    "surgery": {"model": Surgery, "collection": collections["surgery"]},
    "past_surgery": {"model": PastSurgery, "collection": collections["past_surgery"]},
    "medical_history": {"model": MedicalHistory, "collection": collections["medical_history"]},
    "insurance": {"model": Insurance, "collection": collections["insurance"]},
    "contact_details": {"model": ContactDetails, "collection": collections["contact_details"]},
    "doctor": {"model": Doctor, "collection": collections["doctor"]},
    "admin": {"model": Admin, "collection": collections["admin"]},
    "patient": {"model": Patient, "collection": collections["patient"]},
}
