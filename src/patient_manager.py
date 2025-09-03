from typing import List, Optional
from .patient import Patient
from .insurance import Insurance
from .medical_history import IMedicalHistory
from .person import ContactInfo


class PatientManager:
    def __init__(self):
        self._patients: List[Patient] = []

    # ------------------- CRUD -------------------
    def add_patient(self, patient: Patient):
        if any(p.contact_info.email == patient.contact_info.email for p in self._patients):
            raise ValueError("Patient with this email already exists")
        self._patients.append(patient)

    def get_patient(self, email: str) -> Optional[Patient]:
        return next((p for p in self._patients if p.contact_info.email == email), None)

    def update_patient(self, email: str, **kwargs):
        patient = self.get_patient(email)
        if not patient:
            raise ValueError("Patient not found")

        # Update allowed fields
        if "name" in kwargs:
            patient.name = kwargs["name"]
        if "DOB" in kwargs:
            patient.DOB = kwargs["DOB"]
        if "gender" in kwargs:
            patient.gender = kwargs["gender"]
        if "blood_group" in kwargs:
            patient.blood_group = kwargs["blood_group"]
        if "insurance" in kwargs and isinstance(kwargs["insurance"], Insurance):
            patient.insurance = kwargs["insurance"]
        if "medical_history" in kwargs and isinstance(kwargs["medical_history"], IMedicalHistory):
            patient.medical_history = kwargs["medical_history"]
        if "contact_info" in kwargs and isinstance(kwargs["contact_info"], ContactInfo):
            patient.contact_info = kwargs["contact_info"]

    def delete_patient(self, email: str):
        patient = self.get_patient(email)
        if not patient:
            raise ValueError("Patient not found")
        self._patients.remove(patient)

    # ------------------- SEARCH -------------------
    def search_by_name(self, name: str) -> List[Patient]:
        return [p for p in self._patients if name.lower() in p.name.lower()]

    def search_by_blood_group(self, blood_group: str) -> List[Patient]:
        return [p for p in self._patients if p.blood_group == blood_group]

    def search_by_insurance(self, coverage_level: str) -> List[Patient]:
        return [p for p in self._patients if p.insurance.coverage_level == coverage_level]

    def search_by_condition(self, condition: str) -> List[Patient]:
        return [
            p for p in self._patients 
            if condition in p.medical_history.chronic_conditions
        ]

    # ------------------- DETAILS -------------------
    def list_all_patients(self) -> List[str]:
        return [p.get_details() for p in self._patients]

    def get_full_summary(self, email: str) -> dict:
        patient = self.get_patient(email)
        if not patient:
            raise ValueError("Patient not found")

        return {
            "Details": patient.get_details(),
            "Medical History": patient.medical_history.get_summary(),
            "Insurance": patient.insurance.get_coverage_details()
        }
