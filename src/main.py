from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)
import uuid
from schema import *
from database import collections
from fastapi import Body
from datetime import datetime
app = FastAPI(title="Hospital Management API")

@app.post("/signup")
async def signup(
    new_user: Person,
    current_user: Optional[Person] = Depends(get_current_user)
):
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

        # Fetch all related data
        medications_cursor = collections["medication"].find({"medical_history_id": medical_history_id})
        medications = [Medication(**m) async for m in medications_cursor]

        surgeries_cursor = collections["past_surgery"].find({"medical_history_id": medical_history_id})
        past_surgeries = [PastSurgery(**s) async for s in surgeries_cursor]

        conditions_cursor = collections["condition_diagnosis"].find({"medical_history_id": medical_history_id})
        condition_diagnoses = [ConditionDiagnosis(**c) async for c in conditions_cursor]

        allergies_cursor = collections["allergy_diagnosis"].find({"medical_history_id": medical_history_id})
        allergy_diagnoses = [AllergyDiagnosis(**a) async for a in allergies_cursor]

        # Assemble medical history
        medical_history_data = {
            "uuid": medical_history_id,
            "medications": medications,
            "past_surgeries": past_surgeries,
            "condition_diagnoses": condition_diagnoses,
            "allergy_diagnoses": allergy_diagnoses
        }

    # Combine patient info + medical history
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

@app.get("/receptionist/receive-patient", response_model=APIResponse[Person])
async def receive_patient(
    username: Optional[str] = Query(None),
    uuid: Optional[str] = Query(None),
    current_user: Person = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.RECEPTIONIST]:
        raise HTTPException(status_code=403, detail="Not authorized")

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

@app.post("/allergy", response_model=APIResponse[Allergy])
async def create_allergy(
    allergy_data: Allergy,
    current_user: Person = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create allergies")

    result = await collections["allergy"].insert_one(allergy_data.dict(by_alias=True))
    created = await collections["allergy"].find_one({"_id": result.inserted_id})
    return APIResponse[Allergy](code=201, message="Allergy created successfully", data=Allergy(**created))


@app.post("/condition", response_model=APIResponse[Condition])
async def create_condition(
    condition_data: Condition,
    current_user: Person = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create conditions")

    result = await collections["condition"].insert_one(condition_data.dict(by_alias=True))
    created = await collections["condition"].find_one({"_id": result.inserted_id})
    return APIResponse[Condition](code=201, message="Condition created successfully", data=Condition(**created))


@app.post("/surgery", response_model=APIResponse[Surgery])
async def create_surgery(
    surgery_data: Surgery,
    current_user: Person = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create surgeries")

    result = await collections["surgery"].insert_one(surgery_data.dict(by_alias=True))
    created = await collections["surgery"].find_one({"_id": result.inserted_id})
    return APIResponse[Surgery](code=201, message="Surgery created successfully", data=Surgery(**created))


@app.post("/medicine", response_model=APIResponse[Medicine])
async def create_medicine(
    medicine_data: Medicine,
    current_user: Person = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can create medicines")

    result = await collections["medicine"].insert_one(medicine_data.dict(by_alias=True))
    created = await collections["medicine"].find_one({"_id": result.inserted_id})
    return APIResponse[Medicine](code=201, message="Medicine created successfully", data=Medicine(**created))

@app.get("/allergy", response_model=APIResponse[List[Allergy]])
async def list_allergies(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = collections["allergy"].find()
    allergies: List[Allergy] = []
    async for doc in cursor:
        allergies.append(Allergy(**doc))

    return APIResponse[List[Allergy]](
        code=200, message="Allergies retrieved successfully", data=allergies
    )


@app.get("/condition", response_model=APIResponse[List[Condition]])
async def list_conditions(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = collections["condition"].find()
    conditions: List[Condition] = []
    async for doc in cursor:
        conditions.append(Condition(**doc))

    return APIResponse[List[Condition]](
        code=200, message="Conditions retrieved successfully", data=conditions
    )


@app.get("/surgery", response_model=APIResponse[List[Surgery]])
async def list_surgeries(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = collections["surgery"].find()
    surgeries: List[Surgery] = []
    async for doc in cursor:
        surgeries.append(Surgery(**doc))

    return APIResponse[List[Surgery]](
        code=200, message="Surgeries retrieved successfully", data=surgeries
    )


@app.get("/medicine", response_model=APIResponse[List[Medicine]])
async def list_medicines(current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    cursor = collections["medicine"].find()
    medicines: List[Medicine] = []
    async for doc in cursor:
        medicines.append(Medicine(**doc))

    return APIResponse[List[Medicine]](
        code=200, message="Medicines retrieved successfully", data=medicines
    )


@app.get("/allergy/{uuid}", response_model=APIResponse[Allergy])
async def get_allergy(uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    doc = await collections["allergy"].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail="Allergy not found")

    return APIResponse[Allergy](
        code=200, message="Allergy retrieved successfully", data=Allergy(**doc)
    )


@app.get("/condition/{uuid}", response_model=APIResponse[Condition])
async def get_condition(uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    doc = await collections["condition"].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail="Condition not found")

    return APIResponse[Condition](
        code=200, message="Condition retrieved successfully", data=Condition(**doc)
    )


@app.get("/surgery/{uuid}", response_model=APIResponse[Surgery])
async def get_surgery(uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    doc = await collections["surgery"].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail="Surgery not found")

    return APIResponse[Surgery](
        code=200, message="Surgery retrieved successfully", data=Surgery(**doc)
    )


@app.get("/medicine/{uuid}", response_model=APIResponse[Medicine])
async def get_medicine(uuid: str, current_user: Person = Depends(get_current_user)):
    if current_user.role not in [RoleEnum.DOCTOR, RoleEnum.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    doc = await collections["medicine"].find_one({"uuid": uuid})
    if not doc:
        raise HTTPException(status_code=404, detail="Medicine not found")

    return APIResponse[Medicine](
        code=200, message="Medicine retrieved successfully", data=Medicine(**doc)
    )


@app.post(
    "/doctor/prescribe-medicine/{patient_uuid}",
    response_model=APIResponse[Medication]
)
async def prescribe_medication(
    patient_uuid: str,
    medication_data: Medication = Body(...),
    current_user: Person = Depends(get_current_user)
):
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

@app.post(
    "/doctor/record-surgery/{patient_uuid}",
    response_model=APIResponse[PastSurgery]
)
async def record_surgery(
    patient_uuid: str,
    surgery_data: PastSurgery = Body(...),
    current_user: Person = Depends(get_current_user)
):
    if current_user.role != RoleEnum.DOCTOR:
        raise HTTPException(status_code=403, detail="Only doctors can record surgeries")

    patient_doc = await collections["persons"].find_one(
        {"uuid": patient_uuid, "role": RoleEnum.PATIENT}
    )
    if not patient_doc:
        raise HTTPException(status_code=404, detail="Patient not found")
    # Check if surgery exists
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

@app.post(
    "/doctor/diagnose-condition/{patient_uuid}",
    response_model=APIResponse[ConditionDiagnosis]
)
async def diagnose_condition(
    patient_uuid: str,
    diagnosis_data: ConditionDiagnosis = Body(...),
    current_user: Person = Depends(get_current_user)
):
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

@app.post(
    "/doctor/diagnose-allergy/{patient_uuid}",
    response_model=APIResponse[AllergyDiagnosis]
)
async def diagnose_allergy(
    patient_uuid: str,
    diagnosis_data: AllergyDiagnosis = Body(...),
    current_user: Person = Depends(get_current_user)
):
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
