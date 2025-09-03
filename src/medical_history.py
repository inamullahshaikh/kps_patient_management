from abc import ABC, abstractmethod
class IMedicalHistory(ABC):
    @abstractmethod
    def get_summary(self):
        pass


class MedicalHistory(IMedicalHistory):
    def __init__(self):
        self.current_medications = []
        self.allergies = []
        self.past_surgeries = []
        self.chronic_conditions = []

    def add_medication(self, medication):
        if medication not in self.current_medications:
            self.current_medications.append(medication)

    def remove_medication(self, medication):
        if medication in self.current_medications:
            self.current_medications.remove(medication)

    def add_allergy(self, allergy):
        if allergy not in self.allergies:
            self.allergies.append(allergy)

    def remove_allergy(self, allergy):
        if allergy in self.allergies:
            self.allergies.remove(allergy)

    def add_surgery(self, surgery):
        if surgery not in self.past_surgeries:
            self.past_surgeries.append(surgery)

    def remove_surgery(self, surgery):
        if surgery in self.past_surgeries:
            self.past_surgeries.remove(surgery)

    def add_condition(self, condition):
        if condition not in self.chronic_conditions:
            self.chronic_conditions.append(condition)

    def remove_condition(self, condition):
        if condition in self.chronic_conditions:
            self.chronic_conditions.remove(condition)

    def get_summary(self):
        return {
            "Current Medications": self.current_medications,
            "Allergies": self.allergies,
            "Past Surgeries": self.past_surgeries,
            "Chronic Conditions": self.chronic_conditions
        }