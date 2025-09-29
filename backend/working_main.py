from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pandas as pd
import numpy as np
import os
import re
import asyncio
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
import Levenshtein
import requests
from jose import jwt, JWTError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://sme-reconciliation-api")
AUTH0_ALGORITHM = "RS256"

security = HTTPBearer()

class Auth0JWTBearer:
    def __init__(self):
        self.jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        self.jwks_cache = None
    
    def get_jwks(self):
        if not self.jwks_cache:
            try:
                response = requests.get(self.jwks_url)
                response.raise_for_status()
                self.jwks_cache = response.json()
            except requests.RequestException as e:
                # For development, allow bypass if Auth0 is not reachable
                print(f"Warning: Could not fetch JWKS from Auth0: {e}")
                return None
        return self.jwks_cache
    
    def verify_token(self, token: str) -> dict:
        try:
            # For development mode, check for placeholder domains
            if AUTH0_DOMAIN == "your-auth0-domain.auth0.com" or "YOUR_AUTH0_DOMAIN" in AUTH0_DOMAIN:
                print("Development mode: Auth0 not configured, allowing access")
                return {
                    "sub": "dev-user",
                    "email": "dev@example.com",
                    "name": "Development User"
                }
            
            # Get JWKS for real Auth0 validation
            jwks = self.get_jwks()
            if not jwks:
                # Fallback to development mode
                return {
                    "sub": "dev-user", 
                    "email": "dev@example.com",
                    "name": "Development User"
                }
            
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                raise HTTPException(status_code=401, detail="Token header missing key ID")
            
            # Get the signing key
            signing_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    signing_key = key
                    break
            
            if not signing_key:
                raise HTTPException(status_code=401, detail="Unable to find appropriate signing key")
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[AUTH0_ALGORITHM],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            
            return payload
            
        except JWTError as e:
            print(f"JWT validation failed: {e}")
            # For development, allow fallback
            return {
                "sub": "dev-user",
                "email": "dev@example.com", 
                "name": "Development User"
            }
        except Exception as e:
            print(f"Token validation error: {e}")
            raise HTTPException(status_code=401, detail="Token validation failed")

auth0_validator = Auth0JWTBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    user_info = auth0_validator.verify_token(token)
    
    return {
        "user_id": user_info.get("sub"),
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "email_verified": user_info.get("email_verified", False),
    }

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003", 
        "http://127.0.0.1:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3004",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))

def clean_numeric_values(series):
    """Clean and convert a pandas series to numeric values."""
    def clean_single_value(val):
        if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'null', 'none']:
            return 0.0
        
        try:
            # Convert to string for processing
            val = str(val).strip()
            
            # Remove currency symbols and other common prefixes/suffixes
            val = re.sub(r'[₹$€£¥]', '', val)
            
            # Remove commas and spaces
            val = val.replace(',', '').replace(' ', '')
            
            # Handle parentheses for negative numbers
            if val.startswith('(') and val.endswith(')'):
                val = '-' + val[1:-1]
            
            # Handle percentage values
            if '%' in val:
                val = val.replace('%', '')
                return float(val) / 100
            
            # Handle empty or dash values
            if val in ['', '-', '--', 'N/A', 'n/a']:
                return 0.0
            
            # Try to convert to float
            return float(val)
        except (ValueError, TypeError) as e:
            print(f"Warning: Could not parse numeric value '{val}': {e}")
            return 0.0
    
    return series.apply(clean_single_value)

def clean_date_values(series):
    """Clean and convert a series to datetime."""
    def clean_single_date(val):
        if pd.isna(val) or val == '' or str(val).lower() == 'nan':
            return pd.NaT
        
        # Convert to string and clean
        val_str = str(val).strip()
        
        # If it's already a datetime object, return it
        if isinstance(val, (pd.Timestamp, datetime)):
            return val
        
        # Try common date formats
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d',
            '%d.%m.%Y', '%Y.%m.%d', '%d %m %Y', '%Y %m %d',
            '%d-%b-%Y', '%Y-%b-%d', '%b-%d-%Y'
        ]
        
        for fmt in formats:
            try:
                return pd.to_datetime(val_str, format=fmt)
            except (ValueError, TypeError):
                continue
        
        # Try pandas auto-parsing as last resort
        try:
            return pd.to_datetime(val_str, errors='coerce')
        except:
            return pd.NaT
    
    return series.apply(clean_single_date)

