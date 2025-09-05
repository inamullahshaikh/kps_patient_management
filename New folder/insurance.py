from abc import ABC, abstractmethod

class Insurance(ABC):
    def __init__(self, provider: str, policy_number: str):
        self.provider = provider
        self.policy_number = policy_number
        self._coverage_level = None
        self._hospitalization_rate = None
        self._medicines_rate = None
        self._annual_limit = None
        self._international_coverage = None
        self.set_coverage_details()

    @property
    def provider(self):
        return self._provider

    @provider.setter
    def provider(self, value):
        if not value.strip():
            raise ValueError("Provider cannot be empty")
        self._provider = value

    @property
    def policy_number(self):
        return self._policy_number

    @policy_number.setter
    def policy_number(self, value):
        if not value.strip():
            raise ValueError("Policy number cannot be empty")
        self._policy_number = value

    @property
    def coverage_level(self):
        return self._coverage_level

    @coverage_level.setter
    def coverage_level(self, value):
        if value not in ["Basic", "Good", "Best"]:
            raise ValueError("Coverage level must be 'Basic', 'Good', or 'Best'")
        self._coverage_level = value

    @property
    def hospitalization_rate(self):
        return self._hospitalization_rate

    @hospitalization_rate.setter
    def hospitalization_rate(self, value: float):
        if not (0 <= value <= 1):
            raise ValueError("Hospitalization rate must be between 0 and 1")
        self._hospitalization_rate = value

    @property
    def medicines_rate(self):
        return self._medicines_rate

    @medicines_rate.setter
    def medicines_rate(self, value: float):
        if not (0 <= value <= 1):
            raise ValueError("Medicines rate must be between 0 and 1")
        self._medicines_rate = value

    @property
    def annual_limit(self):
        return self._annual_limit

    @annual_limit.setter
    def annual_limit(self, value: float):
        if value < 0:
            raise ValueError("Annual limit must be a positive number")
        self._annual_limit = value

    @property
    def international_coverage(self):
        return self._international_coverage

    @international_coverage.setter
    def international_coverage(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("International coverage must be True or False")
        self._international_coverage = value

    @abstractmethod
    def set_coverage_details(self):
        pass

    def get_coverage_details(self):
        return {
            "Provider": self.provider,
            "Policy Number": self.policy_number,
            "Coverage Level": self.coverage_level,
            "Hospitalization Rate": self.hospitalization_rate,
            "Medicines Rate": self.medicines_rate,
            "Annual Limit": self.annual_limit,
            "International Coverage": self.international_coverage
        }

    def process_bill(self, hospitalization_cost: float, medicines_cost: float):
        total_bill = hospitalization_cost + medicines_cost
        covered_hospitalization = hospitalization_cost * self.hospitalization_rate
        covered_medicines = medicines_cost * self.medicines_rate
        total_covered = covered_hospitalization + covered_medicines
        if total_covered > self.annual_limit:
            total_covered = self.annual_limit
        self._annual_limit -= total_covered
        patient_pays = total_bill - total_covered
        return {
            "Total Bill": total_bill,
            "Covered Hospitalization": covered_hospitalization,
            "Covered Medicines": covered_medicines,
            "Total Covered": total_covered,
            "Patient Pays": patient_pays,
            "Remaining Annual Limit": self.annual_limit
        }


class BasicInsurance(Insurance):
    def set_coverage_details(self):
        self.coverage_level = "Basic"
        self.hospitalization_rate = 0.5  
        self.medicines_rate = 0.0        
        self.annual_limit = 100_000      
        self.international_coverage = False


class GoodInsurance(Insurance):
    def set_coverage_details(self):
        self.coverage_level = "Good"
        self.hospitalization_rate = 0.75  
        self.medicines_rate = 0.5         
        self.annual_limit = 500_000   
        self.international_coverage = False


class BestInsurance(Insurance):
    def set_coverage_details(self):
        self.coverage_level = "Best"
        self.hospitalization_rate = 1.0  
        self.medicines_rate = 0.8         
        self.annual_limit = 1_500_000   
        self.international_coverage = True
