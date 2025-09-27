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
    
    # Convert date columns to datetime if they aren't already
    for df in [bank, ledger]:
        if df['date'].dtype != 'datetime64[ns]':
            df['date'] = pd.to_datetime(df['date'])
    
    # Add source column to identify origin
    bank['source'] = 'bank'
    ledger['source'] = 'ledger'
    
    # Add unique index to track duplicates
    bank['bank_index'] = range(len(bank))
    ledger['ledger_index'] = range(len(ledger))
    
    # Initialize match status
    bank['matched'] = False
    ledger['matched'] = False
    
    reconciled = []
    
    # Group transactions by key to handle duplicates
    bank_groups = bank.groupby(['date', 'amount', 'vendor'])
    ledger_groups = ledger.groupby(['date', 'amount', 'vendor'])
    
    # Iterate through unique combinations
    for key, bank_group in bank_groups:
        if key in ledger_groups.groups:
            ledger_group = ledger_groups.get_group(key)
            
            # Get counts of transactions
            bank_count = len(bank_group)
            ledger_count = len(ledger_group)
            
            # Match the minimum number of transactions from each side
            matches = min(bank_count, ledger_count)
            
            # Get unmatched entries from both groups
            unmatched_bank = bank_group[~bank_group['bank_index'].isin(
                [r.get('bank_index') for r in reconciled])]
            unmatched_ledger = ledger_group[~ledger_group['ledger_index'].isin(
                [r.get('ledger_index') for r in reconciled])]
            
            # Match transactions up to the minimum count
            for i in range(matches):
                bank_row = unmatched_bank.iloc[i]
                ledger_row = unmatched_ledger.iloc[i]
                
                # Add to reconciled list
                reconciled.append({
                    'date': bank_row['date'],
                    'amount': bank_row['amount'],
                    'vendor': bank_row['vendor'],
                    'description': bank_row.get('description', ''),
                    'bank_reference': str(bank_row.get('reference', '')),
                    'ledger_reference': str(ledger_row.get('reference', '')),
                    'bank_index': bank_row['bank_index'],
                    'ledger_index': ledger_row['ledger_index']
                })
    
    # Create reconciled DataFrame
    reconciled_df = pd.DataFrame(reconciled)
    
    # Mark matched transactions
    if not reconciled_df.empty:
        bank.loc[bank['bank_index'].isin(reconciled_df['bank_index']), 'matched'] = True
        ledger.loc[ledger['ledger_index'].isin(reconciled_df['ledger_index']), 'matched'] = True
    
    # Get unmatched transactions
    unmatched_bank = bank[~bank['matched']].copy()
    unmatched_ledger = ledger[~ledger['matched']].copy()
    
    # Clean up temporary columns
    for df in [reconciled_df, unmatched_bank, unmatched_ledger]:
        if not df.empty:
            df.drop(columns=['bank_index', 'ledger_index', 'matched', 'source'], errors='ignore', inplace=True)
    
    return reconciled_df, unmatched_bank, unmatched_ledger
    
    # Get unmatched transactions
    unmatched_bank = bank[~bank['matched']].copy()
    unmatched_ledger = ledger[~ledger['matched']].copy()
    
    # Convert reconciled list to DataFrame
    reconciled_df = pd.DataFrame(reconciled)
    
    return reconciled_df, unmatched_bank, unmatched_ledger
