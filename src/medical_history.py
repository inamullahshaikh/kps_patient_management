from abc import ABC, abstractmethod
from medication import Medication
from allergy import Allergy
from condition import Condition
from surgery import Surgery
from typing import List
class IMedicalHistory(ABC):
    @abstractmethod
    def get_summary(self):
        pass

class MedicalHistory(IMedicalHistory):
    def __init__(self):
        self.current_medications: List[Medication] = []
        self.past_surgeries: List[Surgery] = []
        self.chronic_conditions: List[Condition] = []
        self.allergies: List[Allergy] = []

    def add_medication(self, medication):
        self.current_medications.append(medication)

    def remove_medication(self, medication_name: str):
        for med in self.current_medications:
            if med.name == medication_name:
                self.current_medications.remove(med)
                return True
        return False

    def add_allergy(self, allergy):
        if allergy not in self.allergies:
            self.allergies.append(allergy)

    def remove_allergy(self, substance_name: str):
        for allergy in self.allergies:
            if allergy.substance == substance_name:
                self.allergies.remove(allergy)
                return True
        return False

    def add_surgery(self, surgery):
        self.past_surgeries.append(surgery)

    def remove_surgery(self, surgery_name: str):
        for surg in self.past_surgeries:
            if surg.name == surgery_name:
                self.past_surgeries.remove(surg)
                return True
        return False

    def add_condition(self, condition):
        if condition not in self.chronic_conditions:
            self.chronic_conditions.append(condition)

    def remove_condition(self, condition_name: str):
        for cond in self.chronic_conditions:
            if cond.name == condition_name:
                self.chronic_conditions.remove(cond)
                return True
        return False

    def get_summary(self):
        return {
            "Current Medications": [str(m) for m in self.current_medications],
            "Allergies": [str(a) for a in self.allergies],
            "Past Surgeries": [str(s) for s in self.past_surgeries],
            "Chronic Conditions": [str(c) for c in self.chronic_conditions],
        }
