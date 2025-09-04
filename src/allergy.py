class Allergy:
    def __init__(self, substance: str, severity: str, reaction: str):
        self.substance = substance
        self.severity = severity
        self.reaction = reaction

    def __str__(self):
        return f"{self.substance} (Severity: {self.severity}, Reaction: {self.reaction})"
