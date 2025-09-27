from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from .reconciliation import reconcile_transactions


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define upload folder with absolute path and ensure it's in a user-writable location
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))

@app.on_event("startup")
async def startup_event():
    """Create upload directory with proper permissions on startup"""
    try:
        # Create directory with full permissions if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, mode=0o777, exist_ok=True)
        # Ensure the directory has the correct permissions even if it already existed
        os.chmod(UPLOAD_FOLDER, 0o777)
    except Exception as e:
        print(f"Warning: Could not set upload directory permissions: {e}")

@app.post("/upload/")
async def upload_files(
    bank_file: UploadFile = File(..., description="Bank statement file"),
    ledger_file: UploadFile = File(..., description="Ledger transactions file")
):
    try:
        # Validate file extensions
        for file in [bank_file, ledger_file]:
            if not file.filename.endswith(('.xls', '.xlsx')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} is not an Excel file. Only .xls and .xlsx are allowed"
                )
        
        # Clean up old files
        for old_file in os.listdir(UPLOAD_FOLDER):
            if old_file != '.gitkeep':  # Keep the .gitkeep file
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, old_file))
                except Exception as e:
                    print(f"Warning: Could not remove old file {old_file}: {e}")
        
        # Use simple names for current files
        bank_filepath = os.path.join(UPLOAD_FOLDER, 'bank.xlsx')
        ledger_filepath = os.path.join(UPLOAD_FOLDER, 'ledger.xlsx')
        
        # Save both files
        try:
            for file, filepath in [(bank_file, bank_filepath), (ledger_file, ledger_filepath)]:
                content = await file.read()
                with open(filepath, "wb") as f:
                    f.write(content)
                os.chmod(filepath, 0o666)
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")
        
        # Process both files
        try:
            bank_df = pd.read_excel(bank_filepath)
            ledger_df = pd.read_excel(ledger_filepath)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read Excel files: {str(e)}")
        
        # Validate required columns
        required_columns = {'date', 'amount', 'vendor'}
        for df, name in [(bank_df, 'Bank statement'), (ledger_df, 'Ledger file')]:
            missing = required_columns - set(df.columns)
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"{name} is missing required columns: {', '.join(missing)}"
                )
        
        reconciled_df, unmatched_bank_df, unmatched_ledger_df = reconcile_transactions(bank_df, ledger_df)
        
        return {
            "reconciled": reconciled_df.to_dict(orient="records"),
            "unmatched_bank": unmatched_bank_df.to_dict(orient="records"),
            "unmatched_ledger": unmatched_ledger_df.to_dict(orient="records")
        }
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=str(e))
        raise e