from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import json

from database import SessionLocal, AutomationLog, ClientContext, engine

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="Agency OS API - Full Cash Machine", version="2.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def log_automation(db: Session, task_name: str):
    log = AutomationLog(task_name=task_name, time_saved_minutes=30.0, revenue_generated_euro=15.0)
    db.add(log)
    db.commit()

# --- AI Memory Helper ---
def get_ai_memory(db: Session):
    memory = db.query(ClientContext).first()
    if not memory:
        memory = ClientContext()
        db.add(memory)
        db.commit()
        db.refresh(memory)
    return memory

# ==========================================
# PYDANTIC MODELS
# ==========================================
class EmailRequest(BaseModel): incoming_email: str; intent: str
class LeadRequest(BaseModel): inquiry: str
class FAQRequest(BaseModel): user_question: str; company_context: str
class SummaryRequest(BaseModel): long_text: str
class DataEntryRequest(BaseModel): raw_text: str

class MemoryRequest(BaseModel): brand_voice: str; negative_rules: str

# ==========================================
# DASHBOARD & MEMORY ENDPOINTS
# ==========================================
@app.get("/api/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    logs = db.query(AutomationLog).all()
    return {
        "tasks": len(logs),
        "hours": round(sum([log.time_saved_minutes for log in logs]) / 60, 1),
        "revenue": sum([log.revenue_generated_euro for log in logs])
    }

@app.get("/api/memory")
async def load_memory(db: Session = Depends(get_db)):
    mem = get_ai_memory(db)
    return {"brand_voice": mem.brand_voice, "negative_rules": mem.negative_rules}

@app.post("/api/memory")
async def save_memory(req: MemoryRequest, db: Session = Depends(get_db)):
    mem = get_ai_memory(db)
    mem.brand_voice = req.brand_voice
    mem.negative_rules = req.negative_rules
    db.commit()
    return {"status": "Memory Updated"}

# ==========================================
# THE 5 CASH MACHINES (All Brain-Powered Now!)
# ==========================================
def get_smart_instruction(db: Session, base_instruct: str):
    mem = get_ai_memory(db)
    return f"{base_instruct} CORE RULES: Tone must be {mem.brand_voice}. STRICTLY FOLLOW: {mem.negative_rules}"

@app.post("/api/email-reply")
async def generate_email_reply(request: EmailRequest, db: Session = Depends(get_db)):
    try:
        smart_instruct = get_smart_instruction(db, "Draft a professional B2B email reply. Output in JSON.")
        prompt = f"MODULE: Email Reply\nIncoming: '{request.incoming_email}'\nIntent: '{request.intent}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=types.GenerateContentConfig(system_instruction=smart_instruct, temperature=0.7, response_mime_type="application/json"))
        log_automation(db, "Email Reply")
        return json.loads(response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/lead-qualify")
async def qualify_lead(request: LeadRequest, db: Session = Depends(get_db)):
    try:
        smart_instruct = get_smart_instruction(db, "Classify inquiry as HOT, WARM, or COLD based on urgency and budget. Output in JSON.")
        prompt = f"MODULE: Lead Qualify\nInquiry: '{request.inquiry}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=types.GenerateContentConfig(system_instruction=smart_instruct, temperature=0.5, response_mime_type="application/json"))
        log_automation(db, "Lead Qualify")
        return json.loads(response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/faq-bot")
async def faq_bot(request: FAQRequest, db: Session = Depends(get_db)):
    try:
        smart_instruct = get_smart_instruction(db, "Answer the user's question ONLY using the provided company context. Output in JSON.")
        prompt = f"MODULE: FAQ Bot\nContext: '{request.company_context}'\nQuestion: '{request.user_question}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=types.GenerateContentConfig(system_instruction=smart_instruct, temperature=0.2, response_mime_type="application/json"))
        log_automation(db, "FAQ Bot")
        return json.loads(response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/report-summary")
async def summarize_report(request: SummaryRequest, db: Session = Depends(get_db)):
    try:
        smart_instruct = get_smart_instruction(db, "Summarize the text into an executive summary and 3 actionable bullet points. Output in JSON.")
        prompt = f"MODULE: Summary\nText: '{request.long_text}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=types.GenerateContentConfig(system_instruction=smart_instruct, temperature=0.6, response_mime_type="application/json"))
        log_automation(db, "Report Summary")
        return json.loads(response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data-entry")
async def data_entry(request: DataEntryRequest, db: Session = Depends(get_db)):
    try:
        smart_instruct = get_smart_instruction(db, "Extract key details (vendor name, date, total amount) from the raw text. Output in JSON.")
        prompt = f"MODULE: Data Entry\nRaw: '{request.raw_text}'"
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt, config=types.GenerateContentConfig(system_instruction=smart_instruct, temperature=0.1, response_mime_type="application/json"))
        log_automation(db, "Data Entry")
        return json.loads(response.text)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))