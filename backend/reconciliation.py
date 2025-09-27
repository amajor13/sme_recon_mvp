import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from Levenshtein import ratio
from datetime import timedelta

def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate string similarity using Levenshtein ratio."""
    if pd.isna(str1) or pd.isna(str2):
        return 0.0
    return ratio(str(str1).upper(), str(str2).upper())

def find_duplicates(df: pd.DataFrame, tolerance: float = 1.0, date_window: int = 3) -> Dict[int, List[int]]:
    """Find potential duplicate transactions within a dataframe.
    
    Args:
        df: DataFrame with transactions
        tolerance: Amount difference tolerance
        date_window: Number of days to look around each transaction
        
    Returns:
        Dictionary mapping transaction index to list of potential duplicate indices
    """
    duplicates = {}
    for i, row in df.iterrows():
        date_mask = abs((df['date'] - row['date']).dt.days) <= date_window
        amount_mask = abs(df['amount'] - row['amount']) <= tolerance
        
        potential_dupes = df[
            date_mask & 
            amount_mask & 
            (df.index != i)
        ].index.tolist()
        
        if potential_dupes:
            duplicates[i] = potential_dupes
    
    return duplicates

def reconcile_transactions(
    bank_df: pd.DataFrame, 
    ledger_df: pd.DataFrame,
    match_config: Dict = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
    
    # Set default match configuration if not provided
    if match_config is None:
        match_config = {
            'amount_tolerance': 1.0,  # Amount difference tolerance in rupees
            'date_window': 3,         # Days to look around for matches
            'vendor_similarity': 0.85, # Minimum vendor name similarity ratio
            'ref_similarity': 0.7      # Minimum reference number similarity ratio
        }
    
    # Initialize match status and confidence scores
    gstr2b['matched'] = False
    tally['matched'] = False
    
    # Find potential duplicates in both datasets
    gstr2b_dupes = find_duplicates(gstr2b, match_config['amount_tolerance'], match_config['date_window'])
    tally_dupes = find_duplicates(tally, match_config['amount_tolerance'], match_config['date_window'])
    
    if gstr2b_dupes:
        print("\nPotential duplicates in GSTR2B:")
        for idx, dupes in gstr2b_dupes.items():
            print(f"Entry {idx} has similar entries: {dupes}")
    
    if tally_dupes:
        print("\nPotential duplicates in Tally:")
        for idx, dupes in tally_dupes.items():
            print(f"Entry {idx} has similar entries: {dupes}")
    
    reconciled = []
    
    def calculate_match_score(gstr_row, tally_row):
        """Calculate a confidence score for a potential match."""
        scores = {
            'amount': 1.0 if abs(gstr_row['amount'] - tally_row['amount']) <= match_config['amount_tolerance'] else 0.0,
            'date': 1.0 if abs((gstr_row['date'] - tally_row['date']).days) <= match_config['date_window'] else 0.0,
            'vendor': calculate_similarity(gstr_row['vendor'], tally_row['vendor']),
            'reference': calculate_similarity(
                str(gstr_row.get('reference', '')), 
                str(tally_row.get('reference', ''))
            ) if 'reference' in gstr_row and 'reference' in tally_row else 0.5
        }
        
        # Weighted average of scores
        weights = {'amount': 0.4, 'date': 0.3, 'vendor': 0.2, 'reference': 0.1}
        return sum(score * weights[key] for key, score in scores.items()), scores
    
    # Iterate through GSTR2B entries
    for idx, gstr_row in gstr2b.iterrows():
        if gstr_row['matched']:
            continue
            
        # Find potential matching Tally entries with fuzzy date matching
        date_mask = abs((tally['date'] - gstr_row['date']).dt.days) <= match_config['date_window']
        amount_mask = abs(tally['amount'] - gstr_row['amount']) <= match_config['amount_tolerance']
        unmatched_mask = ~tally['matched']
        
        potential_matches = tally[date_mask & amount_mask & unmatched_mask]
        
        if not potential_matches.empty:
            print(f"\nFound potential matches for GSTR2B entry:")
            print(f"GSTR2B: Date={gstr_row['date']}, Amount={gstr_row['amount']}, Vendor={gstr_row['vendor']}")
            
            # Calculate match scores for all potential matches
            best_match = None
            best_score = 0
            best_details = None
            
            for _, tally_row in potential_matches.iterrows():
                match_score, score_details = calculate_match_score(gstr_row, tally_row)
                print(f"\nPotential match:")
                print(f"Tally: Date={tally_row['date']}, Amount={tally_row['amount']}, Vendor={tally_row['vendor']}")
                print(f"Match scores: {score_details}")
                print(f"Overall score: {match_score:.2f}")
                
                if match_score > best_score:
                    best_score = match_score
                    best_match = tally_row
                    best_details = score_details
            
            # If we found a good match
            if best_score >= 0.8:  # Minimum threshold for a match
                print(f"\nAccepted match with score {best_score:.2f}")
                reconciled.append({
                    'date': gstr_row['date'],
                    'amount': gstr_row['amount'],
                    'vendor': gstr_row['vendor'],
                    'gstr2b_reference': str(gstr_row.get('reference', '')),
                    'tally_reference': str(best_match.get('reference', '')),
                    'gstr2b_index': gstr_row['gstr2b_index'],
                    'tally_index': best_match['tally_index'],
                    'match_score': best_score,
                    'match_details': best_details
                })
                
                # Mark as matched
                gstr2b.loc[gstr2b['gstr2b_index'] == gstr_row['gstr2b_index'], 'matched'] = True
                tally.loc[tally['tally_index'] == best_match['tally_index'], 'matched'] = True
    
    # Convert reconciled list to DataFrame
    reconciled_df = pd.DataFrame(reconciled)
    
    # Get unmatched transactions
    unmatched_gstr2b = gstr2b[~gstr2b['matched']].copy()
    unmatched_tally = tally[~tally['matched']].copy()
    
    # Clean up temporary columns
    for df in [reconciled_df, unmatched_gstr2b, unmatched_tally]:
        if not df.empty:
            df.drop(columns=['gstr2b_index', 'tally_index', 'matched'], errors='ignore', inplace=True)
    
    # Calculate match quality metrics
    if not reconciled_df.empty:
        match_scores = reconciled_df['match_score']
        metrics = {
            'total_matches': len(reconciled_df),
            'high_confidence': sum(match_scores >= 0.9),
            'medium_confidence': sum((match_scores >= 0.8) & (match_scores < 0.9)),
            'low_confidence': sum(match_scores < 0.8),
            'average_score': match_scores.mean(),
            'min_score': match_scores.min(),
            'max_score': match_scores.max()
        }
    else:
        metrics = {
            'total_matches': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'average_score': 0,
            'min_score': 0,
            'max_score': 0
        }
    
    # Print detailed summary
    print("\nReconciliation Summary:")
    print(f"Total GSTR2B entries: {len(gstr2b)}")
    print(f"Total Tally entries: {len(tally)}")
    print(f"Reconciled entries: {metrics['total_matches']}")
    print(f"- High confidence matches (>0.9): {metrics['high_confidence']}")
    print(f"- Medium confidence matches (0.8-0.9): {metrics['medium_confidence']}")
    print(f"- Low confidence matches (<0.8): {metrics['low_confidence']}")
    print(f"Average match score: {metrics['average_score']:.2f}")
    print(f"Unmatched GSTR2B entries: {len(unmatched_gstr2b)}")
    print(f"Unmatched Tally entries: {len(unmatched_tally)}")
    
    if len(reconciled_df) == 0:
        print("\nNo matches found. Sample entries for debugging:")
        print("\nGSTR2B Sample (first 3 entries):")
        print(gstr2b[['date', 'amount', 'vendor']].head(3))
        print("\nTally Sample (first 3 entries):")
        print(tally[['date', 'amount', 'vendor']].head(3))
    
    return {
        'reconciled': reconciled_df.to_dict(orient="records"),
        'unmatched_bank': unmatched_gstr2b.to_dict(orient="records"),
        'unmatched_ledger': unmatched_tally.to_dict(orient="records"),
        'metrics': metrics,
        'duplicates': {
            'gstr2b': gstr2b_dupes,
            'tally': tally_dupes
        }
    }
