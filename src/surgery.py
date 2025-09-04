from datetime import date

class Surgery:
    def __init__(self, name: str, surgery_date: date, hospital: str, price: float):
        self.name = name
        self.surgery_date = surgery_date
        self.hospital = hospital
        self.price = price 

    def __str__(self):
        return f"{self.name} on {self.surgery_date} at {self.hospital} - PKR{self.price:.2f}"
