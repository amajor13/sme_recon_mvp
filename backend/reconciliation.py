import pandas as pd

def reconcile_transactions(df: pd.DataFrame):
    # Assumes df has 'date', 'amount', 'vendor' columns
    df['matched'] = False
    
    reconciled = []
    unmatched = []

    seen = set()
    for idx, row in df.iterrows():
        key = (row['date'], row['amount'], row['vendor'])
        if key not in seen:
            reconciled.append(row)
            seen.add(key)
        else:
            unmatched.append(row)
    
    reconciled_df = pd.DataFrame(reconciled)
    unmatched_df = pd.DataFrame(unmatched)
    
    return reconciled_df, unmatched_df
