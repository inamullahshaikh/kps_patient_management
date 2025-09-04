class Medication:
    def __init__(self, name: str, dosage: str, frequency: str, price: float):
        self.name = name
        self.dosage = dosage  
        self.frequency = frequency  
        self.price = price 

    def __str__(self):
        return f"{self.name} ({self.dosage}, {self.frequency}) - PKR{self.price:.2f}"
