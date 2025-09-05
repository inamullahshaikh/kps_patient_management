from abc import ABC, abstractmethod
from datetime import datetime
class ContactInfo:
    def __init__(self, email: str, phone: str, address: str):
        self.email = email
        self.phone = phone
        self.address = address

    @property
    def email(self):
        return self._email
    
    @email.setter
    def email(self, value):
        if "@" not in value:
            raise ValueError("Invalid email address")
        self._email = value

    @property
    def phone(self):
        return self._phone
    
    @phone.setter
    def phone(self, value):
        if not value.isdigit() and not value.startswith("+"):
            raise ValueError("Phone must contain only digits or start with +")
        self._phone = value

    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, value):
        if not value.strip():
            raise ValueError("Address cannot be empty")
        self._address = value


# ---- Abstract Person ----
class Person(ABC):
    def __init__(self, name, DOB, gender, contact_info: ContactInfo):
        self.name = name
        self.DOB = DOB
        self.gender = gender
        self.contact_info = contact_info

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        self._name = value

    @property
    def DOB(self):
        return self._DOB
    
    @DOB.setter
    def DOB(self, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")  # validate format
        except ValueError:
            raise ValueError("DOB must be in YYYY-MM-DD format")
        self._DOB = value

    @property
    def age(self):
        dob_date = datetime.strptime(self._DOB, "%Y-%m-%d").date()
        today = datetime.today().date()
        return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

    @property
    def gender(self):
        return self._gender
    
    @gender.setter
    def gender(self, value):
        allowed = ["Male", "Female", "Other"]
        if value not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        self._gender = value

    @abstractmethod
    def get_details(self):
        pass
