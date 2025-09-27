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
        allowed_extensions = ('.xls', '.xlsx', '.csv')
        for file in [bank_file, ledger_file]:
            if not file.filename.lower().endswith(allowed_extensions):
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} has an unsupported format. Allowed formats: Excel (.xls, .xlsx) and CSV (.csv)"
                )
        
        # Clean up old files
        for old_file in os.listdir(UPLOAD_FOLDER):
            if old_file != '.gitkeep':  # Keep the .gitkeep file
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, old_file))
                except Exception as e:
                    print(f"Warning: Could not remove old file {old_file}: {e}")
        
        # Get file extensions from original files
        bank_ext = os.path.splitext(bank_file.filename)[1].lower()
        ledger_ext = os.path.splitext(ledger_file.filename)[1].lower()
        
        # Use simple names but preserve original extensions
        bank_filepath = os.path.join(UPLOAD_FOLDER, f'bank{bank_ext}')
        ledger_filepath = os.path.join(UPLOAD_FOLDER, f'ledger{ledger_ext}')
        
        # Save both files
        try:
            for file, filepath in [(bank_file, bank_filepath), (ledger_file, ledger_filepath)]:
                content = await file.read()
                with open(filepath, "wb") as f:
                    f.write(content)
                os.chmod(filepath, 0o666)
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")
        
        def read_file(filepath: str, file_type: str = None) -> pd.DataFrame:
            """Read either Excel or CSV file into a pandas DataFrame."""
            try:
                filename = os.path.basename(filepath).lower()
                if filepath.lower().endswith('.csv'):
                    # Default CSV reading parameters
                    params = {
                        'encoding': 'utf-8',
                        'sep': ',',
                        'dtype': str  # Read all columns as string initially
                    }
                    
                    # Special handling for specific file types
                    if 'gstr2b' in filename:
                        params.update({
                            'encoding': 'utf-8',
                            'sep': ',',
                            'skiprows': 0  # Adjust if there are header rows to skip
                        })
                    elif 'tally' in filename:
                        params.update({
                            'encoding': 'utf-8',
                            'sep': ',',
                            'skiprows': 0  # Adjust if there are header rows to skip
                        })
                    
                    try:
                        # First attempt with specified parameters
                        df = pd.read_csv(filepath, **params)
                    except Exception as csv_err:
                        print(f"Initial CSV read failed: {csv_err}")
                        # Fallback to trying different encodings and delimiters
                        encodings = ['utf-8', 'iso-8859-1', 'cp1252']
                        delimiters = [',', ';', '\t']
                        success = False
                        
                        for encoding in encodings:
                            for delimiter in delimiters:
                                try:
                                    df = pd.read_csv(filepath, encoding=encoding, sep=delimiter)
                                    print(f"Successfully read with encoding: {encoding}, delimiter: {delimiter}")
                                    success = True
                                    break
                                except Exception:
                                    continue
                            if success:
                                break
                        
                        if not success:
                            raise ValueError("Could not read CSV file with any common encoding/delimiter combination")
                else:
                    # For Excel files
                    df = pd.read_excel(filepath)
                
                # Clean up column names
                df.columns = df.columns.str.strip().str.lower()
                
                # Print column names for debugging
                print(f"Columns found in {filename}: {list(df.columns)}")
                
                return df
                
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to read file {os.path.basename(filepath)}: {str(e)}\nPlease ensure the file is properly formatted and contains the required columns."
                )

        # Process both files
        try:
            bank_df = read_file(bank_filepath)
            ledger_df = read_file(ledger_filepath)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=400, detail=f"Failed to read files: {str(e)}")
        
        # Column mapping for different file types
        def map_columns(df: pd.DataFrame, filename: str) -> pd.DataFrame:
            filename = filename.lower()
            if 'gstr2b' in filename:
                # Add your GSTR2B column mapping here
                mapping = {
                    'invoice date': 'date',
                    'invoice value': 'amount',
                    'trade/legal name': 'vendor',
                    # Add more mappings as needed
                }
            elif 'tally' in filename:
                # Add your Tally column mapping here
                mapping = {
                    'date': 'date',
                    'amount': 'amount',
                    'party name': 'vendor',
                    # Add more mappings as needed
                }
            else:
                # Default mapping
                mapping = {
                    'date': 'date',
                    'amount': 'amount',
                    'vendor': 'vendor',
                }
            
            # Print available columns for debugging
            print(f"Available columns in {filename}: {list(df.columns)}")
            
            # Rename columns based on mapping
            for old_col, new_col in mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            return df
        
        # Map columns for both dataframes
        bank_df = map_columns(bank_df, bank_file.filename)
        ledger_df = map_columns(ledger_df, ledger_file.filename)
        
        # Validate required columns
        required_columns = {'date', 'amount', 'vendor'}
        for df, name, filename in [
            (bank_df, 'Bank statement', bank_file.filename),
            (ledger_df, 'Ledger file', ledger_file.filename)
        ]:
            missing = required_columns - set(df.columns)
            if missing:
                # Get the actual columns for better error message
                actual_columns = set(df.columns)
                raise HTTPException(
                    status_code=400,
                    detail=f"{name} ({filename}) is missing required columns: {', '.join(missing)}.\n"
                           f"Found columns: {', '.join(actual_columns)}\n"
                           f"Please ensure your file contains the required columns or check the column names."
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