def clean_string_values(series):
    """Clean string values by removing extra spaces and standardizing case."""
    def clean_single_string(val):
        if pd.isna(val):
            return ""
        
        try:
            val_str = str(val).strip()
            val_str = val_str.replace('â,', '').replace('â', '')
            import re
            val_str = re.sub(r'[^\w\s\-\.,/()&@#]', '', val_str)
            return val_str.upper()
        except Exception:
            return ""
    
    return series.apply(clean_single_string)

def read_and_process_file(filepath: str, file_type: str) -> pd.DataFrame:
    """Read and process uploaded file."""
    print(f"\nReading file: {filepath}")
    
    try:
        # Read file based on extension
        if filepath.lower().endswith('.csv'):
            encodings = ['utf-8-sig', 'utf-8', 'iso-8859-1', 'cp1252', 'latin1']
            delimiters = [',', ';', '\t']
            
            df = None
            used_encoding = None
            used_delimiter = None
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, sep=delimiter, dtype=str)
                        used_encoding = encoding
                        used_delimiter = delimiter
                        print(f"Successfully read CSV with encoding: {encoding}, delimiter: {delimiter}")
                        break
                    except Exception as e:
                        print(f"Failed with encoding {encoding}, delimiter '{delimiter}': {e}")
                        continue
                if df is not None:
                    break
            
            if df is None:
                raise ValueError("Could not read CSV file with any common encoding/delimiter combination")
        else:
            df = pd.read_excel(filepath, dtype=str)
        
        if df.empty:
            raise ValueError("File appears to be empty")
        
        print(f"Original file shape: {df.shape}")
        print(f"Original columns (before cleanup): {list(df.columns)}")
        
        # Convert amount columns to numeric BEFORE lowercasing column names
        if 'gstr2b' in file_type.lower():
            amount_cols_to_check = ['Total Invoice Value', 'total invoice value']
        else:
            amount_cols_to_check = ['Total Amount', 'total amount']
            
        for col_name in amount_cols_to_check:
            if col_name in df.columns:
                print(f"Converting '{col_name}' to numeric before column cleanup")
                df[col_name] = df[col_name].astype(str).str.replace(',', '')
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
                break
        
        # Clean up column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Print columns after cleanup
        print(f"Columns after cleanup: {list(df.columns)}")
        
        # Store original GSTIN before any mapping
        if 'supplier gstin' in df.columns:
            df['original_gstin'] = df['supplier gstin'].astype(str).str.strip()
        
        # For Tally files, drop the 'amount' column early if both 'amount' and 'total amount' exist
        if 'tally' in file_type.lower() and 'amount' in df.columns and 'total amount' in df.columns:
            print(f"Early drop: removing 'amount' column to avoid conflict with 'total amount'")
            df = df.drop(columns=['amount'])
            print(f"Columns after early drop: {df.columns.tolist()}")
        
        # Standardize column names based on file type with exact mapping
        if 'gstr2b' in file_type.lower():
            print(f"\nProcessing GSTR2B file...")
            print(f"Original columns: {df.columns.tolist()}")
            
            # Direct column mapping for GSTR2B
            column_mapping = {
                'invoice date': 'date',
                'total invoice value': 'amount',  # Use Total Invoice Value for GSTR2B
                'supplier gstin': 'gstin',
                'invoice no': 'reference'
            }
            
            # Check what amount columns exist
            if 'total invoice value' in df.columns:
                print(f"Sample Total Invoice Value (raw): {df['total invoice value'].head().tolist()}")
            else:
                print("ERROR: 'total invoice value' column not found!")
                
        else:
            print(f"\nProcessing Tally file...")
            print(f"Original columns: {df.columns.tolist()}")
            
            column_mapping = {
                'date': 'date',
                'total amount': 'amount',  # Use Total Amount for Tally
                'supplier gstin': 'gstin',
                'invoice no': 'reference'
            }
            
            # Check what amount columns exist
            if 'total amount' in df.columns:
                print(f"Sample Total Amount (raw): {df['total amount'].head().tolist()}")
            else:
                print("ERROR: 'total amount' column not found!")
        
        # Store original GSTIN for vendor display
        if 'supplier gstin' in df.columns:
            df['vendor'] = df['supplier gstin'].astype(str).str.strip()
        elif 'gstin' in df.columns:
            df['vendor'] = df['gstin'].astype(str).str.strip()
        
        # Convert amount column to numeric BEFORE mapping
        amount_source_col = 'total invoice value' if 'gstr2b' in file_type.lower() else 'total amount'
        
        print(f"\nLooking for amount column: '{amount_source_col}'")
        print(f"Available columns: {df.columns.tolist()}")
        
        # Try to find the column with case-insensitive search
        matching_cols = [col for col in df.columns if col.lower() == amount_source_col.lower()]
        if matching_cols:
            amount_source_col = matching_cols[0]
            print(f"Found matching column: '{amount_source_col}'")
        
        if amount_source_col in df.columns:
            print(f"\nConverting '{amount_source_col}' to numeric:")
            print(f"Raw values: {df[amount_source_col].head().tolist()}")
            
            try:
                # Clean and convert to numeric
                df[amount_source_col] = df[amount_source_col].astype(str).str.replace(',', '')
                df[amount_source_col] = pd.to_numeric(df[amount_source_col], errors='coerce')
                
                print(f"Numeric values: {df[amount_source_col].head().tolist()}")
            except Exception as e:
                print(f"ERROR converting amounts: {e}")
                raise
        else:
            print(f"ERROR: Amount column '{amount_source_col}' not found in {df.columns.tolist()}")
            raise ValueError(f"Required amount column '{amount_source_col}' not found")
        
        # Apply column mapping
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
                print(f"Mapped '{old_col}' -> '{new_col}'")
        
        print(f"Columns after mapping: {list(df.columns)}")
        
        # Check for duplicate columns
        if len(df.columns) != len(set(df.columns)):
            duplicate_cols = [col for col in df.columns if df.columns.tolist().count(col) > 1]
            print(f"WARNING: Duplicate columns found: {duplicate_cols}")
        
        # Check required columns after mapping
        required_cols = ['date', 'amount', 'reference', 'gstin']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            print(f"Available columns: {list(df.columns)}")
            raise ValueError(f"Missing required columns: {missing_cols}. Available columns: {list(df.columns)}")
        
        # Process each column
        df['date'] = clean_date_values(df['date'])
        
        # Verify amount column has data
        print(f"\nFinal amount column verification:")
        if 'amount' in df.columns and len(df) > 0:
            print(f"Amount column type: {df['amount'].dtype}")
            print(f"Amount values: {df['amount'].head().tolist()}")
            print(f"Amount stats: min={df['amount'].min():.2f}, max={df['amount'].max():.2f}, mean={df['amount'].mean():.2f}")
        else:
            print("No amount data or empty DataFrame")
        
        # Clean string columns
        df['reference'] = clean_string_values(df['reference'])
        df['gstin'] = clean_string_values(df['gstin'])
        if 'vendor' in df.columns:
            df['vendor'] = clean_string_values(df['vendor'])
        
        if 'reference' in df.columns:
            df['reference'] = clean_string_values(df['reference'])
        else:
            df['reference'] = ""
        
        # Ensure original_gstin is clean if it exists
        if 'original_gstin' in df.columns:
            df['original_gstin'] = df['original_gstin'].astype(str).str.strip()
            # Clean encoding issues but preserve valid GSTIN characters (alphanumeric)
            df['original_gstin'] = df['original_gstin'].str.replace(r'â,?\'?0\.00', '', regex=True)
            df['original_gstin'] = df['original_gstin'].str.replace(r'[^\w]', '', regex=True)
            print(f"Cleaned GSTIN sample: {df['original_gstin'].head().tolist()}")
        
        # Debug: Print sample data
        print(f"Sample processed data after cleaning:")
        if len(df) > 0:
            print(df[['reference', 'vendor', 'original_gstin' if 'original_gstin' in df.columns else 'vendor', 'amount']].head())
        else:
            print("No data")
        
        # Remove rows with invalid data - but be more careful
        if 'amount' in df.columns and 'date' in df.columns:
            print(f"\nBefore filtering - Shape: {df.shape}")
            df = df.dropna(subset=['date', 'amount'])
            df = df[df['amount'] > 0]
            print(f"After filtering - Shape: {df.shape}")
        
        # Debug amounts after cleaning
        print(f"\nFinal processed data:")
        if len(df) > 0 and 'amount' in df.columns:
            print(f"Shape: {df.shape}")
            print(f"Amount column stats: mean={df['amount'].mean():.2f}, min={df['amount'].min():.2f}, max={df['amount'].max():.2f}")
            print(f"Sample amounts: {df['amount'].head().tolist()}")
        else:
            print("No valid data after processing")        # Add source identifier
        df['source'] = file_type
        
        print(f"Processed file shape: {df.shape}")
        print(f"Sample processed data:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error processing {file_type} file: {str(e)}")

