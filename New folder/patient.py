from insurance import Insurance
from person import *
from medical_history import *

class Patient(Person):
    def __init__(self, name, DOB, gender, contact_info: ContactInfo,
                 blood_group: str, insurance: Insurance, medical_history: IMedicalHistory):
        super().__init__(name, DOB, gender, contact_info)
        self._blood_group = blood_group
        self._insurance = insurance
        self._medical_history = medical_history

    @property
    def blood_group(self):
        return self._blood_group

    @blood_group.setter
    def blood_group(self, value):
        allowed = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        if value not in allowed:
            raise ValueError(f"Blood group must be one of {allowed}")
        self._blood_group = value

    @property
    def insurance(self):
        return self._insurance

    @insurance.setter
    def insurance(self, value):
        if not isinstance(value, Insurance):
            raise TypeError("Insurance must be an instance of Insurance or its subclass")
        self._insurance = value

    @property
    def medical_history(self):
        return self._medical_history

    @medical_history.setter
    def medical_history(self, history: IMedicalHistory):
        if not isinstance(history, IMedicalHistory):
            raise TypeError("Medical history must implement IMedicalHistory")
        self._medical_history = history
    def get_details(self):
        return {
            "name": self._name,
            "dob": self._DOB,
            "gender": self._gender,
            "email": self.contact_info.email,
            "phone": self.contact_info.phone,
            "address": self.contact_info.address,
            "blood_group": self._blood_group,
            "insurance_type": str(self._insurance.coverage_level),
            "medications": [m.__dict__ for m in self._medical_history.current_medications],
            "allergies": [a.__dict__ for a in self._medical_history.allergies],
            "conditions": [c.__dict__ for c in self._medical_history.chronic_conditions],
            "surgeries": [s.__dict__ for s in self._medical_history.past_surgeries],
        }

