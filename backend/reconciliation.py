import pandas as pd
from typing import Tuple

def reconcile_transactions(bank_df: pd.DataFrame, ledger_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reconcile transactions between bank statements and ledger entries.
    
    Args:
        bank_df (pd.DataFrame): Bank statement transactions
        ledger_df (pd.DataFrame): Ledger transactions
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
            - Reconciled transactions
            - Unmatched bank transactions
            - Unmatched ledger transactions
    """
    # Create copies to avoid modifying original dataframes
    bank = bank_df.copy()
    ledger = ledger_df.copy()
    
    # Add source column to identify origin
    bank['source'] = 'bank'
    ledger['source'] = 'ledger'
    
    # Initialize match status
    bank['matched'] = False
    ledger['matched'] = False
    
    reconciled = []
    
    # Match transactions
    for bank_idx, bank_row in bank.iterrows():
        key = (bank_row['date'], bank_row['amount'], bank_row['vendor'])
        
        # Look for matching transaction in ledger
        matches = ledger[
            (ledger['date'] == bank_row['date']) & 
            (ledger['amount'] == bank_row['amount']) & 
            (ledger['vendor'] == bank_row['vendor']) &
            (~ledger['matched'])  # Only consider unmatched ledger entries
        ]
        
        if not matches.empty:
            # Get the first match
            ledger_row = matches.iloc[0]
            
            # Mark both transactions as matched
            bank.loc[bank_idx, 'matched'] = True
            ledger.loc[ledger_row.name, 'matched'] = True
            
            # Add to reconciled list with both references
            reconciled.append({
                'date': bank_row['date'],
                'amount': bank_row['amount'],
                'vendor': bank_row['vendor'],
                'description': bank_row.get('description', ''),
                'bank_reference': bank_row.get('reference', ''),
                'ledger_reference': ledger_row.get('reference', '')
            })
    
    # Get unmatched transactions
    unmatched_bank = bank[~bank['matched']].copy()
    unmatched_ledger = ledger[~ledger['matched']].copy()
    
    # Convert reconciled list to DataFrame
    reconciled_df = pd.DataFrame(reconciled)
    
    return reconciled_df, unmatched_bank, unmatched_ledger
