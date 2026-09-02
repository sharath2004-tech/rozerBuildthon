"""
Database connection module for PostgreSQL (Render).
Uses DATABASE_URL environment variable from Render PostgreSQL.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

# Get DATABASE_URL from Render PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
if DATABASE_URL:
    # Render provides postgres:// but SQLAlchemy 1.4+ needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Render free tier has connection limits
        echo=False,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    if engine is None:
        return
    
    # Create tables if they don't exist
    with engine.connect() as conn:
        # Recovery workflows table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recovery_workflows (
                id SERIAL PRIMARY KEY,
                payment_id VARCHAR(255) NOT NULL,
                customer_id VARCHAR(255) NOT NULL,
                amount_inr DECIMAL(10, 2) NOT NULL,
                rail VARCHAR(50),
                failure_code VARCHAR(50),
                disposition VARCHAR(50) NOT NULL,
                rule_id VARCHAR(100),
                reason TEXT,
                recovery_probability DECIMAL(5, 4),
                expected_value_inr DECIMAL(10, 2),
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Batch results table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS batch_results (
                id SERIAL PRIMARY KEY,
                batch_id VARCHAR(255) NOT NULL UNIQUE,
                total_payments INTEGER NOT NULL,
                auto_retried INTEGER DEFAULT 0,
                needs_approval INTEGER DEFAULT 0,
                blocked INTEGER DEFAULT 0,
                total_amount_inr DECIMAL(12, 2) NOT NULL,
                recovered_amount_inr DECIMAL(12, 2) DEFAULT 0,
                success_rate DECIMAL(5, 4) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """))
        
        # Payment logs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payment_logs (
                id SERIAL PRIMARY KEY,
                payment_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                status VARCHAR(50),
                amount_inr DECIMAL(10, 2),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Compliance stats table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS compliance_stats (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                total_decisions INTEGER DEFAULT 0,
                auto_approved INTEGER DEFAULT 0,
                human_approved INTEGER DEFAULT 0,
                auto_blocked INTEGER DEFAULT 0,
                override_rate DECIMAL(5, 4) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        """))
        
        conn.commit()


def health_check() -> dict:
    """Check database connection health."""
    if engine is None:
        return {"database": "not_configured", "status": "warning"}
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "connected", "status": "ok"}
    except Exception as e:
        return {"database": "error", "status": "error", "message": str(e)}