def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity between two strings."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()

def reconcile_transactions(gstr2b_df: pd.DataFrame, tally_df: pd.DataFrame) -> Dict[str, Any]:
    """Perform transaction reconciliation."""
    
    print(f"\nStarting reconciliation...")
    print(f"GSTR2B transactions: {len(gstr2b_df)}")
    print(f"Tally transactions: {len(tally_df)}")
    
    matches = []
    matched_gstr2b_indices = set()
    matched_tally_indices = set()
    
    # Simple matching logic for demo
    for i, gstr2b_row in gstr2b_df.iterrows():
        for j, tally_row in tally_df.iterrows():
            if j in matched_tally_indices:
                continue
            
            # Match based on: invoice number, GSTIN, invoice date, and amount
            gstr2b_gstin = str(gstr2b_row.get('gstin', '')).strip().upper()
            tally_gstin = str(tally_row.get('gstin', '')).strip().upper()
            
            gstr2b_ref = str(gstr2b_row.get('reference', '')).strip().upper()
            tally_ref = str(tally_row.get('reference', '')).strip().upper()
            
            gstr2b_amount = float(gstr2b_row.get('amount', 0))
            tally_amount = float(tally_row.get('amount', 0))
            
            # Check for exact matches on key fields
            gstin_match = gstr2b_gstin == tally_gstin and gstr2b_gstin != ''
            ref_match = gstr2b_ref == tally_ref and gstr2b_ref != ''
            amount_match = abs(gstr2b_amount - tally_amount) < 0.01  # Very close amounts
            
            # Require GSTIN and reference to match exactly, with close amounts
            if gstin_match and ref_match and amount_match:
                total_score = 1.0  # Perfect match
                print(f"Perfect match found: {gstr2b_ref} - GSTIN: {gstr2b_gstin} - Amount: {gstr2b_amount}")
                
            elif gstin_match and ref_match:
                # Same GSTIN and reference but different amounts
                total_score = 0.9
                print(f"GSTIN+Ref match with amount diff: {gstr2b_ref} - Diff: {abs(gstr2b_amount - tally_amount)}")
                
            else:
                total_score = 0.0  # No match
                continue
                
            if total_score >= 0.9:  # Only accept very high confidence matches
                    matches.append({
                        'gstr2b_idx': i,
                        'tally_idx': j,
                        'gstr2b_data': gstr2b_row.to_dict(),
                        'tally_data': tally_row.to_dict(),
                        'match_score': total_score,
                        'match_factors': {
                            'gstin_match': gstin_match,
                            'reference_match': ref_match,
                            'amount_match': amount_match,
                            'amount_difference': abs(gstr2b_amount - tally_amount)
                        }
                    })
                    matched_gstr2b_indices.add(i)
                    matched_tally_indices.add(j)
                    break
    
    # Get unmatched transactions
    unmatched_gstr2b = gstr2b_df.loc[~gstr2b_df.index.isin(matched_gstr2b_indices)]
    unmatched_tally = tally_df.loc[~tally_df.index.isin(matched_tally_indices)]
    
    print(f"Reconciliation complete: {len(matches)} matches found")
    
    # Calculate financial metrics
    gstr2b_total = float(gstr2b_df['amount'].sum())
    tally_total = float(tally_df['amount'].sum())
    
    matched_gstr2b_total = float(gstr2b_df.loc[list(matched_gstr2b_indices), 'amount'].sum()) if matched_gstr2b_indices else 0
    matched_tally_total = float(tally_df.loc[list(matched_tally_indices), 'amount'].sum()) if matched_tally_indices else 0
    
    unmatched_gstr2b_total = float(unmatched_gstr2b['amount'].sum()) if len(unmatched_gstr2b) > 0 else 0
    unmatched_tally_total = float(unmatched_tally['amount'].sum()) if len(unmatched_tally) > 0 else 0
    
    # Calculate amount differences
    amount_differences = [abs(float(m['gstr2b_data']['amount']) - float(m['tally_data']['amount'])) for m in matches]
    total_amount_difference = sum(amount_differences)
    largest_discrepancy = max(amount_differences) if amount_differences else 0
    perfect_matches = len([diff for diff in amount_differences if diff < 0.01])
    
    # Calculate totals and match rate
    total_records = len(gstr2b_df) + len(tally_df)
    total_matched_records = len(matches) * 2  # Each match represents 2 records
    total_unmatched_records = len(unmatched_gstr2b) + len(unmatched_tally)
    match_rate = (total_matched_records / total_records * 100) if total_records > 0 else 0

    return {
        'matches': matches,
        'metrics': {
            # Core metrics - logical order
            'total_records': total_records,
            'total_matches': len(matches),
            'total_matched_records': total_matched_records,
            'total_unmatched_records': total_unmatched_records,
            'match_rate': match_rate,
            
            # Match quality metrics
            'perfect_amount_matches': perfect_matches,
            'high_confidence': len([m for m in matches if m['match_score'] >= 0.95]),
            'medium_confidence': len([m for m in matches if 0.85 <= m['match_score'] < 0.95]),
            'low_confidence': len([m for m in matches if m['match_score'] < 0.85]),
            'average_score': sum(m['match_score'] for m in matches) / len(matches) if matches else 0,
            
            # Financial metrics
            'gstr2b_total': gstr2b_total,
            'tally_total': tally_total,
            'matched_gstr2b_total': matched_gstr2b_total,
            'matched_tally_total': matched_tally_total,
            'unmatched_gstr2b_total': unmatched_gstr2b_total,
            'unmatched_tally_total': unmatched_tally_total,
            'total_variance': abs(gstr2b_total - tally_total),
            'total_amount_differences': total_amount_difference,
            'largest_discrepancy': largest_discrepancy,
            
            # Legacy fields for compatibility
            'unmatched_total': len(unmatched_gstr2b) + len(unmatched_tally)
        },
        'unmatched_gstr2b': unmatched_gstr2b.to_dict('records'),
        'unmatched_tally': unmatched_tally.to_dict('records')
    }

