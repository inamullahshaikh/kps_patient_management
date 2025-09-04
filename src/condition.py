from datetime import date
class Condition:
    def __init__(self, name: str, diagnosed_date: date, status: str):
        self.name = name
        self.diagnosed_date = diagnosed_date
        self.status = status

    def __str__(self):
        return f"{self.name} (Diagnosed: {self.diagnosed_date}, Status: {self.status})"
