import pandas as pd
from typing import Tuple

def reconcile_transactions(bank_df: pd.DataFrame, ledger_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reconcile transactions between GSTR2B and Tally entries.
    
    Args:
        bank_df (pd.DataFrame): GSTR2B transactions
        ledger_df (pd.DataFrame): Tally transactions
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
            - Reconciled transactions
            - Unmatched GSTR2B transactions
            - Unmatched Tally transactions
    """
    # Create copies to avoid modifying original dataframes
    gstr2b = bank_df.copy()
    tally = ledger_df.copy()
    
    # Debug information
    print("\nDebug Info:")
    print("GSTR2B Columns:", gstr2b.columns.tolist())
    print("Tally Columns:", tally.columns.tolist())
    print("\nGSTR2B Data Types:")
    print(gstr2b.dtypes)
    print("\nTally Data Types:")
    print(tally.dtypes)
    
    # Clean and prepare data
    for df, name in [(gstr2b, 'GSTR2B'), (tally, 'Tally')]:
        # Convert amounts to float
        if 'amount' in df.columns:
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            print(f"\n{name} amount values (first 5):")
            print(df['amount'].head())
        
        # Convert dates to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            print(f"\n{name} date values (first 5):")
            print(df['date'].head())
        
        # Clean vendor IDs (GSTINs)
        if 'vendor' in df.columns:
            df['vendor'] = df['vendor'].astype(str).str.upper().str.strip()
            print(f"\n{name} vendor values (first 5):")
            print(df['vendor'].head())
    
    # Add unique index to track matches
    gstr2b['gstr2b_index'] = range(len(gstr2b))
    tally['tally_index'] = range(len(tally))
    
    # Initialize match status
    gstr2b['matched'] = False
    tally['matched'] = False
    
    reconciled = []
    
    # Function to check if amounts are close enough (within 1 rupee)
    def amounts_match(a1, a2, tolerance=1.0):
        try:
            return abs(float(a1) - float(a2)) <= tolerance
        except (ValueError, TypeError):
            return False
    
    # Iterate through GSTR2B entries
    for idx, gstr_row in gstr2b.iterrows():
        if gstr_row['matched']:
            continue
            
        # Find matching Tally entries
        potential_matches = tally[
            (tally['date'] == gstr_row['date']) &
            (tally['vendor'] == gstr_row['vendor']) &
            (~tally['matched'])
        ]
        
        # Debug output for potential matches
        if not potential_matches.empty:
            print(f"\nFound potential matches for GSTR2B entry:")
            print(f"GSTR2B: Date={gstr_row['date']}, Amount={gstr_row['amount']}, Vendor={gstr_row['vendor']}")
            print("Potential Tally matches:")
            print(potential_matches[['date', 'amount', 'vendor']].head())
        
        # Check amounts with tolerance
        for _, tally_row in potential_matches.iterrows():
            if amounts_match(gstr_row['amount'], tally_row['amount']):
                reconciled.append({
                    'date': gstr_row['date'],
                    'amount': gstr_row['amount'],
                    'vendor': gstr_row['vendor'],
                    'gstr2b_reference': str(gstr_row.get('reference', '')),
                    'tally_reference': str(tally_row.get('reference', '')),
                    'gstr2b_index': gstr_row['gstr2b_index'],
                    'tally_index': tally_row['tally_index']
                })
                
                # Mark as matched
                gstr2b.loc[gstr2b['gstr2b_index'] == gstr_row['gstr2b_index'], 'matched'] = True
                tally.loc[tally['tally_index'] == tally_row['tally_index'], 'matched'] = True
                break
    
    # Convert reconciled list to DataFrame
    reconciled_df = pd.DataFrame(reconciled)
    
    # Get unmatched transactions
    unmatched_gstr2b = gstr2b[~gstr2b['matched']].copy()
    unmatched_tally = tally[~tally['matched']].copy()
    
    # Clean up temporary columns
    for df in [reconciled_df, unmatched_gstr2b, unmatched_tally]:
        if not df.empty:
            df.drop(columns=['gstr2b_index', 'tally_index', 'matched'], errors='ignore', inplace=True)
    
    # Print summary
    print("\nReconciliation Summary:")
    print(f"Total GSTR2B entries: {len(gstr2b)}")
    print(f"Total Tally entries: {len(tally)}")
    print(f"Reconciled entries: {len(reconciled_df)}")
    print(f"Unmatched GSTR2B entries: {len(unmatched_gstr2b)}")
    print(f"Unmatched Tally entries: {len(unmatched_tally)}")
    
    if len(reconciled_df) == 0:
        print("\nNo matches found. Sample entries for debugging:")
        print("\nGSTR2B Sample (first 3 entries):")
        print(gstr2b[['date', 'amount', 'vendor']].head(3))
        print("\nTally Sample (first 3 entries):")
        print(tally[['date', 'amount', 'vendor']].head(3))
    
    return reconciled_df, unmatched_gstr2b, unmatched_tally
