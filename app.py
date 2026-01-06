import os
import cv2
import joblib
import tempfile
import json  
import hashlib
import tensorflow as tf
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import database

# --- PIPELINE IMPORTS ---
from Pipelines.preprocess import preprocess_document
from Pipelines.CNN_predict import cnn_predict
from Pipelines.ocr_extractor import run_ocr
from Pipelines.extract_Aadhaar import extract_fields
from Pipelines.rule_validator import rule_validation
from Pipelines.qr_validator import validate_qr
from Pipelines.consistency_checker import build_consistency
from Pipelines.forensic_analyzer import analyze_image_forensics
from Pipelines.fraud_assement import assess_fraud
from Pipelines.model_json import predict_fraud
from Pipelines.final_decision import make_final_decision
from Pipelines.face_matcher import verify_face # <--- NEW IMPORT

app = FastAPI(title="RakshaUID Identity Defense")

# --- SECURITY CONFIG ---
app.add_middleware(
    SessionMiddleware, 
    secret_key="raksha-super-secret-key", 
    max_age=1209600  
)

# --- USER DATABASE SETUP ---
DB_FILE = "users_db.json"

def load_users():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save_users(db_data):
    with open(DB_FILE, "w") as f: json.dump(db_data, f, indent=4)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- CONFIGURATION ---
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- LOAD MODELS ---
try:
    cnn_model = tf.keras.models.load_model("Models/aadhaar_classifier_final.h5")
    fraud_model = joblib.load("Models/RandomForest_model.pkl")
    print("Models Loaded Successfully.")
except Exception as e:
    print(f"Warning: Models not found ({e}).")
    cnn_model = None
    fraud_model = None

# ==========================================================
#  AUTH ROUTES
# ==========================================================
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.session.get("user"): return RedirectResponse(url="/verify-page")
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")

@app.post("/api/login")
async def api_login(request: Request, data: dict = Body(...)):
    email = data.get("email")
    password = data.get("password")
    users_db = load_users()
    user = users_db.get(email)
    if not user or user["password"] != hash_password(password):
        return JSONResponse(content={"success": False, "message": "Invalid credentials."}, status_code=401)
    request.session["user"] = email
    return JSONResponse(content={"success": True, "redirect_url": "/verify-page"})

@app.post("/api/signup")
async def api_signup(data: dict = Body(...)):
    email = data.get("email")
    password = data.get("password")
    users_db = load_users()
    if email in users_db:
        return JSONResponse(content={"success": False, "message": "Account exists."}, status_code=409)
    users_db[email] = {"password": hash_password(password), "created_at": "today"}
    save_users(users_db)
    return JSONResponse(content={"success": True, "message": "Registered!", "redirect_url": "/login"})

# ==========================================================
#  APP ROUTES
# ==========================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/verify-page", response_class=HTMLResponse)
async def verify_page(request: Request):
    if not request.session.get("user"): return RedirectResponse(url="/login")
    return templates.TemplateResponse("verify.html", {"request": request})

# ==========================================================
#  STEP 1: ANALYZE CARD (UPDATED TO RETURN FILENAME)
# ==========================================================
@app.post("/api/analyze-card")
async def analyze_card_step(file: UploadFile = File(...)):
    if cnn_model is None:
        return JSONResponse({"is_aadhaar": False, "message": "Models not loaded."})

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        clean_path = file_path.replace(".jpg", "_clean.jpg")
        processed_data = preprocess_document(file_path)
        clean_img = processed_data["processed_image"]
        cv2.imwrite(clean_path, clean_img)
        target_path = clean_path
    except:
        target_path = file_path

    cnn_out = cnn_predict(cnn_model, target_path)
    label = cnn_out.get("project_label", "UNKNOWN")

    if label == "NON_AADHAAR":
        return JSONResponse(content={
            "is_aadhaar": False,
            "message": "This document does not appear to be an Aadhaar card.",
            "details": cnn_out
        })
    else:
        ocr_result = run_ocr(target_path)
        extracted_fields = extract_fields(ocr_result)

        return JSONResponse(content={
            "is_aadhaar": True,
            "message": "Aadhaar Detected. Proceeding to Face Verification.",
            "aadhaar_path": file.filename, 
            "extracted_data": extracted_fields,
            "details": cnn_out
        })

