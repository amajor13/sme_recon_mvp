from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))

@app.get("/")
async def read_root():
    return {"message": "SME Reconciliation MVP API", "status": "running"}

@app.post("/upload/")
async def upload_files(
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...)
):
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        bank_path = os.path.join(UPLOAD_FOLDER, f"bank_{bank_file.filename}")
        ledger_path = os.path.join(UPLOAD_FOLDER, f"ledger_{ledger_file.filename}")
        
        with open(bank_path, "wb") as f:
            content = await bank_file.read()
            f.write(content)
            
        with open(ledger_path, "wb") as f:
            content = await ledger_file.read()
            f.write(content)
        
        return {
            "status": "success", 
            "message": "Files uploaded successfully",
            "files": {"bank": bank_file.filename, "ledger": ledger_file.filename}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))