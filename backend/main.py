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
                # GSTR2B specific column mapping
                mapping = {
                    'invoice date': 'date',  # Changed from 'date' to 'invoice date'
                    'total invoice value': 'amount',
                    'supplier gstin': 'vendor',  # Using GSTIN as vendor identifier
                    'invoice no': 'reference'
                }
                
                # Print the columns before and after mapping for debugging
                print(f"Before mapping - Available columns: {list(df.columns)}")
                
                # If we need to perform any data transformations
                if 'total invoice value' in df.columns:
                    # Convert amount to numeric, removing any currency symbols and commas
                    df['total invoice value'] = pd.to_numeric(
                        df['total invoice value'].str.replace('₹', '').str.replace(',', ''),
                        errors='coerce'
                    )
                
                # Print the mapping being applied
                print(f"Applying mapping: {mapping}")
            elif 'tally' in filename:
                # Print original columns and their types for debugging
                print(f"Original Tally file columns and types:\n{df.dtypes}")
                
                # For Tally files, we need to handle the case where there might be multiple amount columns
                if 'amount' in df.columns and pd.api.types.is_numeric_dtype(df['amount']):
                    # If 'amount' is already numeric, we'll use it directly
                    print("Using existing numeric 'amount' column")
                else:
                    # If we have both amount and tax amount, we might need to calculate the total
                    print("Calculating total amount from available columns")
                    amount_cols = [col for col in df.columns if 'amount' in col.lower()]
                    print(f"Found amount columns: {amount_cols}")
                    
                    # Try to convert each amount column to numeric
                    for col in amount_cols:
                        try:
                            df[col] = clean_numeric_values(df[col])
                        except Exception as e:
                            print(f"Warning: Could not convert column {col} to numeric: {e}")
                    
                    # Use the first numeric amount column we find
                    for col in amount_cols:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            print(f"Using column '{col}' as amount")
                            df['amount'] = df[col]
                            break
                
                # Tally specific column mapping
                mapping = {
                    'date': 'date',
                    'supplier gstin': 'vendor',  # Using GSTIN as vendor identifier
                    'invoice no': 'reference'
                }
                
                print(f"Processing Tally file columns after amount handling: {list(df.columns)}")
                print(f"Column types after preprocessing:\n{df.dtypes}")
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
            print(f"\nProcessing file: {filename}")
            print(f"Original columns: {list(df.columns)}")
            
            for old_col, new_col in mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
                    print(f"Mapped '{old_col}' to '{new_col}'")
                else:
                    print(f"Warning: Expected column '{old_col}' not found in file")
            
            print(f"Final columns after mapping: {list(df.columns)}")
            
            return df
        
        # Map columns for both dataframes
        bank_df = map_columns(bank_df, bank_file.filename)
        ledger_df = map_columns(ledger_df, ledger_file.filename)
        
        # Validate and prepare dataframes
        def validate_and_prepare_df(df: pd.DataFrame, name: str, filename: str) -> pd.DataFrame:
            """Validate and prepare dataframe for reconciliation."""
            required_columns = {'date', 'amount', 'vendor'}
            
            # Check for required columns after mapping
            missing = required_columns - set(df.columns)
            if missing:
                # Get the actual columns for error message
                actual_columns = set(df.columns)
                
                # Provide specific guidance based on file type
                if 'gstr2b' in filename.lower():
                    hint = ("\nGSTR2B Guidance:\n"
                           "- 'date' should come from 'invoice date' column\n"
                           "- 'amount' should come from 'total invoice value' column\n"
                           "- 'vendor' should come from 'supplier gstin' column\n"
                           f"\nCurrent columns found: {', '.join(sorted(actual_columns))}")
                elif 'tally' in filename.lower():
                    hint = ("\nTally File Guidance:\n"
                           "- 'date' should come from 'date' column\n"
                           "- 'amount' should come from 'total amount' column\n"
                           "- 'vendor' should come from 'supplier gstin' column\n"
                           f"\nCurrent columns found: {', '.join(sorted(actual_columns))}\n"
                           "Note: Using GSTIN as vendor identifier for consistency with GSTR2B")
                else:
                    hint = "\nRequired column format: 'date', 'amount', 'vendor'"
                
                raise HTTPException(
                    status_code=400,
                    detail=f"{name} ({filename}) is missing required columns: {', '.join(missing)}.\n"
                           f"Found columns: {', '.join(sorted(actual_columns))}\n"
                           f"{hint}"
                )
            
            def clean_numeric_values(series):
                """Clean and convert a series to numeric values, handling various formats."""
                if pd.api.types.is_numeric_dtype(series):
                    return series
                
                try:
                    # First, try direct conversion if possible
                    return pd.to_numeric(series, errors='raise')
                except (TypeError, ValueError):
                    # If direct conversion fails, try cleaning the data
                    if isinstance(series, pd.Series):
                        # Convert to string first to handle all cases
                        cleaned = series.astype(str)
                    else:
                        # Handle case where the column might be a different type
                        cleaned = pd.Series(series).astype(str)
                    
                    # Print sample values for debugging
                    print(f"Sample values before cleaning: {cleaned.head()}")
                    
                    # Remove common currency symbols and formatting
                    currency_chars = ['₹', '$', '€', '£', ',']
                    for char in currency_chars:
                        cleaned = cleaned.str.replace(char, '')
                    
                    # Handle parentheses for negative numbers: (100) -> -100
                    cleaned = cleaned.str.strip('()').str.strip()
                    cleaned = cleaned.apply(lambda x: f"-{x.strip('()')}" if '(' in str(x) and ')' in str(x) else x)
                    
                    # Remove any remaining non-numeric characters except decimal point and minus sign
                    cleaned = cleaned.str.replace(r'[^\d.-]', '', regex=True)
                    
                    # Print sample values after cleaning
                    print(f"Sample values after cleaning: {cleaned.head()}")
                    
                    # Convert to numeric, setting errors='coerce' to handle invalid values
                    numeric_values = pd.to_numeric(cleaned, errors='coerce')
                    
                    # Print information about any values that couldn't be converted
                    nan_mask = numeric_values.isna()
                    if nan_mask.any():
                        print(f"Warning: Could not convert {nan_mask.sum()} values to numeric")
                        print(f"Problem values: {series[nan_mask].head()}")
                    
                    return numeric_values

            def clean_date_values(series):
                """Clean and convert a series to datetime, handling various formats."""
                if pd.api.types.is_datetime64_any_dtype(series):
                    return series.dt.date
                
                try:
                    # Try parsing with various formats
                    return pd.to_datetime(series, infer_datetime_format=True).dt.date
                except Exception as e:
                    print(f"Warning: Date parsing failed with error: {str(e)}")
                    # If that fails, try manual format detection
                    sample = str(series.iloc[0]) if not series.empty else ""
                    if '/' in sample:
                        return pd.to_datetime(series, format='%d/%m/%Y').dt.date
                    elif '-' in sample:
                        return pd.to_datetime(series, format='%Y-%m-%d').dt.date
                    else:
                        raise ValueError(f"Unrecognized date format. Sample date: {sample}")

            def clean_string_values(series):
                """Clean string values by removing extra spaces and standardizing case."""
                return pd.Series(series).astype(str).str.strip().str.upper()

            try:
                # Clean date values
                if 'date' in df.columns:
                    try:
                        df['date'] = clean_date_values(df['date'])
                    except Exception as e:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Error processing dates in {name}: {str(e)}\n"
                                   "Please ensure dates are in a standard format (e.g., YYYY-MM-DD or DD/MM/YYYY)"
                        )

                # Clean amount values
                if 'amount' in df.columns:
                    try:
                        df['amount'] = clean_numeric_values(df['amount'])
                        # Check for any NaN values after conversion
                        nan_count = df['amount'].isna().sum()
                        if nan_count > 0:
                            print(f"Warning: Found {nan_count} invalid amount values in {name}")
                    except Exception as e:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Error processing amounts in {name}: {str(e)}\n"
                                   "Please ensure amounts are valid numeric values"
                        )

                # Clean vendor values
                if 'vendor' in df.columns:
                    df['vendor'] = clean_string_values(df['vendor'])
                    # Basic GSTIN validation (if applicable)
                    if df['vendor'].str.len().eq(15).any():  # Check if we're dealing with GSTINs
                        invalid_gstin = df[df['vendor'].str.len() != 15]['vendor'].tolist()
                        if invalid_gstin:
                            print(f"Warning: Found potentially invalid GSTINs in {name}: {invalid_gstin}")

                # Add source identifier
                df['source'] = 'gstr2b' if 'gstr2b' in filename.lower() else 'tally'

            except Exception as e:
                # Log the error for debugging
                print(f"Error processing {name}: {str(e)}")
                print(f"Column types: {df.dtypes}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error processing {name}: {str(e)}\n"
                           f"Column types: {df.dtypes}"
                )
            
            return df
        
        # Validate and prepare both dataframes
        bank_df = validate_and_prepare_df(bank_df, "Bank statement", bank_file.filename)
        ledger_df = validate_and_prepare_df(ledger_df, "Ledger file", ledger_file.filename)
        
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