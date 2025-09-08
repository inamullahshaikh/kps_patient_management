from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRouter
from bson import ObjectId
from schema import APIResponse
from registry import registry
from datetime import date, datetime

app = FastAPI(title="Medical System API")
router = APIRouter()


def validate_id(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
    return ObjectId(id)


def to_mongo_dict(obj: dict) -> dict:
    """Convert any date/datetime in the dict into ISO strings before saving"""
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
    """Convert MongoDB document to JSON-serializable dict"""
    if not doc:
        return None
    doc = dict(doc)
    if "_id" in doc:  # only convert if raw MongoDB doc
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc


def serialize_data(data):
    """Ensure everything returned is JSON-safe"""
    if isinstance(data, list):
        return [serialize_doc(d) for d in data]
    if isinstance(data, dict):
        return serialize_doc(data)
    if isinstance(data, ObjectId):
        return str(data)
    return data


@router.post("/{entity}")
async def create_entity(entity: str, payload: dict):
    if entity not in registry:
        raise HTTPException(status_code=404, detail="Entity not found")

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


app.include_router(router, prefix="/api", tags=["CRUD"])
