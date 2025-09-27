from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import get_session, ReconciliationPeriod, Transaction, GSTR3BSummary

def get_or_create_period(session: Session, period_date: date) -> ReconciliationPeriod:
    """Get or create a reconciliation period for the given month"""
    # Convert to first day of the month
    period_start = date(period_date.year, period_date.month, 1)
    
    period = session.query(ReconciliationPeriod).filter(
        ReconciliationPeriod.period == period_start
    ).first()
    
    if not period:
        period = ReconciliationPeriod(
            period=period_start,
            status='in_progress'
        )
        session.add(period)
        session.commit()
    
    return period

def serialize_transaction_data(data: Dict) -> Dict:
    """Serialize transaction data for JSON storage."""
    serialized = {}
    for key, value in data.items():
        if isinstance(value, date):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized

def save_transaction_batch(
    session: Session,
    period: ReconciliationPeriod,
    transactions: List[Dict],
    source: str
) -> List[Transaction]:
    """Save a batch of transactions to the database"""
    saved_transactions = []
    
    for trans_data in transactions:
        # Check if transaction already exists
        existing = session.query(Transaction).filter(
            Transaction.period_id == period.id,
            Transaction.source == source,
            Transaction.invoice_number == trans_data.get('reference'),
            Transaction.vendor_gstin == trans_data.get('vendor'),
            Transaction.amount == trans_data.get('amount')
        ).first()
        
        if not existing:
            # Serialize the original data for JSON storage
            serialized_data = serialize_transaction_data(trans_data)
            
            transaction = Transaction(
                period_id=period.id,
                source=source,
                transaction_date=trans_data['date'],
                amount=trans_data['amount'],
                vendor_gstin=trans_data.get('vendor'),
                invoice_number=trans_data.get('reference'),
                original_data=serialized_data
            )
            session.add(transaction)
            saved_transactions.append(transaction)
    
    session.commit()
    return saved_transactions

def update_period_statistics(session: Session, period: ReconciliationPeriod):
    """Update reconciliation period statistics"""
    stats = {
        'total_transactions': session.query(Transaction).filter(
            Transaction.period_id == period.id
        ).count(),
        'matched_transactions': session.query(Transaction).filter(
            Transaction.period_id == period.id,
            Transaction.matched == True
        ).count(),
        'total_amount': session.query(Transaction).filter(
            Transaction.period_id == period.id
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0,
        'matched_amount': session.query(Transaction).filter(
            Transaction.period_id == period.id,
            Transaction.matched == True
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    }
    
    for key, value in stats.items():
        setattr(period, key, value)
    
    session.commit()

def save_gstr3b_summary(
    session: Session,
    period: ReconciliationPeriod,
    summary_data: Dict
) -> GSTR3BSummary:
    """Save GSTR3B summary data"""
    summary = GSTR3BSummary(
        period_id=period.id,
        return_period=period.period,  # Using the renamed column
        total_itc_available=summary_data.get('total_itc_available', 0),
        total_itc_claimed=summary_data.get('total_itc_claimed', 0),
        filing_status='draft',
        summary_data=summary_data
    )
    
    session.add(summary)
    session.commit()
    return summary

def get_period_summary(
    session: Session,
    period_date: Optional[date] = None,
    months_lookback: int = 3
) -> Dict:
    """Get reconciliation summary for recent periods"""
    if not period_date:
        period_date = datetime.now().date()
    
    # Get last n months of reconciliation data
    periods = session.query(ReconciliationPeriod).filter(
        ReconciliationPeriod.period <= period_date
    ).order_by(
        ReconciliationPeriod.period.desc()
    ).limit(months_lookback).all()
    
    summary = []
    for period in periods:
        gstr3b = period.gstr3b_summary[0] if period.gstr3b_summary else None
        
        period_summary = {
            'period': period.period.strftime('%B %Y'),
            'status': period.status,
            'total_transactions': period.total_transactions,
            'matched_transactions': period.matched_transactions,
            'match_rate': (period.matched_transactions / period.total_transactions * 100) if period.total_transactions else 0,
            'total_amount': period.total_amount,
            'matched_amount': period.matched_amount,
            'gstr3b_status': gstr3b.filing_status if gstr3b else 'not_filed',
            'itc_claimed': gstr3b.total_itc_claimed if gstr3b else 0,
            'filing_date': gstr3b.filed_date.strftime('%Y-%m-%d') if gstr3b and gstr3b.filed_date else None
        }
        summary.append(period_summary)
    
    return {
        'periods': summary,
        'total_pending_matches': session.query(Transaction).filter(
            Transaction.matched == False
        ).count(),
        'total_pending_claims': session.query(Transaction).filter(
            Transaction.matched == True,
            Transaction.claim_status == 'pending'
        ).count()
    }