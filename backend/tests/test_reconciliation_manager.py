import pytest
from datetime import datetime, date
import pandas as pd
import numpy as np

from ..reconciliation_manager import (
    get_or_create_period,
    save_transaction_batch,
    update_period_statistics,
    save_gstr3b_summary,
    get_period_summary
)
from ..database import ReconciliationPeriod, Transaction, GSTR3BSummary

def test_get_or_create_period(session):
    """Test period creation and retrieval."""
    # Create a new period
    period = get_or_create_period(session, date(2025, 9, 15))
    assert period.period == date(2025, 9, 1)  # Should be first day of month
    assert period.status == 'in_progress'
    
    # Try getting the same period
    same_period = get_or_create_period(session, date(2025, 9, 20))
    assert same_period.id == period.id

def test_save_transaction_batch(session):
    """Test saving a batch of transactions."""
    period = get_or_create_period(session, date(2025, 9, 1))
    
    # Create sample transactions
    transactions = [
        {
            'date': date(2025, 9, 15),
            'amount': 1000.0,
            'vendor': '27AAAAA0000A1Z5',
            'reference': 'INV001'
        },
        {
            'date': date(2025, 9, 16),
            'amount': 2000.0,
            'vendor': '27BBBBB0000B1Z5',
            'reference': 'INV002'
        }
    ]
    
    # Save transactions
    saved = save_transaction_batch(session, period, transactions, 'gstr2b')
    assert len(saved) == 2
    
    # Verify transactions were saved
    db_transactions = session.query(Transaction).filter_by(period_id=period.id).all()
    assert len(db_transactions) == 2
    assert db_transactions[0].amount == 1000.0
    assert db_transactions[1].amount == 2000.0

def test_update_period_statistics(session):
    """Test updating period statistics."""
    period = get_or_create_period(session, date(2025, 9, 1))
    
    # Create some transactions
    transactions = [
        Transaction(
            period_id=period.id,
            source='gstr2b',
            transaction_date=date(2025, 9, 15),
            amount=1000.0,
            matched=True
        ),
        Transaction(
            period_id=period.id,
            source='tally',
            transaction_date=date(2025, 9, 15),
            amount=1000.0,
            matched=True
        ),
        Transaction(
            period_id=period.id,
            source='gstr2b',
            transaction_date=date(2025, 9, 16),
            amount=2000.0,
            matched=False
        )
    ]
    
    for trans in transactions:
        session.add(trans)
    session.commit()
    
    # Update statistics
    update_period_statistics(session, period)
    
    # Verify statistics
    assert period.total_transactions == 3
    assert period.matched_transactions == 2
    assert period.total_amount == 4000.0
    assert period.matched_amount == 2000.0

def test_gstr3b_summary_integration(session):
    """Test GSTR3B summary integration."""
    period = get_or_create_period(session, date(2025, 9, 1))
    
    # Create GSTR3B summary data
    summary_data = {
        'total_itc_available': 5000.0,
        'total_itc_claimed': 4000.0,
        'details': [
            {'section': 'ITC Available', 'amount': 5000.0},
            {'section': 'ITC Claimed', 'amount': 4000.0}
        ]
    }
    
    # Save summary
    summary = save_gstr3b_summary(session, period, summary_data)
    
    # Verify summary was saved
    assert summary.total_itc_available == 5000.0
    assert summary.total_itc_claimed == 4000.0
    assert summary.filing_status == 'draft'
    assert summary.period_rel.id == period.id

def test_period_summary_retrieval(session):
    """Test retrieving period summaries."""
    # Create multiple periods with data
    periods = []
    for month in [7, 8, 9]:  # July, August, September
        period = get_or_create_period(session, date(2025, month, 1))
        periods.append(period)
        
        # Add some transactions
        transactions = [
            Transaction(
                period_id=period.id,
                source='gstr2b',
                transaction_date=date(2025, month, 15),
                amount=1000.0,
                matched=True
            ),
            Transaction(
                period_id=period.id,
                source='tally',
                transaction_date=date(2025, month, 15),
                amount=1000.0,
                matched=False
            )
        ]
        
        for trans in transactions:
            session.add(trans)
        
        # Add GSTR3B summary
        summary = GSTR3BSummary(
            period_id=period.id,
            return_period=date(2025, month, 1),
            total_itc_available=5000.0,
            total_itc_claimed=4000.0,
            filing_status='draft'
        )
        session.add(summary)
    
    session.commit()
    
    # Update statistics for all periods
    for period in periods:
        update_period_statistics(session, period)
    
    # Get summary for last 3 months
    summary = get_period_summary(session, date(2025, 9, 30), months_lookback=3)
    
    # Verify summary
    assert len(summary['periods']) == 3
    assert summary['total_pending_matches'] > 0
    latest_period = summary['periods'][0]
    assert latest_period['period'] == 'September 2025'
    assert latest_period['total_transactions'] == 2
    assert latest_period['matched_transactions'] == 1