from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from .auth import *
import uuid
from .schema import *
from .database import collections
from fastapi import Body
from datetime import datetime
from typing import Type
app = FastAPI(title="Hospital Management API")

@app.post("/signup")
async def signup(new_user: Person,current_user: Optional[Person] = Depends(get_current_user)):
    if new_user.role == RoleEnum.PATIENT:
        if current_user is None:
            pass  
        elif current_user.role in [RoleEnum.RECEPTIONIST, RoleEnum.PATIENT]:
            pass  
        else:
            raise HTTPException(status_code=403, detail="Not authorized to create patient profiles")

        existing = await collections["persons"].find_one({"username": new_user.username})
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")

        patient_uuid = str(uuid.uuid4())

        user_dict = new_user.dict(by_alias=True)
        user_dict["uuid"] = patient_uuid
        user_dict["password"] = hash_password(new_user.password)

        await collections["persons"].insert_one(user_dict)

        medical_history = MedicalHistory(patient_id=patient_uuid)
        await collections["medical_history"].insert_one(medical_history.dict(by_alias=True))

        return {"message": "Patient profile created successfully", "uuid": patient_uuid}

    if not current_user or current_user.role != RoleEnum.ADMIN:
        print(current_user.role)
        print(RoleEnum.ADMIN)
        raise HTTPException(status_code=403, detail="Only admin can create this type of user")

    existing = await collections["persons"].find_one({"username": new_user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_uuid = str(uuid.uuid4())

    user_dict = new_user.dict(by_alias=True)
    user_dict["uuid"] = user_uuid
    user_dict["password"] = hash_password(new_user.password)

    await collections["persons"].insert_one(user_dict)
    return {"message": f"{new_user.role.value} profile created successfully", "uuid": user_uuid}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "uuid": user.uuid
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "uuid": user.uuid
    }


@app.get("/patients", response_model=APIResponse[List[Person]])
async def list_patients(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    patients_cursor = collections["persons"].find({"role": RoleEnum.PATIENT})
    patients: List[Person] = []
    async for doc in patients_cursor:
        patients.append(Person(**doc)) 

    return APIResponse[List[Person]](
        code=200,
        message="Patients retrieved successfully",
        data=patients
    )
@app.get("/receptionists", response_model=APIResponse[List[Person]])
async def list_receptionists(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    receptionists_cursor = collections["persons"].find({"role": RoleEnum.RECEPTIONIST})
    receptionists: List[Person] = []
    async for doc in receptionists_cursor:
        receptionists.append(Person(**doc)) 

    return APIResponse[List[Person]](
        code=200,
        message="Receptionists retrieved successfully",
        data=receptionists
    )

@app.get("/receptionist/{uuid}", response_model=APIResponse[Person])
async def get_receptionist(uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.ADMIN and current_user.uuid != uuid:
        raise HTTPException(status_code=403, detail="Not authorized")

    doc = await collections["persons"].find_one({"uuid": uuid, "role": RoleEnum.RECEPTIONIST})
    if not doc:
        raise HTTPException(status_code=404, detail="Receptionist not found")

    receptionist = Person(**doc)
    return APIResponse[Person](
        code=200,
        message="Receptionist retrieved successfully",
        data=receptionist
    )

@app.put("/persons/{uuid}", response_model=APIResponse[Person])
async def update_person(
    uuid: str,
    updated_data: Person = Body(...),
    current_user: Person = Depends(get_current_user)
):
    person_doc = await collections["persons"].find_one({"uuid": uuid})
    if not person_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Only admin or owner can update
    if current_user.role != RoleEnum.ADMIN and current_user.uuid != uuid:
        raise HTTPException(status_code=403, detail="You can only update your own account")

    # Preserve role if not admin
    if current_user.role != RoleEnum.ADMIN:
        updated_data.role = person_doc.get("role")

    # Hash password if changed
    if updated_data.password and updated_data.password != person_doc.get("password"):
        updated_data.password = hash_password(updated_data.password)
    else:
        updated_data.password = person_doc.get("password")

    # Only update fields provided
    update_dict = {k: v for k, v in updated_data.dict(exclude_unset=True).items() if v is not None}

    await collections["persons"].update_one(
        {"uuid": uuid},
        {"$set": update_dict}
    )

    updated_person_doc = await collections["persons"].find_one({"uuid": uuid})
    return APIResponse[Person](
        code=200,
        message="User updated successfully",
        data=Person(**updated_person_doc)
    )


@app.delete("/persons/{uuid}", response_model=APIResponse[None])
async def delete_person(uuid: str, current_user: Person = Depends(get_current_user)):
    person_doc = await collections["persons"].find_one({"uuid": uuid})
    if not person_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    if current_user.role != RoleEnum.ADMIN and current_user.uuid != uuid:
        raise HTTPException(status_code=403, detail="You can only delete your own account")

    if person_doc["role"] == RoleEnum.PATIENT:
        medical_history_doc = await collections["medical_history"].find_one({"patient_id": uuid})
        if medical_history_doc:
            medical_history_id = medical_history_doc["uuid"]

            await collections["medication"].delete_many({"medical_history_id": medical_history_id})
            await collections["past_surgery"].delete_many({"medical_history_id": medical_history_id})
            await collections["condition_diagnosis"].delete_many({"medical_history_id": medical_history_id})
            await collections["allergy_diagnosis"].delete_many({"medical_history_id": medical_history_id})
            await collections["medical_history"].delete_one({"uuid": medical_history_id})

    await collections["persons"].delete_one({"uuid": uuid})
    message = "User deleted successfully" if current_user.role == RoleEnum.ADMIN else "Your account has been deleted successfully"
    return APIResponse[None](code=200, message=message, data=None)


@app.get("/patients/{uuid}", response_model=APIResponse[dict])
async def get_patient_full(
    uuid: str,
    current_user: Person = Depends(get_current_user)
):
    if current_user.role == RoleEnum.PATIENT:
        if current_user.uuid != uuid: 
            raise HTTPException(status_code=403, detail="Not authorized to view other patients")
    elif current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    patient_doc = await collections["persons"].find_one({"uuid": uuid, "role": RoleEnum.PATIENT})
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient = Person(**patient_doc)

    medical_history_doc = await collections["medical_history"].find_one({"patient_id": uuid})
    if not medical_history_doc:
        medical_history_data = {}
    else:
        medical_history_id = medical_history_doc["uuid"]

        medications_cursor = collections["medication"].find({"medical_history_id": medical_history_id})
        medications = [Medication(**m) async for m in medications_cursor]

        surgeries_cursor = collections["past_surgery"].find({"medical_history_id": medical_history_id})
        past_surgeries = [PastSurgery(**s) async for s in surgeries_cursor]

        conditions_cursor = collections["condition_diagnosis"].find({"medical_history_id": medical_history_id})
        condition_diagnoses = [ConditionDiagnosis(**c) async for c in conditions_cursor]

        allergies_cursor = collections["allergy_diagnosis"].find({"medical_history_id": medical_history_id})
        allergy_diagnoses = [AllergyDiagnosis(**a) async for a in allergies_cursor]

        medical_history_data = {
            "uuid": medical_history_id,
            "medications": medications,
            "past_surgeries": past_surgeries,
            "condition_diagnoses": condition_diagnoses,
            "allergy_diagnoses": allergy_diagnoses
        }

    result = patient.dict()
    result["medical_history"] = medical_history_data

    return APIResponse[dict](
        code=200,
        message="Patient with medical history retrieved successfully",
        data=result
    )



@app.get("/doctors", response_model=APIResponse[List[Person]])
async def list_doctors(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.RECEPTIONIST, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    doctors_cursor = collections["persons"].find({"role": RoleEnum.DOCTOR})
    doctors: List[Person] = []
    async for doc in doctors_cursor:
        if current_user.role == RoleEnum.RECEPTIONIST:
            doc["password"] = "**************"
        doctors.append(Person(**doc))

    return APIResponse[List[Person]](
        code=200,
        message="Doctors retrieved successfully",
        data=doctors
    )

@app.get("/doctors/{uuid}", response_model=APIResponse[Person])
async def get_doctor(
    uuid: str,
    current_user: Person = Depends(get_current_user)
):
    doctor_doc = await collections["persons"].find_one(
        {"uuid": uuid, "role": RoleEnum.DOCTOR}
    )
    if not doctor_doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if current_user.role == RoleEnum.DOCTOR and current_user.uuid != uuid:
        raise HTTPException(status_code=403, detail="Doctors can only view their own profile")
    doctor = Person(**doctor_doc)
    if current_user.role in [RoleEnum.RECEPTIONIST, RoleEnum.PATIENT]:
        doctor.password = None  
    return APIResponse[Person](
        code=200,
        message="Doctor retrieved successfully",
        data=doctor
    )

@app.get("/receive-patient", response_model=APIResponse[Person])
async def receive_patient(username: Optional[str] = Query(None), uuid: Optional[str] = Query(None), current_user: Person = Depends(get_current_user)):
    print(current_user)
    if current_user.role not in RoleEnum.RECEPTIONIST:
        raise HTTPException(status_code=403, detail=f"{current_user.role} Not a receptionist")

    if not username and not uuid:
        raise HTTPException(status_code=400, detail="Provide either username or uuid")

    query = {"role": RoleEnum.PATIENT}
    if username:
        query["username"] = username
    if uuid:
        query["uuid"] = uuid

    patient_doc = await collections["persons"].find_one(query)
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_doc["password"] = None  

    patient = Person(**patient_doc)

    return APIResponse[Person](
        code=200,
        message="Patient details retrieved successfully",
        data=patient
    )

entity_access = {
    "allergy": {"create": [RoleEnum.DOCTOR], "read": [RoleEnum.DOCTOR, RoleEnum.ADMIN],
                "update": [RoleEnum.DOCTOR], "delete": [RoleEnum.DOCTOR, RoleEnum.ADMIN]},
    "condition": {"create": [RoleEnum.DOCTOR], "read": [RoleEnum.DOCTOR, RoleEnum.ADMIN],
                  "update": [RoleEnum.DOCTOR], "delete": [RoleEnum.DOCTOR, RoleEnum.ADMIN]},
    "medicine": {"create": [RoleEnum.DOCTOR], "read": [RoleEnum.DOCTOR, RoleEnum.ADMIN],
                 "update": [RoleEnum.DOCTOR], "delete": [RoleEnum.DOCTOR, RoleEnum.ADMIN]},
    "surgery": {"create": [RoleEnum.DOCTOR], "read": [RoleEnum.DOCTOR, RoleEnum.ADMIN],
                "update": [RoleEnum.DOCTOR], "delete": [RoleEnum.DOCTOR, RoleEnum.ADMIN]},
}

async def create_entity(entity_name: str, data: BaseModel, current_user: Person):
    if current_user.role not in entity_access[entity_name]["create"]:
        raise HTTPException(status_code=403, detail=f"Not authorized to create {entity_name}")
    result = await collections[entity_name].insert_one(data.dict(by_alias=True))
    created = await collections[entity_name].find_one({"_id": result.inserted_id})
    return APIResponse(code=201, message=f"{entity_name.capitalize()} created successfully", data=data.__class__(**created))


async def list_entities(entity_name: str, model: Type[BaseModel], current_user: Person):
    if current_user.role not in entity_access[entity_name]["read"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    cursor = collections[entity_name].find()
    items: List[BaseModel] = [model(**doc) async for doc in cursor]
    return APIResponse[List[BaseModel]](code=200, message=f"{entity_name.capitalize()}s retrieved successfully", data=items)


async def get_entity(entity_name: str, uuid: str, model: Type[BaseModel], current_user: Person):
    if current_user.role not in entity_access[entity_name]["read"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    doc = await collections[entity_name].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"{entity_name.capitalize()} not found")
    return APIResponse[model](code=200, message=f"{entity_name.capitalize()} retrieved successfully", data=model(**doc))


async def update_entity(entity_name: str, uuid: str, data: BaseModel, current_user: Person):
    if current_user.role not in entity_access[entity_name]["update"]:
        raise HTTPException(status_code=403, detail=f"Not authorized to update {entity_name}")
    doc = await collections[entity_name].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"{entity_name.capitalize()} not found")
    await collections[entity_name].update_one(
        {"uuid": uuid},
        {"$set": data.dict(by_alias=True, exclude_unset=True)}
    )
    updated_doc = await collections[entity_name].find_one({"uuid": uuid})
    return APIResponse[BaseModel](code=200, message=f"{entity_name.capitalize()} updated successfully", data=data.__class__(**updated_doc))


async def delete_entity(entity_name: str, uuid: str, current_user: Person):
    if current_user.role not in entity_access[entity_name]["delete"]:
        raise HTTPException(status_code=403, detail=f"Not authorized to delete {entity_name}")
    doc = await collections[entity_name].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"{entity_name.capitalize()} not found")
    await collections[entity_name].delete_one({"uuid": uuid})
    return APIResponse[None](code=200, message=f"{entity_name.capitalize()} deleted successfully", data=None)

@app.post("/allergy", response_model=APIResponse[Allergy])
async def create_allergy_endpoint(allergy_data: Allergy, current_user: Person = Depends(get_current_user)):
    return await create_entity("allergy", allergy_data, current_user)

@app.get("/allergy", response_model=APIResponse[List[Allergy]])
async def list_allergies_endpoint(current_user: Person = Depends(get_current_user)):
    return await list_entities("allergy", Allergy, current_user)

@app.get("/allergy/{uuid}", response_model=APIResponse[Allergy])
async def get_allergy_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await get_entity("allergy", uuid, Allergy, current_user)

@app.put("/allergy/{uuid}", response_model=APIResponse[Allergy])
async def update_allergy_endpoint(uuid: str, allergy_data: Allergy = Body(...), current_user: Person = Depends(get_current_user)):
    return await update_entity("allergy", uuid, allergy_data, current_user)

@app.delete("/allergy/{uuid}", response_model=APIResponse[None])
async def delete_allergy_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await delete_entity("allergy", uuid, current_user)

@app.post("/condition", response_model=APIResponse[Condition])
async def create_condition_endpoint(condition_data: Condition, current_user: Person = Depends(get_current_user)):
    return await create_entity("condition", condition_data, current_user)

@app.get("/condition", response_model=APIResponse[List[Condition]])
async def list_conditions_endpoint(current_user: Person = Depends(get_current_user)):
    return await list_entities("condition", Condition, current_user)

@app.get("/condition/{uuid}", response_model=APIResponse[Condition])
async def get_condition_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await get_entity("condition", uuid, Condition, current_user)

@app.put("/condition/{uuid}", response_model=APIResponse[Condition])
async def update_condition_endpoint(uuid: str, condition_data: Condition = Body(...), current_user: Person = Depends(get_current_user)):
    return await update_entity("condition", uuid, condition_data, current_user)

@app.delete("/condition/{uuid}", response_model=APIResponse[None])
async def delete_condition_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await delete_entity("condition", uuid, current_user)

@app.post("/medicine", response_model=APIResponse[Medicine])
async def create_medicine_endpoint(medicine_data: Medicine, current_user: Person = Depends(get_current_user)):
    return await create_entity("medicine", medicine_data, current_user)

@app.get("/medicine", response_model=APIResponse[List[Medicine]])
async def list_medicines_endpoint(current_user: Person = Depends(get_current_user)):
    return await list_entities("medicine", Medicine, current_user)

@app.get("/medicine/{uuid}", response_model=APIResponse[Medicine])
async def get_medicine_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await get_entity("medicine", uuid, Medicine, current_user)

@app.put("/medicine/{uuid}", response_model=APIResponse[Medicine])
async def update_medicine_endpoint(uuid: str, medicine_data: Medicine = Body(...), current_user: Person = Depends(get_current_user)):
    return await update_entity("medicine", uuid, medicine_data, current_user)

@app.delete("/medicine/{uuid}", response_model=APIResponse[None])
async def delete_medicine_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await delete_entity("medicine", uuid, current_user)

@app.post("/surgery", response_model=APIResponse[Surgery])
async def create_surgery_endpoint(surgery_data: Surgery, current_user: Person = Depends(get_current_user)):
    return await create_entity("surgery", surgery_data, current_user)

@app.get("/surgery", response_model=APIResponse[List[Surgery]])
async def list_surgeries_endpoint(current_user: Person = Depends(get_current_user)):
    return await list_entities("surgery", Surgery, current_user)

@app.get("/surgery/{uuid}", response_model=APIResponse[Surgery])
async def get_surgery_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await get_entity("surgery", uuid, Surgery, current_user)

@app.put("/surgery/{uuid}", response_model=APIResponse[Surgery])
async def update_surgery_endpoint(uuid: str, surgery_data: Surgery = Body(...), current_user: Person = Depends(get_current_user)):
    return await update_entity("surgery", uuid, surgery_data, current_user)

@app.delete("/surgery/{uuid}", response_model=APIResponse[None])
async def delete_surgery_endpoint(uuid: str, current_user: Person = Depends(get_current_user)):
    return await delete_entity("surgery", uuid, current_user)


@app.post("/doctor/prescribe-medicine/{patient_uuid}",response_model=APIResponse[Medication])
async def prescribe_medication(patient_uuid: str, medication_data: Medication = Body(...), current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can prescribe medication")

    patient_doc = await collections["persons"].find_one(
        {"uuid": patient_uuid, "role": RoleEnum.PATIENT}
    )
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    medicine_doc = await collections["medicine"].find_one({"uuid": medication_data.medicine_id})
    if not medicine_doc:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medical_history = await collections["medical_history"].find_one(
        {"patient_id": patient_uuid}
    )
    if not medical_history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    new_medication = Medication(
        medicine_id=medication_data.medicine_id,
        medical_history_id=medical_history["uuid"],
        dosage=medication_data.dosage,
        starting_date=medication_data.starting_date,
        ending_date=medication_data.ending_date,
        prescribing_doctor_id=current_user.uuid,
    )

    await collections["medication"].insert_one(new_medication.dict(by_alias=True))

    return APIResponse[Medication](
        code=201,
        message="Medication prescribed successfully",
        data=new_medication
    )



@app.delete("/doctor/prescribe-medicine/{medication_uuid}", response_model=APIResponse[None])
async def delete_medication(medication_uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can delete medication")
    medication_doc = await collections["medication"].find_one({"uuid": medication_uuid})
    if not medication_doc:
        raise HTTPException(status_code=404, detail="Medication not found")
    await collections["medication"].delete_one({"uuid": medication_uuid})
    return APIResponse[None](code=200, message="Medication deleted successfully", data=None)


@app.post("/doctor/record-surgery/{patient_uuid}", response_model=APIResponse[PastSurgery])
async def record_surgery(patient_uuid: str, surgery_data: PastSurgery = Body(...), current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can record surgeries")

    patient_doc = await collections["persons"].find_one(
        {"uuid": patient_uuid, "role": RoleEnum.PATIENT}
    )
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    surgery_doc = await collections["surgery"].find_one({"uuid": surgery_data.surgery_id})
    if not surgery_doc:
        raise HTTPException(status_code=404, detail="Surgery not found")

    medical_history = await collections["medical_history"].find_one(
        {"patient_id": patient_uuid}
    )
    if not medical_history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    new_surgery = PastSurgery(
        surgery_id=surgery_data.surgery_id,
        medical_history_id=medical_history["uuid"],
        date=surgery_data.date,
        surgeon_id=current_user.uuid,
        complications=surgery_data.complications,
        notes=surgery_data.notes,
        outcome=surgery_data.outcome
    )

    await collections["past_surgery"].insert_one(new_surgery.dict(by_alias=True))

    return APIResponse[PastSurgery](
        code=201,
        message="Surgery recorded successfully",
        data=new_surgery
    )

@app.delete("/doctor/record-surgery/{surgery_uuid}", response_model=APIResponse[None])
async def delete_surgery(surgery_uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR or current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only doctors can delete surgeries")
    surgery_doc = await collections["past_surgery"].find_one({"uuid": surgery_uuid})
    if not surgery_doc:
        raise HTTPException(status_code=404, detail="Surgery not found")
    await collections["past_surgery"].delete_one({"uuid": surgery_uuid})
    return APIResponse[None](code=200, message="Surgery deleted successfully", data=None)


@app.post("/doctor/diagnose-condition/{patient_uuid}",response_model=APIResponse[ConditionDiagnosis])
async def diagnose_condition(patient_uuid: str, diagnosis_data: ConditionDiagnosis = Body(...), current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can diagnose conditions")
    
    patient_doc = await collections["persons"].find_one(
        {"uuid": patient_uuid, "role": RoleEnum.PATIENT}
    )
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    condition_doc = await collections["condition"].find_one({"uuid": diagnosis_data.condition_id})
    if not condition_doc:
        raise HTTPException(status_code=404, detail="Condition not found")
    medical_history = await collections["medical_history"].find_one(
        {"patient_id": patient_uuid}
    )
    if not medical_history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    new_condition = ConditionDiagnosis(
        condition_id=diagnosis_data.condition_id,
        medical_history_id=medical_history["uuid"],
        severity=diagnosis_data.severity,
        diagnosing_doctor_id=current_user.uuid,
        diagnosis_date=diagnosis_data.diagnosis_date,
        triggers=diagnosis_data.triggers
    )

    await collections["condition_diagnosis"].insert_one(new_condition.dict(by_alias=True))

    return APIResponse[ConditionDiagnosis](
        code=201,
        message="Condition diagnosed successfully",
        data=new_condition
    )


@app.delete("/doctor/diagnose-condition/{condition_diagnosis_uuid}", response_model=APIResponse[None])
async def delete_condition_diagnosis(condition_diagnosis_uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR or current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Only doctors and admins can delete condition diagnoses")
    diagnosis_doc = await collections["condition_diagnosis"].find_one({"uuid": condition_diagnosis_uuid})
    if not diagnosis_doc:
        raise HTTPException(status_code=404, detail="Condition diagnosis not found")
    await collections["condition_diagnosis"].delete_one({"uuid": condition_diagnosis_uuid})
    return APIResponse[None](code=200, message="Condition diagnosis deleted successfully", data=None)

@app.post("/doctor/diagnose-allergy/{patient_uuid}", response_model=APIResponse[AllergyDiagnosis])
async def diagnose_allergy(patient_uuid: str, diagnosis_data: AllergyDiagnosis = Body(...), current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can diagnose allergies")

    patient_doc = await collections["persons"].find_one(
        {"uuid": patient_uuid, "role": RoleEnum.PATIENT}
    )
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Check if allergy exists
    allergy_doc = await collections["allergy"].find_one({"uuid": diagnosis_data.allergy_id})
    if not allergy_doc:
        raise HTTPException(status_code=404, detail="Allergy not found")

    medical_history = await collections["medical_history"].find_one(
        {"patient_id": patient_uuid}
    )
    if not medical_history:
        raise HTTPException(status_code=404, detail="Medical history not found")

    new_allergy = AllergyDiagnosis(
        allergy_id=diagnosis_data.allergy_id,
        medical_history_id=medical_history["uuid"],
        severity=diagnosis_data.severity,
        diagnosing_doctor_id=current_user.uuid,
        diagnosis_date=diagnosis_data.diagnosis_date
    )

    await collections["allergy_diagnosis"].insert_one(new_allergy.dict(by_alias=True))

    return APIResponse[AllergyDiagnosis](
        code=201,
        message="Allergy diagnosed successfully",
        data=new_allergy
    )

@app.delete("/doctor/diagnose-allergy/{allergy_diagnosis_uuid}", response_model=APIResponse[None])
async def delete_allergy_diagnosis(allergy_diagnosis_uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can delete allergy diagnoses")
    diagnosis_doc = await collections["allergy_diagnosis"].find_one({"uuid": allergy_diagnosis_uuid})
    if not diagnosis_doc:
        raise HTTPException(status_code=404, detail="Allergy diagnosis not found")
    await collections["allergy_diagnosis"].delete_one({"uuid": allergy_diagnosis_uuid})
    return APIResponse[None](code=200, message="Allergy diagnosis deleted successfully", data=None)
