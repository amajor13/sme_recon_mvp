from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class ReconciliationPeriod(Base):
    """Tracks reconciliation sessions for each month"""
    __tablename__ = 'reconciliation_periods'
    
    id = Column(Integer, primary_key=True)
    period = Column(Date, nullable=False)  # First day of the month
    status = Column(String, nullable=False)  # 'in_progress', 'completed', 'filed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statistics and summary
    total_transactions = Column(Integer, default=0)
    matched_transactions = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    matched_amount = Column(Float, default=0.0)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="period")
    gstr3b_summary = relationship("GSTR3BSummary", back_populates="period_rel")

from datetime import date

def serialize_date(dt):
    """Convert date objects to string format."""
    return dt.isoformat() if isinstance(dt, date) else dt

class Transaction(Base):
    """Stores all transactions (both GSTR2B and Tally)"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('reconciliation_periods.id'))
    source = Column(String, nullable=False)  # 'gstr2b' or 'tally'
    transaction_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    vendor_gstin = Column(String)
    invoice_number = Column(String)
    original_data = Column(JSON)  # Store original row data
    
    # Matching information
    matched = Column(Boolean, default=False)
    matched_with_id = Column(Integer, ForeignKey('transactions.id'), nullable=True)
    match_score = Column(Float)
    match_details = Column(JSON)  # Store detailed match scoring
    
    # GSTR3B claim tracking
    claimed_in_period = Column(Date, nullable=True)
    claim_status = Column(String)  # 'pending', 'claimed', 'disputed'
    
    # Relationships
    period = relationship("ReconciliationPeriod", back_populates="transactions")
    matched_with = relationship("Transaction", remote_side=[id])

class GSTR3BSummary(Base):
    """Stores GSTR3B return summaries"""
    __tablename__ = 'gstr3b_summaries'
    
    id = Column(Integer, primary_key=True)
    period_id = Column(Integer, ForeignKey('reconciliation_periods.id'))
    return_period = Column(Date, nullable=False)  # Return period (renamed from period to avoid confusion)
    total_itc_available = Column(Float)
    total_itc_claimed = Column(Float)
    filing_status = Column(String)  # 'draft', 'filed'
    filed_date = Column(DateTime)
    summary_data = Column(JSON)  # Store complete GSTR3B summary
    
    # Relationships
    period_rel = relationship("ReconciliationPeriod", back_populates="gstr3b_summary")

# Database connection and session management
DATABASE_URL = "sqlite:///./reconciliation.db"
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize database
init_db()