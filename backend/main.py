from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import re
from .reconciliation import reconcile_transactions

def clean_numeric_values(series):
    """
    Clean and convert a pandas series to numeric values, handling various formats:
    - Remove currency symbols (₹, $, etc.)
    - Remove commas from numbers (1,234.56 -> 1234.56)
    - Remove leading/trailing whitespace
    - Convert parentheses to negative numbers ((100) -> -100)
    - Handle percentage values
    - Handle text representation of numbers ('five thousand' -> 5000)
    
    Args:
        series: pandas Series containing the values to clean
    
    Returns:
        pandas Series with cleaned numeric values
    """
    def clean_single_value(val):
        if pd.isna(val):
            return pd.NA
        
        # Convert to string for processing
        val = str(val).strip()
        
        # Remove currency symbols and other common prefixes/suffixes
        val = re.sub(r'[₹$€£¥]', '', val)
        
        # Remove commas
        val = val.replace(',', '')
        
        # Handle parentheses for negative numbers
        if val.startswith('(') and val.endswith(')'):
            val = '-' + val[1:-1]
        
        # Handle percentage values
        if '%' in val:
            val = val.replace('%', '')
            try:
                return float(val) / 100
            except ValueError:
                return pd.NA
        
        # Handle text numbers (basic implementation)
        text_numbers = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'hundred': 100, 'thousand': 1000, 'lakh': 100000,
            'lakhs': 100000, 'crore': 10000000, 'crores': 10000000
        }
        
        if val.lower() in text_numbers:
            return text_numbers[val.lower()]
        
        # Try to convert to float
        try:
            return float(val)
        except ValueError:
            return pd.NA
    
    return series.apply(clean_single_value)


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
            # Print original columns for debugging
            print(f"\nOriginal columns in file {filename}:")
            print(df.columns.tolist())
            
            # Check if this is GSTR2B data by looking for its specific columns
            if any(col in df.columns for col in ['taxable value', 'igst', 'cgst', 'sgst', 'total invoice value']):
                print("Detected GSTR2B file format")
                mapping = {
                    'invoice date': 'date',
                    'total invoice value': 'amount',
                    'supplier gstin': 'vendor',
                    'invoice no': 'reference'
                }
                
                # Print the columns before and after mapping for debugging
                print(f"Before mapping - Available columns: {list(df.columns)}")
                
                # Convert amount to numeric
                if 'total invoice value' in df.columns:
                    print("Converting Total Invoice Value to numeric")
                    df['total invoice value'] = pd.to_numeric(df['total invoice value'], errors='coerce')
                    print(f"Sample amounts after conversion:\n{df['total invoice value'].head()}")
                
                print(f"Applying mapping: {mapping}")
            
            # Check if this is Tally data by looking for its specific columns
            elif any(col in df.columns for col in ['tax amount', 'total amount', 'type']):
                print("Detected Tally file format")
                print(f"\nOriginal columns and types:")
                print(df.dtypes)
                
                # Step 1: Convert amount columns to numeric first
                amount_cols = ['amount', 'tax amount', 'total amount']
                for col in amount_cols:
                    if col in df.columns:
                        print(f"\nProcessing {col} column:")
                        print(f"Original values:\n{df[col].head()}")
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                            print(f"Converted values:\n{df[col].head()}")
                        except Exception as e:
                            print(f"Warning: Error converting {col}: {e}")
                
                # Step 2: Calculate total amount if needed
                if 'total amount' not in df.columns and 'amount' in df.columns and 'tax amount' in df.columns:
                    print("\nCalculating total amount from components")
                    df['calculated_total'] = df['amount'].fillna(0) + df['tax amount'].fillna(0)
                    print("Sample calculated totals:")
                    print(df[['amount', 'tax amount', 'calculated_total']].head())
                
                # Step 3: Determine which amount column to use for reconciliation
                print("\nAnalyzing available amount columns:")
                
                amount_columns = {
                    col: df[col].notna().sum() 
                    for col in df.columns 
                    if any(name in col.lower() for name in ['amount', 'value', 'total'])
                }
                
                print("Found potential amount columns:")
                for col, count in amount_columns.items():
                    print(f"  {col}: {count} non-null values")
                
                # Priority order for amount columns
                if 'total amount' in df.columns:
                    print("\nUsing 'total amount' column (highest priority)")
                    amount_col = 'total amount'
                elif 'calculated_total' in df.columns:
                    print("\nUsing calculated total (next priority)")
                    amount_col = 'calculated_total'
                elif 'amount' in df.columns:
                    print("\nUsing base 'amount' column")
                    amount_col = 'amount'
                else:
                    # Try to find any column that might contain amount data
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                    amount_like = [col for col in numeric_cols if any(name in col.lower() for name in ['amount', 'value', 'total'])]
                    
                    if amount_like:
                        amount_col = amount_like[0]
                        print(f"\nUsing best guess amount column: {amount_col}")
                    else:
                        raise ValueError(
                            "Could not determine amount column. Available columns: " +
                            ", ".join(df.columns.tolist()) +
                            "\nPlease ensure your file has a column containing transaction amounts."
                        )
                
                # Step 4: Create mapping
                mapping = {
                    'date': 'date',
                    amount_col: 'amount',  # Map the selected amount column
                    'supplier gstin': 'vendor',
                    'invoice no': 'reference',
                    'type': 'type'
                }
                
                print("\nSelected mapping:")
                print(mapping)
                print("\nColumn to be used for amount:", amount_col)
                print("Sample values from selected amount column:")
                print(df[amount_col].head())
                
            else:
                print(f"Could not determine file type. Available columns: {list(df.columns)}")
                # Default mapping assuming basic columns are present
                mapping = {
                    'date': 'date',
                    'amount': 'amount',
                    'vendor': 'vendor'
                }
            
            # Print available columns for debugging
            print(f"Available columns in {filename}: {list(df.columns)}")
            
            # Rename columns based on mapping
            print(f"\nProcessing file: {filename}")
            print(f"Original columns before mapping: {list(df.columns)}")
            
            # Create a copy of the DataFrame with only the columns we want to map
            mapped_df = pd.DataFrame()
            
            # Track which columns were successfully mapped
            mapped_columns = []
            missing_columns = []
            
            for old_col, new_col in mapping.items():
                if old_col in df.columns:
                    mapped_df[new_col] = df[old_col]
                    mapped_columns.append(f"{old_col} -> {new_col}")
                else:
                    missing_columns.append(old_col)
            
            print(f"\nMapping summary:")
            if mapped_columns:
                print("Successfully mapped columns:")
                for mapping in mapped_columns:
                    print(f"  {mapping}")
            
            if missing_columns:
                print("\nMissing columns:")
                for col in missing_columns:
                    print(f"  {col}")
            
            if mapped_df.empty or not all(col in mapped_df.columns for col in ['date', 'amount', 'vendor']):
                required = ['date', 'amount', 'vendor']
                missing = [col for col in required if col not in mapped_df.columns]
                available = df.columns.tolist()
                raise ValueError(
                    f"Failed to map all required columns. Missing: {missing}\n"
                    f"Available columns in original file: {available}\n"
                    "Please ensure your file contains the necessary data columns."
                )
            
            print(f"\nFinal columns after mapping: {list(mapped_df.columns)}")
            print("\nFirst few rows of mapped data:")
            print(mapped_df.head())
            
            return mapped_df
        
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
                
                # Print sample values for debugging
                print("\nCleaning numeric values")
                print("Original values (first 5):")
                print(series.head())
                
                # Convert to string first to handle all cases
                cleaned = pd.Series(series).astype(str).str.strip()
                
                # Handle special characters and formatting
                for char in ['₹', '$', '€', '£', ',']:
                    cleaned = cleaned.str.replace(char, '', regex=False)
                
                # Handle parentheses for negative numbers: (100) -> -100
                cleaned = cleaned.apply(lambda x: f"-{x.strip('()')}" if '(' in str(x) and ')' in str(x) else x)
                
                # Remove any remaining non-numeric characters except decimal point and minus sign
                cleaned = cleaned.str.replace(r'[^\d.-]', '', regex=True)
                
                print("\nCleaned values (first 5):")
                print(cleaned.head())
                
                # Convert to numeric, handling invalid values
                try:
                    numeric = pd.to_numeric(cleaned, errors='coerce')
                    print("\nConverted to numeric (first 5):")
                    print(numeric.head())
                    
                    # Check for any NaN values
                    nan_mask = numeric.isna()
                    if nan_mask.any():
                        print(f"\nWarning: Could not convert {nan_mask.sum()} values to numeric")
                        print("Problem values:")
                        for orig, clean in zip(series[nan_mask].head(), cleaned[nan_mask].head()):
                            print(f"Original: '{orig}' -> Cleaned: '{clean}'")
                    
                    return numeric
                except Exception as e:
                    print(f"\nError converting to numeric: {str(e)}")
                    raise

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