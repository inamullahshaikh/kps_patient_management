from patient import *
from typing import List
class App:
    def __init__(self):
        self._patients: List[Patient] = []
    def add_patient(self, patient):
        for p in self._patients:
            if p.__eq__(patient):
                return {"code": 400, "message": "Patient already exists"}
        self._patients.append(patient)
        return {"code": 201, "message": "Patient added successfully"}

    def remove_patient(self, email):
        for i, p in enumerate(self._patients):
            if p.contact_info.email == email:
                del self._patients[i]
                return {"code": 200, "message": f"Patient with email {email} removed successfully"}
        return {"code": 404, "message": "Patient not found"}

    def update_patient(self, email, **kwargs):
        for patient in self._patients:
            if patient.contact_info.email == email:
                if "name" in kwargs:
                    patient.name = kwargs["name"]
                if "DOB" in kwargs:
                    patient.DOB = kwargs["DOB"]
                if "gender" in kwargs:
                    patient.gender = kwargs["gender"]
                if "email" in kwargs:
                    patient.contact_info.email = kwargs["email"]
                if "phone" in kwargs:
                    patient.contact_info.phone = kwargs["phone"]
                if "address" in kwargs:
                    patient.contact_info.address = kwargs["address"]
                if "blood_group" in kwargs:
                    patient.blood_group = kwargs["blood_group"]

                if "insurance" in kwargs:
                    if isinstance(kwargs["insurance"], Insurance):
                        patient.insurance = kwargs["insurance"]
                    elif isinstance(kwargs["insurance"], dict):
                        ins = kwargs["insurance"]
                        if "provider" in ins:
                            patient.insurance.provider = ins["provider"]
                        if "policy_number" in ins:
                            patient.insurance.policy_number = ins["policy_number"]
                        if "coverage_level" in ins:
                            patient.insurance.coverage_level = ins["coverage_level"]
                        if "hospitalization_rate" in ins:
                            patient.insurance.hospitalization_rate = ins["hospitalization_rate"]
                        if "medicines_rate" in ins:
                            patient.insurance.medicines_rate = ins["medicines_rate"]
                        if "annual_limit" in ins:
                            patient.insurance.annual_limit = ins["annual_limit"]
                        if "international_coverage" in ins:
                            patient.insurance.international_coverage = ins["international_coverage"]

                if "medical_history" in kwargs:
                    mh = kwargs["medical_history"]

                    if isinstance(mh, IMedicalHistory):
                        patient.medical_history = mh

                    elif isinstance(mh, dict):
                        if "add_medication" in mh:
                            for m in mh["add_medication"]:
                                obj = m if isinstance(m, Medication) else Medication(**m)
                                patient.medical_history.add_medication(obj)

                        if "remove_medication" in mh:
                            for m in mh["remove_medication"]:
                                print(m)
                                patient.medical_history.remove_medication(m)

                        if "add_allergy" in mh:
                            for a in mh["add_allergy"]:
                                obj = a if isinstance(a, Allergy) else Allergy(**a)
                                patient.medical_history.add_allergy(obj)

                        if "remove_allergy" in mh:
                            for a in mh["remove_allergy"]:
                                patient.medical_history.remove_allergy(a)

                        if "add_surgery" in mh:
                            for s in mh["add_surgery"]:
                                obj = s if isinstance(s, Surgery) else Surgery(**s)
                                patient.medical_history.add_surgery(obj)

                        if "remove_surgery" in mh:
                            for s in mh["remove_surgery"]:
                                patient.medical_history.remove_surgery(s)

                        if "add_condition" in mh:
                            for c in mh["add_condition"]:
                                obj = c if isinstance(c, Condition) else Condition(**c)
                                patient.medical_history.add_condition(obj)

                        if "remove_condition" in mh:
                            for c in mh["remove_condition"]:
                                patient.medical_history.remove_condition(c)

                return {
                    "code": 200,
                    "message": f"Patient {patient.name} updated successfully",
                    "updated_details": patient.get_details()
                }

        return {"code": 404, "message": "Patient not found"}


    def get_patient(self, email):
        for p in self._patients:
            if p.contact_info.email == email:
                return {
                    "code": 200,
                    "message": "Patient retrieved successfully",
                    "patient": p.get_details()
                }
        return {"code": 404, "message": "Patient not found"}

    def get_all_patients(self):
        p_details = [p.get_details() for p in self._patients]
        if p_details:
            return {
                "code": 200,
                "message": "All patients retrieved successfully",
                "patients": p_details
            }
        return {"code": 404, "message": "No patients found"}

    def add_medication(self, patient_email: str, medication: Medication):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                p.medical_history.add_medication(medication)
                bill = p.insurance.process_bill(
                    hospitalization_cost=0.0,
                    medicines_cost=medication.price
                )
                return {
                    "code": 200,
                    "message": f"Medication '{medication.name}' added to {p.name}",
                    "bill": bill,
                    "updated_history": p.medical_history.get_summary()
                }
        return {"code": 404, "message": "Patient not found"}

    def add_surgery(self, patient_email: str, surgery: Surgery):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                p.medical_history.add_surgery(surgery)
                bill = p.insurance.process_bill(
                    hospitalization_cost=surgery.price,
                    medicines_cost=0.0
                )
                return {
                    "code": 200,
                    "message": f"Surgery '{surgery.name}' added to {p.name}",
                    "bill": bill,
                    "updated_history": p.medical_history.get_summary()
                }
        return {"code": 404, "message": "Patient not found"}

    def add_allergy(self, patient_email: str, allergy: Allergy):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                p.medical_history.add_allergy(allergy)
                return {
                    "code": 200,
                    "message": f"Allergy '{allergy.substance}' added to {p.name}",
                    "updated_history": p.medical_history.get_summary()
                }
        return {"code": 404, "message": "Patient not found"}

    def add_chronic_condition(self, patient_email: str, condition: Condition):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                p.medical_history.add_condition(condition)
                return {
                    "code": 200,
                    "message": f"Chronic condition '{condition.name}' added to {p.name}",
                    "updated_history": p.medical_history.get_summary()
                }
        return {"code": 404, "message": "Patient not found"}

    def remove_medication(self, patient_email: str, medication_name: str):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                for med in p.medical_history.current_medications:
                    if med.name == medication_name:
                        p.medical_history.remove_medication(med)
                        return {
                            "code": 200,
                            "message": f"Medication '{medication_name}' removed from {p.name}",
                            "updated_history": p.medical_history.get_summary()
                        }
                return {"code": 400, "message": f"Medication '{medication_name}' not found"}
        return {"code": 404, "message": "Patient not found"}

    def remove_surgery(self, patient_email: str, surgery_name: str):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                for surg in p.medical_history.past_surgeries:
                    if surg.name == surgery_name:
                        p.medical_history.remove_surgery(surg)
                        return {
                            "code": 200,
                            "message": f"Surgery '{surgery_name}' removed from {p.name}",
                            "updated_history": p.medical_history.get_summary()
                        }
                return {"code": 400, "message": f"Surgery '{surgery_name}' not found"}
        return {"code": 404, "message": "Patient not found"}

    def remove_allergy(self, patient_email: str, allergy_name: str):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                for allergy in p.medical_history.allergies:
                    if allergy.name == allergy_name:
                        p.medical_history.remove_allergy(allergy)
                        return {
                            "code": 200,
                            "message": f"Allergy '{allergy_name}' removed from {p.name}",
                            "updated_history": p.medical_history.get_summary()
                        }
                return {"code": 400, "message": f"Allergy '{allergy_name}' not found"}
        return {"code": 404, "message": "Patient not found"}

    def remove_chronic_condition(self, patient_email: str, condition_name: str):
        for p in self._patients:
            if p.contact_info.email == patient_email:
                for cond in p.medical_history.chronic_conditions:
                    if cond.name == condition_name:
                        p.medical_history.remove_condition(cond)
                        return {
                            "code": 200,
                            "message": f"Chronic condition '{condition_name}' removed from {p.name}",
                            "updated_history": p.medical_history.get_summary()
                        }
                return {"code": 400, "message": f"Condition '{condition_name}' not found"}
        return {"code": 404, "message": "Patient not found"}
