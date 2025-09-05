from fastapi import FastAPI, HTTPException, Path, Body
from typing import Any, Dict, Optional
from pydantic import BaseModel
from registry import registry

app = FastAPI(title="Hospital Generic CRUD")

@app.post("/patients", response_model=registry["patient"]["model"])
def create_patient(payload: registry["patient"]["model"] = Body(...)):
    inserted_id = create_one(
        collection=registry["patient"]["collection"], 
        payload=payload
    )
    return {**payload.dict(), "_id": inserted_id}