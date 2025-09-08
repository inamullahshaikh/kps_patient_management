from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["hospital"]

collections = {
    "medicine": db["medicines"],
    "medication": db["medications"],
    "allergy": db["allergies"],
    "allergy_diagnosis": db["allergy_diagnoses"],
    "condition": db["conditions"],
    "condition_diagnosis": db["condition_diagnoses"],
    "surgery": db["surgeries"],
    "past_surgery": db["past_surgeries"],
    "medical_history": db["medical_histories"],
    "insurance": db["insurances"],
    "contact_details": db["contact_details"],
    "doctor": db["doctors"],
    "admin": db["admins"],
    "patient": db["patients"],
}
