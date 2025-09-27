import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import os

from ..database import Base, ReconciliationPeriod, Transaction, GSTR3BSummary

# Use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def engine():
    """Create a fresh database engine for each test."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def session(engine):
    """Create a new session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_reconciliation_period_creation(session):
    """Test creating a reconciliation period."""
    period = ReconciliationPeriod(
        period=date(2025, 9, 1),
        status='in_progress'
    )
    session.add(period)
    session.commit()

    # Verify the period was created
    saved_period = session.query(ReconciliationPeriod).first()
    assert saved_period.period == date(2025, 9, 1)
    assert saved_period.status == 'in_progress'

def test_transaction_relationships(session):
    """Test relationships between transactions and reconciliation period."""
    # Create a period
    period = ReconciliationPeriod(
        period=date(2025, 9, 1),
        status='in_progress'
    )
    session.add(period)
    
    # Create two transactions
    gstr2b_trans = Transaction(
        period_id=1,
        source='gstr2b',
        transaction_date=date(2025, 9, 15),
        amount=1000.0,
        vendor_gstin='27AAAAA0000A1Z5',
        invoice_number='INV001'
    )
    
    tally_trans = Transaction(
        period_id=1,
        source='tally',
        transaction_date=date(2025, 9, 15),
        amount=1000.0,
        vendor_gstin='27AAAAA0000A1Z5',
        invoice_number='INV001'
    )
    
    session.add(gstr2b_trans)
    session.add(tally_trans)
    session.commit()

    # Verify relationships
    assert len(period.transactions) == 2
    assert period.transactions[0].source in ['gstr2b', 'tally']
    assert period.transactions[1].source in ['gstr2b', 'tally']

def test_gstr3b_relationship(session):
    """Test relationship between reconciliation period and GSTR3B summary."""
    # Create a period
    period = ReconciliationPeriod(
        period=date(2025, 9, 1),
        status='in_progress'
    )
    session.add(period)
    
    # Create GSTR3B summary
    gstr3b = GSTR3BSummary(
        period_id=1,
        return_period=date(2025, 9, 1),
        total_itc_available=5000.0,
        total_itc_claimed=4000.0,
        filing_status='draft',
        summary_data={
            'details': [
                {'section': 'ITC Available', 'amount': 5000.0},
                {'section': 'ITC Claimed', 'amount': 4000.0}
            ]
        }
    )
    session.add(gstr3b)
    session.commit()

    # Verify relationships
    assert len(period.gstr3b_summary) == 1
    assert period.gstr3b_summary[0].total_itc_available == 5000.0
    assert period.gstr3b_summary[0].total_itc_claimed == 4000.0
    assert period.gstr3b_summary[0].period_rel.period == date(2025, 9, 1)

def test_match_tracking(session):
    """Test tracking matched transactions."""
    # Create a period
    period = ReconciliationPeriod(
        period=date(2025, 9, 1),
        status='in_progress'
    )
    session.add(period)
    
    # Create two transactions that match
    gstr2b_trans = Transaction(
        period_id=1,
        source='gstr2b',
        transaction_date=date(2025, 9, 15),
        amount=1000.0,
        vendor_gstin='27AAAAA0000A1Z5',
        invoice_number='INV001',
        matched=True
    )
    
    tally_trans = Transaction(
        period_id=1,
        source='tally',
        transaction_date=date(2025, 9, 15),
        amount=1000.0,
        vendor_gstin='27AAAAA0000A1Z5',
        invoice_number='INV001',
        matched=True,
        matched_with_id=1
    )
    
    session.add(gstr2b_trans)
    session.add(tally_trans)
    session.commit()

    # Verify match tracking
    tally_transaction = session.query(Transaction).filter_by(source='tally').first()
    assert tally_transaction.matched == True
    assert tally_transaction.matched_with_id == gstr2b_trans.id
    assert tally_transaction.matched_with.source == 'gstr2b'