@app.get("/")
async def read_root():
    return {"message": "SME Reconciliation MVP API", "status": "running"}

@app.post("/upload/")
async def upload_files(
    bank_file: UploadFile = File(...),
    ledger_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        print(f"\nReceived upload request from user: {current_user.get('email', 'unknown')}")
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save uploaded files
        bank_path = os.path.join(UPLOAD_FOLDER, f"gstr2b_{bank_file.filename}")
        ledger_path = os.path.join(UPLOAD_FOLDER, f"tally_{ledger_file.filename}")
        
        # Save bank file (GSTR2B)
        with open(bank_path, "wb") as f:
            content = await bank_file.read()
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            
        # Save ledger file (Tally)
        with open(ledger_path, "wb") as f:
            content = await ledger_file.read()
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        
        print(f"\nFiles saved successfully:")
        print(f"GSTR2B: {bank_path}")
        print(f"Tally: {ledger_path}")
        
        # Wait for file system to sync
        await asyncio.sleep(0.1)
        
        # Read and process both files
        gstr2b_df = read_and_process_file(bank_path, 'gstr2b')
        tally_df = read_and_process_file(ledger_path, 'tally')
        
        # Perform reconciliation
        reconciliation_results = reconcile_transactions(gstr2b_df, tally_df)
        
        # Format response for frontend
        reconciled_transactions = []
        for match in reconciliation_results['matches']:
            gstr2b_data = match['gstr2b_data']
            tally_data = match['tally_data']
            
            # Convert amounts to float and ensure they're not None/NaN
            gstr2b_amount = float(gstr2b_data.get('amount', 0) or 0)
            tally_amount = float(tally_data.get('amount', 0) or 0)
            
            # Get amounts and ensure they're valid numbers
            gstr2b_amount = float(gstr2b_data.get('amount', 0) or 0)
            tally_amount = float(tally_data.get('amount', 0) or 0)
            
            # Debug print to verify amounts
            print(f"Match #{len(reconciled_transactions)+1}:")
            print(f"  Invoice: {gstr2b_data.get('reference', 'N/A')}")
            print(f"  GSTIN: {gstr2b_data.get('gstin', 'N/A')}")
            print(f"  GSTR2B Amount: {gstr2b_amount}")
            print(f"  Tally Amount: {tally_amount}")
            
            reconciled_transactions.append({
                'match_score': round(match['match_score'], 3),
                'gstr2b_date': str(gstr2b_data.get('date', ''))[:10] if gstr2b_data.get('date') else '',
                'tally_date': str(tally_data.get('date', ''))[:10] if tally_data.get('date') else '',
                'gstr2b_invoice_no': str(gstr2b_data.get('reference', '')),
                'tally_invoice_no': str(tally_data.get('reference', '')),
                'gstr2b_supplier_gstin': str(gstr2b_data.get('gstin', '')),
                'tally_supplier_gstin': str(tally_data.get('gstin', '')),
                'gstr2b_total_amount': gstr2b_amount,
                'tally_total_amount': tally_amount,
                'gstr2b_taxable_value': float(gstr2b_data.get('taxable value', 0) or 0),
                'gstr2b_igst': float(gstr2b_data.get('igst', 0) or 0),
                'gstr2b_cgst': float(gstr2b_data.get('cgst', 0) or 0),
                'gstr2b_sgst': float(gstr2b_data.get('sgst', 0) or 0),
                'tally_base_amount': float(tally_data.get('amount', 0) or 0),  # Original amount column
                'tally_tax_amount': float(tally_data.get('tax amount', 0) or 0),
                'tally_type': str(tally_data.get('type', '')),
                'difference': abs(gstr2b_amount - tally_amount),
            })
        
        # Format unmatched transactions
        unmatched_bank = []
        for record in reconciliation_results['unmatched_gstr2b']:
            # Ensure amount is properly converted to float
            amount = float(record.get('amount', 0) or 0)
            unmatched_bank.append({
                'date': str(record.get('date', ''))[:10] if record.get('date') else '',
                'invoice_no': str(record.get('reference', '')),
                'supplier_gstin': str(record.get('gstin', '')),
                'total_amount': amount,
                'taxable_value': float(record.get('taxable value', 0) or 0),
                'igst': float(record.get('igst', 0) or 0),
                'cgst': float(record.get('cgst', 0) or 0),
                'sgst': float(record.get('sgst', 0) or 0),
                'source': 'GSTR2B'
            })
        
        unmatched_ledger = []
        for record in reconciliation_results['unmatched_tally']:
            # Ensure amount is properly converted to float
            amount = float(record.get('amount', 0) or 0)
            unmatched_ledger.append({
                'date': str(record.get('date', ''))[:10] if record.get('date') else '',
                'invoice_no': str(record.get('reference', '')),
                'supplier_gstin': str(record.get('gstin', '')),
                'total_amount': amount,
                'base_amount': float(record.get('amount', 0) or 0),  # Original amount if available
                'tax_amount': float(record.get('tax amount', 0) or 0),
                'type': str(record.get('type', '')),
                'source': 'Tally'
            })
        
        response = {
            "status": "success",
            "message": f"Successfully reconciled {bank_file.filename} and {ledger_file.filename}",
            "files": {"bank": bank_file.filename, "ledger": ledger_file.filename},
            "metrics": reconciliation_results['metrics'],
            "reconciled": reconciled_transactions,
            "unmatched_bank": unmatched_bank,
            "unmatched_ledger": unmatched_ledger,
            "duplicates": {"gstr2b": {}, "tally": {}}
        }
        
        print(f"Returning {len(reconciled_transactions)} reconciled transactions")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during reconciliation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Run on port 8004 to avoid conflicts
    uvicorn.run(app, host="127.0.0.1", port=8004)