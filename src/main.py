from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.routing import APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bson import ObjectId
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import date, datetime, timedelta
from typing import Optional
from schema import APIResponse, Admin
from registry import registry
import os

app = FastAPI(title="Medical System API with JWT Auth")
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def validate_id(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    return ObjectId(id)

def to_mongo_dict(obj: dict) -> dict:
    new_obj = {}
    for k, v in obj.items():
        if isinstance(v, (date, datetime)):
            new_obj[k] = v.isoformat()
        elif isinstance(v, dict):
            new_obj[k] = to_mongo_dict(v)
        elif isinstance(v, list):
            new_obj[k] = [
                to_mongo_dict(x) if isinstance(x, dict)
                else (x.isoformat() if isinstance(x, (date, datetime)) else x)
                for x in v
            ]
        else:
            new_obj[k] = v
    return new_obj


def serialize_doc(doc: dict) -> dict:
    if not doc:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


def serialize_data(data):
    if isinstance(data, list):
        return [serialize_doc(d) for d in data]
    if isinstance(data, dict):
        return serialize_doc(data)
    if isinstance(data, ObjectId):
        return str(data)
    return data

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        role: str = payload.get("role")
        if admin_id is None or role != "Admin":
            raise HTTPException(status_code=403, detail="Not authorized")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    admin_collection = registry["admin"]["collection"]
    admin = await admin_collection.find_one({"_id": ObjectId(admin_id)})
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    return serialize_doc(admin)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_collection = registry["admin"]["collection"]

    admin = await admin_collection.find_one({"username": form_data.username})
    if not admin:
        raise HTTPException(status_code=400, detail="Invalid username or password")

    if not verify_password(form_data.password, admin["password"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin["_id"]), "role": "Admin"},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/{entity}")
async def create_entity(entity: str, payload: dict):
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

    if "password" in payload:
        payload["password"] = get_password_hash(payload["password"])

    model = registry[entity]["model"]
    collection = registry[entity]["collection"]

    obj = model(**payload)
    mongo_doc = to_mongo_dict(obj.dict(by_alias=True))
    result = await collection.insert_one(mongo_doc)
    new_doc = await collection.find_one({"_id": result.inserted_id})

    return APIResponse(
        code=201,
        message=f"{entity} created",
        data=serialize_data(new_doc),
    )



@router.get("/{entity}/{id}")
async def get_entity(entity: str, id: str):
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

    collection = registry[entity]["collection"]
    obj = await collection.find_one({"_id": validate_id(id)})
    if not obj:
        raise HTTPException(status_code=404, detail=f"{entity} not found")

    return APIResponse(
        code=200,
        message=f"{entity} retrieved",
        data=serialize_data(obj),
    )


@router.get("/{entity}")
async def list_entities(entity: str):
    if entity == "doctor" or entity == "patient":
        raise HTTPException(status_code=400, detail="Private Information only admin can access")
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

    collection = registry[entity]["collection"]
    results = []
    async for doc in collection.find():
        results.append(serialize_doc(doc))

    return APIResponse(
        code=200,
        message=f"{entity} list",
        data=serialize_data(results),
    )


@router.put("/{entity}/{id}")
async def update_entity(entity: str, id: str, payload: dict):
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

    collection = registry[entity]["collection"]
    payload = to_mongo_dict(payload)
    update_result = await collection.update_one(
        {"_id": validate_id(id)}, {"$set": payload}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"{entity} not found")

    updated_doc = await collection.find_one({"_id": validate_id(id)})
    return APIResponse(
        code=200,
        message=f"{entity} updated",
        data=serialize_data(updated_doc),
    )


@router.delete("/{entity}/{id}")
async def delete_entity(entity: str, id: str):
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

    collection = registry[entity]["collection"]
    delete_result = await collection.delete_one({"_id": validate_id(id)})

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"{entity} not found")

    return APIResponse(
        code=200,
        message=f"{entity} deleted",
        data={"id": id},
    )

@router.get("/patient/{id}/details")
async def get_patient_details(id: str):
    patient_collection = registry["patient"]["collection"]
    insurance_collection = registry["insurance"]["collection"]
    history_collection = registry["medical_history"]["collection"]
    allergy_collection = registry["allergy_diagnosis"]["collection"]
    condition_collection = registry["condition_diagnosis"]["collection"]
    surgery_collection = registry["past_surgery"]["collection"]
    medication_collection = registry["medication"]["collection"]

    patient = await patient_collection.find_one({"_id": validate_id(id)})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    insurances = []
    async for ins in insurance_collection.find({"patient_id": validate_id(id)}):
        insurances.append(serialize_doc(ins))

    histories = []
    async for hist in history_collection.find({"patient_id": validate_id(id)}):
        hist_doc = serialize_doc(hist)

        allergies = []
        async for a in allergy_collection.find({"medical_history_id": hist["_id"]}):
            allergies.append(serialize_doc(a))

        conditions = []
        async for c in condition_collection.find({"medical_history_id": hist["_id"]}):
            conditions.append(serialize_doc(c))

        surgeries = []
        async for s in surgery_collection.find({"medical_history_id": hist["_id"]}):
            surgeries.append(serialize_doc(s))

        medications = []
        async for m in medication_collection.find({"medical_history_id": hist["_id"]}):
            medications.append(serialize_doc(m))

        hist_doc["allergies"] = allergies
        hist_doc["conditions"] = conditions
        hist_doc["surgeries"] = surgeries
        hist_doc["medications"] = medications

        histories.append(hist_doc)

    response = {
        "patient": serialize_doc(patient),
        "insurances": insurances,
        "medical_history": histories,
    }

    return APIResponse(
        code=200,
        message="Patient details with insurance and medical history retrieved",
        data=response,
    )

@router.get("/admin/{id}/doctors")
async def list_all_doctors(current_admin=Depends(get_current_admin)):
    doctor_collection = registry["doctor"]["collection"]
    doctors = []
    async for doc in doctor_collection.find():
        doctors.append(serialize_doc(doc))
    return APIResponse(code=200, message="List of doctors", data=doctors)


@router.get("/admin/{id}/patients")
async def list_all_patients(current_admin=Depends(get_current_admin)):
    patient_collection = registry["patient"]["collection"]
    patients = []
    async for doc in patient_collection.find():
        patients.append(serialize_doc(doc))
    return APIResponse(code=200, message="List of patients", data=patients)

app.include_router(router, prefix="/api", tags=["CRUD & Auth"])