# ==========================================================
#  STEP 2: FACE VERIFICATION (NEW ENDPOINT)
# ==========================================================
@app.post("/api/verify-face")
async def verify_face_step(
    person_image: UploadFile = File(...), 
    aadhaar_filename: str = Body(...)
):
    # 1. Save Person Image
    temp_person = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_person.write(await person_image.read())
    person_path = temp_person.name
    temp_person.close()

    # 2. Get Aadhaar Path
    aadhaar_path = os.path.join(UPLOAD_DIR, aadhaar_filename)

    # 3. Verify using your provided logic
    result = verify_face(aadhaar_path, person_path)

    # 4. Cleanup Person Image
    os.remove(person_path)

    if result["match"]:
        return JSONResponse(content={"success": True, "message": "Biometrics Matched!", "score": result["confidence"]})
    else:
        return JSONResponse(content={"success": False, "message": f"Face Mismatch (Score: {result['confidence']}%)"})

# ==========================================================
#  DATABASE LOOKUP
# ==========================================================
@app.post("/api/lookup")
async def lookup_aadhaar(data: dict = Body(...)):
    uid = data.get('aadhaar_number')
    if not uid or len(uid) != 12:
        return JSONResponse(content={"success": False, "message": "Invalid format."})

    user = database.get_user_by_aadhaar(uid)
    if user:
        return JSONResponse(content={"success": True, "found": True, "data": user})
    else:
        return JSONResponse(content={"success": True, "found": False, "message": "Not verified yet."})

# ==========================================================
#  STEP 3: FULL VERIFICATION (QR + FRAUD)
# ==========================================================
@app.post("/api/verify-full")
async def verify_full_process(
    file: UploadFile = File(...), 
    qr_file: Optional[UploadFile] = File(None)
):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.write(await file.read())
    tmp.close()
    raw_image_path = tmp.name
    image_path = raw_image_path 

    try:
        clean_path = raw_image_path.replace(".jpg", "_clean.jpg")
        processed_data = preprocess_document(raw_image_path)
        cv2.imwrite(clean_path, processed_data["processed_image"])
        image_path = clean_path 
    except: pass

    cnn_out = cnn_predict(cnn_model, image_path)
    ocr_result = run_ocr(image_path)
    aadhaar_fields = extract_fields(ocr_result)
    qr_result = validate_qr(image_path)

    if qr_result["status"] != "DECODED" and qr_file is not None:
        tmp_qr = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        tmp_qr.write(await qr_file.read())
        tmp_qr.close()
        qr_path = tmp_qr.name
        
        backup_qr = validate_qr(qr_path)
        if backup_qr["status"] == "DECODED": qr_result = backup_qr
        os.remove(qr_path)

    validation = rule_validation(aadhaar_fields, qr_result["status"])
    consistency = build_consistency(aadhaar_fields, qr_result)
    forensics = analyze_image_forensics(raw_image_path)
    fraud_rule = assess_fraud(validation, qr_result, consistency, forensics)

    record_for_ml = {
        "validation": validation, "consistency": consistency,
        "image_forensics": forensics, "ocr_extracted": aadhaar_fields, "qr": qr_result
    }
    fraud_ml = predict_fraud(fraud_model, record_for_ml)
    final_decision = make_final_decision(cnn_out, fraud_ml, fraud_rule)

    if final_decision.get("final_decision") == "ACCEPTED" and aadhaar_fields.get("aadhaar_number"):
        prob = fraud_ml.get("fraud_probability", 0)
        db_data = {
            "aadhaar_number": aadhaar_fields.get("aadhaar_number", "").replace(" ", ""),
            "name": aadhaar_fields.get("name"),
            "dob": aadhaar_fields.get("dob"),
            "gender": aadhaar_fields.get("gender"),
            "status": "ACCEPTED",
            "confidence": (1 - prob) * 100
        }
        database.save_verified_user(db_data)

    return {
        "cnn_result": cnn_out, 
        "ocr_extracted": aadhaar_fields,
        "qr": qr_result, 
        "final_decision": final_decision, 
        "fraud_ml": fraud_ml
    }