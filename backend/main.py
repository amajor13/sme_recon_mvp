from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import os
import re
import asyncio
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from difflib import SequenceMatcher
import Levenshtein

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))

def clean_numeric_values(series):
    """Clean and convert a pandas series to numeric values."""
    def clean_single_value(val):
        if pd.isna(val):
            return 0.0
        
        try:
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
                return float(val) / 100
            
            # Try to convert to float
            return float(val)
        except (ValueError, TypeError):
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
    return series.astype(str).str.strip().str.upper()

def read_and_process_file(filepath: str, file_type: str) -> pd.DataFrame:
    """Read and process uploaded file."""
    print(f"\nReading file: {filepath}")
    
    try:
        # Read file based on extension
        if filepath.lower().endswith('.csv'):
            # Try different encodings and delimiters for CSV files
            encodings = ['utf-8', 'iso-8859-1', 'cp1252']
            delimiters = [',', ';', '\t']
            
            df = None
            for encoding in encodings:
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding, sep=delimiter)
                        print(f"Successfully read CSV with encoding: {encoding}, delimiter: {delimiter}")
                        break
                    except Exception:
                        continue
                if df is not None:
                    break
            
            if df is None:
                raise ValueError("Could not read CSV file with any common encoding/delimiter combination")
        else:
            # For Excel files
            df = pd.read_excel(filepath)
        
        if df.empty:
            raise ValueError("File appears to be empty")
        
        print(f"Original file shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")
        
        # Clean up column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Standardize column names based on file type
        if 'gstr2b' in file_type.lower():
            # GSTR2B file processing - use Total Invoice Value for comparison
            column_mapping = {
                'invoice date': 'date',
                'total invoice value': 'amount',  # Use total amount including taxes
                'supplier gstin': 'vendor',
                'invoice no': 'reference',
                'gstin of supplier': 'vendor',
                'invoice number': 'reference',
                'taxable value': 'taxable_amount',
                'igst': 'igst',
                'cgst': 'cgst', 
                'sgst': 'sgst'
            }
        else:
            # Tally file processing - use Total Amount for comparison
            column_mapping = {
                'date': 'date',
                'amount': 'base_amount',        # Keep base amount separate
                'total amount': 'amount',       # Use total amount including taxes
                'vendor': 'vendor',
                'supplier gstin': 'vendor',
                'reference': 'reference',
                'invoice no': 'reference',
                'invoice number': 'reference'
            }
        
        # Apply column mapping
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and new_col not in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Ensure we have required columns
        required_cols = ['date', 'amount', 'vendor']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}. Available columns: {list(df.columns)}")
        
        # Process each column
        df['date'] = clean_date_values(df['date'])
        df['amount'] = clean_numeric_values(df['amount'])
        df['vendor'] = clean_string_values(df['vendor'])
        
        if 'reference' in df.columns:
            df['reference'] = clean_string_values(df['reference'])
        else:
            df['reference'] = ""
        
        # Remove rows with invalid data
        df = df.dropna(subset=['date', 'amount'])
        df = df[df['amount'] > 0]  # Remove zero amounts
        
        # Add source identifier
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
    """Perform transaction reconciliation between GSTR2B and Tally data."""
    
    print(f"\nStarting reconciliation...")
    print(f"GSTR2B transactions: {len(gstr2b_df)}")
    print(f"Tally transactions: {len(tally_df)}")
    
    # Show sample data for debugging
    print(f"\nSample GSTR2B data:")
    for i in range(min(3, len(gstr2b_df))):
        row = gstr2b_df.iloc[i]
        print(f"  {i}: {row['reference']} | {row['vendor']} | {row['amount']} | {row['date']}")
    
    print(f"\nSample Tally data:")  
    for i in range(min(3, len(tally_df))):
        row = tally_df.iloc[i]
        print(f"  {i}: {row['reference']} | {row['vendor']} | {row['amount']} | {row['date']}")
    
    matches = []
    matched_gstr2b_indices = set()
    matched_tally_indices = set()
    
    # Improved configuration for matching with higher precision
    amount_tolerance_percent = 0.05  # 5% amount tolerance
    date_window = 30  # 30 days window 
    vendor_similarity_threshold = 0.6  # Vendor similarity threshold
    min_match_threshold = 0.5  # Higher minimum threshold for better quality matches
    
    match_attempts = 0
    
    for i, gstr2b_row in gstr2b_df.iterrows():
        best_match = None
        best_score = 0.0
        best_tally_idx = None
        best_debug_info = None
        
        for j, tally_row in tally_df.iterrows():
            if j in matched_tally_indices:
                continue
                
            match_attempts += 1
            
            # Calculate match score based on multiple factors
            score = 0.0
            factors = {}
            debug_info = {}
            
            # 1. Reference/Invoice number matching (HIGHEST PRIORITY for exact matches)
            ref_sim = similarity_score(str(gstr2b_row['reference']), str(tally_row['reference']))
            if ref_sim >= 0.98:  # Perfect or near-perfect match
                score += 0.65  # 65% of total score for perfect invoice match
            elif ref_sim >= 0.9:  # Very high similarity
                score += 0.55 + (ref_sim - 0.9) * 1.0  # 55% + bonus up to 65%
            elif ref_sim >= 0.8:  # High similarity
                score += ref_sim * 0.5  # Up to 40% for high similarity
            else:
                score += ref_sim * 0.15  # Up to 15% for partial similarity
            factors['reference'] = ref_sim
            debug_info['ref_sim'] = ref_sim
            
            # 2. Amount matching (second priority)
            gstr2b_amount = float(gstr2b_row['amount'])
            tally_amount = float(tally_row['amount'])
            amount_diff = abs(gstr2b_amount - tally_amount)
            amount_percent_diff = amount_diff / max(gstr2b_amount, tally_amount) if max(gstr2b_amount, tally_amount) > 0 else 1
            
            if amount_percent_diff <= 0.001:  # Perfect match (within 0.1%)
                amount_score = 1.0
                score += 0.25  # Full 25% for perfect amount match
                factors['amount'] = amount_score
            elif amount_percent_diff <= amount_tolerance_percent:
                amount_score = 1.0 - (amount_percent_diff / amount_tolerance_percent)
                score += amount_score * 0.25
                factors['amount'] = amount_score
            else:
                # Still give partial score for reasonable differences
                if amount_percent_diff <= 0.2:  # Within 20%
                    amount_score = max(0, 1.0 - (amount_percent_diff / 0.2)) * 0.5
                    score += amount_score * 0.25
                    factors['amount'] = amount_score
                else:
                    factors['amount'] = 0
            
            debug_info['amount_diff'] = amount_diff
            debug_info['amount_percent_diff'] = amount_percent_diff
            
            # 3. Date matching (third priority)
            try:
                date_diff = abs((gstr2b_row['date'] - tally_row['date']).days)
                if date_diff == 0:  # Exact same date
                    score += 0.08  # Full 8% for exact date match
                    factors['date'] = 1.0
                elif date_diff <= date_window:
                    date_score = max(0, 1 - (date_diff / date_window))
                    score += date_score * 0.08
                    factors['date'] = date_score
                else:
                    factors['date'] = 0
                debug_info['date_diff'] = date_diff
            except Exception as e:
                factors['date'] = 0
                debug_info['date_error'] = str(e)
            
            # 4. Vendor similarity (for tie-breaking and validation)
            vendor_sim = similarity_score(str(gstr2b_row['vendor']), str(tally_row['vendor']))
            if vendor_sim >= 0.95:  # Perfect or near-perfect vendor match
                score += 0.02  # 2% bonus for perfect vendor match
                factors['vendor'] = vendor_sim
            elif vendor_sim >= vendor_similarity_threshold:
                score += vendor_sim * 0.02  # Up to 2% for good vendor match
                factors['vendor'] = vendor_sim
            else:
                # Small partial score for any similarity
                score += vendor_sim * 0.01
                factors['vendor'] = vendor_sim
            debug_info['vendor_sim'] = vendor_sim
            
            debug_info['total_score'] = score
            debug_info['factors'] = factors
            
            # Update best match if this is better
            if score > best_score and score >= min_match_threshold:
                best_match = {
                    'gstr2b_idx': i,
                    'tally_idx': j,
                    'gstr2b_data': gstr2b_row.to_dict(),
                    'tally_data': tally_row.to_dict(),
                    'match_score': score,
                    'match_factors': factors
                }
                best_score = score
                best_tally_idx = j
                best_debug_info = debug_info
        
        # Debug: Show best attempt for first few transactions
        if i < 5:
            print(f"\nGSTR2B #{i} ({gstr2b_row['reference']}) best match score: {best_score:.3f}")
            if best_debug_info:
                print(f"  Amount diff: {best_debug_info['amount_diff']:.2f} ({best_debug_info['amount_percent_diff']:.1%})")
                print(f"  Date diff: {best_debug_info.get('date_diff', 'N/A')} days")
                print(f"  Vendor sim: {best_debug_info['vendor_sim']:.3f}")
                print(f"  Ref sim: {best_debug_info['ref_sim']:.3f}")
                print(f"  Score breakdown: Ref={best_debug_info['factors']['reference']:.3f}, Amount={best_debug_info['factors'].get('amount', 0):.3f}, Date={best_debug_info['factors'].get('date', 0):.3f}, Vendor={best_debug_info['factors']['vendor']:.3f}")
                
                # Calculate theoretical score breakdown for debugging
                ref_sim = best_debug_info['ref_sim']
                if ref_sim >= 0.98:
                    ref_contribution = 0.65
                elif ref_sim >= 0.9:
                    ref_contribution = 0.55 + (ref_sim - 0.9) * 1.0
                elif ref_sim >= 0.8:
                    ref_contribution = ref_sim * 0.5
                else:
                    ref_contribution = ref_sim * 0.15
                
                amount_contribution = best_debug_info['factors'].get('amount', 0) * 0.25
                date_contribution = best_debug_info['factors'].get('date', 0) * 0.08
                vendor_contribution = best_debug_info['factors']['vendor'] * 0.02
                calculated_score = ref_contribution + amount_contribution + date_contribution + vendor_contribution
                print(f"  Manual calc: Ref({ref_contribution:.3f}) + Amount({amount_contribution:.3f}) + Date({date_contribution:.3f}) + Vendor({vendor_contribution:.3f}) = {calculated_score:.3f}")
        
        # If we found a good match, add it
        if best_match:
            matches.append(best_match)
            matched_gstr2b_indices.add(i)
            matched_tally_indices.add(best_tally_idx)
    
    # Calculate metrics
    total_matches = len(matches)
    high_confidence = len([m for m in matches if m['match_score'] >= 0.95])  # Perfect/near-perfect matches
    medium_confidence = len([m for m in matches if 0.85 <= m['match_score'] < 0.95])  # Good matches
    low_confidence = len([m for m in matches if m['match_score'] < 0.85])  # Possible matches
    average_score = sum(m['match_score'] for m in matches) / total_matches if total_matches > 0 else 0
    
    # Get unmatched transactions
    unmatched_gstr2b = gstr2b_df.loc[~gstr2b_df.index.isin(matched_gstr2b_indices)]
    unmatched_tally = tally_df.loc[~tally_df.index.isin(matched_tally_indices)]
    
    print(f"\nReconciliation complete:")
    print(f"- Match attempts: {match_attempts}")
    print(f"- Total matches: {total_matches}")
    print(f"- High confidence: {high_confidence}")
    print(f"- Medium confidence: {medium_confidence}")
    print(f"- Low confidence: {low_confidence}")
    print(f"- Average score: {average_score:.3f}")
    print(f"- Unmatched GSTR2B: {len(unmatched_gstr2b)}")
    print(f"- Unmatched Tally: {len(unmatched_tally)}")
    
    if total_matches > 0:
        print(f"\nFirst few matches:")
        for i, match in enumerate(matches[:3]):
            print(f"  Match {i+1}: {match['gstr2b_data']['reference']} <-> {match['tally_data']['reference']} (score: {match['match_score']:.3f})")
    
    return {
        'matches': matches,
        'metrics': {
            'total_matches': total_matches,
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence,
            'average_score': average_score,
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
    ledger_file: UploadFile = File(...)
):
    try:
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
        
        # Format matches for frontend with all major fields
        reconciled_transactions = []
        for match in reconciliation_results['matches']:
            gstr2b_data = match['gstr2b_data']
            tally_data = match['tally_data']
            
            # Format dates properly
            try:
                gstr2b_date_str = gstr2b_data['date'].strftime('%Y-%m-%d') if pd.notnull(gstr2b_data['date']) and hasattr(gstr2b_data['date'], 'strftime') else str(gstr2b_data['date'])[:10] if str(gstr2b_data['date']) != 'nan' else ''
            except:
                gstr2b_date_str = ''
                
            try:
                tally_date_str = tally_data['date'].strftime('%Y-%m-%d') if pd.notnull(tally_data['date']) and hasattr(tally_data['date'], 'strftime') else str(tally_data['date'])[:10] if str(tally_data['date']) != 'nan' else ''
            except:
                tally_date_str = ''
            
            # Format amounts properly
            def safe_float(val, default=0.0):
                try:
                    return float(val) if pd.notnull(val) else default
                except:
                    return default
                    
            def safe_str(val, default=''):
                try:
                    return str(val) if pd.notnull(val) and str(val) != 'nan' else default
                except:
                    return default
            
            gstr2b_amount = safe_float(gstr2b_data['amount'])
            tally_amount = safe_float(tally_data['amount'])
            
            # Use the primary date and amount from the match
            primary_date = gstr2b_date_str if gstr2b_date_str else tally_date_str
            primary_amount = gstr2b_amount if gstr2b_amount != 0 else tally_amount
            
            reconciled_transactions.append({
                # Primary reconciliation fields
                'match_score': round(match['match_score'], 3),
                'date': primary_date,
                'amount': primary_amount,
                'vendor': safe_str(gstr2b_data['vendor']) or safe_str(tally_data['vendor']),
                'invoice_no': safe_str(gstr2b_data.get('reference', '')) or safe_str(tally_data.get('reference', '')),
                'gstr2b_reference': safe_str(gstr2b_data.get('reference', '')),  # Add this for old table compatibility
                'tally_reference': safe_str(tally_data.get('reference', '')),    # Add this for old table compatibility
                'amount_difference': abs(gstr2b_amount - tally_amount),
                'date_difference': abs((gstr2b_data['date'] - tally_data['date']).days) if pd.notnull(gstr2b_data['date']) and pd.notnull(tally_data['date']) else 0,
                
                # GSTR2B specific fields
                'gstr2b_date': gstr2b_date_str,
                'gstr2b_invoice_no': safe_str(gstr2b_data.get('reference', '')),
                'gstr2b_supplier_gstin': safe_str(gstr2b_data['vendor']),
                'gstr2b_total_amount': gstr2b_amount,
                'gstr2b_taxable_value': safe_float(gstr2b_data.get('taxable_amount', 0)),
                'gstr2b_igst': safe_float(gstr2b_data.get('igst', 0)),
                'gstr2b_cgst': safe_float(gstr2b_data.get('cgst', 0)),
                'gstr2b_sgst': safe_float(gstr2b_data.get('sgst', 0)),
                
                # Tally specific fields
                'tally_date': tally_date_str,
                'tally_invoice_no': safe_str(tally_data.get('reference', '')),
                'tally_supplier_gstin': safe_str(tally_data['vendor']),
                'tally_total_amount': tally_amount,
                'tally_base_amount': safe_float(tally_data.get('base_amount', 0)),
                'tally_tax_amount': safe_float(tally_data.get('tax amount', 0)),
                'tally_type': safe_str(tally_data.get('type', '')),
                
                # Match quality indicators
                'reference_similarity': match['match_factors'].get('reference', 0),
                'amount_similarity': match['match_factors'].get('amount', 0),
                'date_similarity': match['match_factors'].get('date', 0),
                'vendor_similarity': match['match_factors'].get('vendor', 0)
            })
        
        # Format unmatched transactions for frontend with all fields
        def safe_float(val, default=0.0):
            try:
                return float(val) if pd.notnull(val) else default
            except:
                return default
                
        def safe_str(val, default=''):
            try:
                return str(val) if pd.notnull(val) and str(val) != 'nan' else default
            except:
                return default
        
        def safe_date(val):
            try:
                return val.strftime('%Y-%m-%d') if pd.notnull(val) and hasattr(val, 'strftime') else str(val)[:10] if str(val) != 'nan' else ''
            except:
                return ''
        
        unmatched_bank = []
        for record in reconciliation_results['unmatched_gstr2b']:
            unmatched_bank.append({
                'date': safe_date(record['date']),
                'amount': safe_float(record['amount']),  # Add for old table compatibility
                'vendor': safe_str(record['vendor']),   # Add for old table compatibility
                'reference': safe_str(record.get('reference', '')),  # Add for old table compatibility
                'invoice_no': safe_str(record.get('reference', '')),
                'supplier_gstin': safe_str(record['vendor']),
                'total_amount': safe_float(record['amount']),
                'taxable_value': safe_float(record.get('taxable_amount', 0)),
                'igst': safe_float(record.get('igst', 0)),
                'cgst': safe_float(record.get('cgst', 0)),
                'sgst': safe_float(record.get('sgst', 0)),
                'source': 'GSTR2B'
            })
        
        unmatched_ledger = []
        for record in reconciliation_results['unmatched_tally']:
            unmatched_ledger.append({
                'date': safe_date(record['date']),
                'amount': safe_float(record['amount']),  # Add for old table compatibility
                'vendor': safe_str(record['vendor']),   # Add for old table compatibility
                'reference': safe_str(record.get('reference', '')),  # Add for old table compatibility
                'invoice_no': safe_str(record.get('reference', '')),
                'supplier_gstin': safe_str(record['vendor']),
                'total_amount': safe_float(record['amount']),
                'base_amount': safe_float(record.get('base_amount', 0)),
                'tax_amount': safe_float(record.get('tax amount', 0)),
                'type': safe_str(record.get('type', '')),
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
            "duplicates": {
                "gstr2b": {},
                "tally": {}
            }
        }
        
        print(f"\nReturning response with {len(reconciled_transactions)} matches")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during reconciliation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reconciliation failed: {str(e)}")