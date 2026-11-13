"""
AlphaWatch AI — Database Models (SQLAlchemy ORM)
ASTRAQUANT X 2026

Enforces:
  - Strict user separation (Every user owns only their records)
  - Cascading deletes on account deletion (Right to Erasure compliance)
  - Secure audit timestamps
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """Registered application user entity."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Account lockout fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Cascading deletes purge all user data if the account is erased
    holdings: Mapped[List["Holding"]] = relationship(
        "Holding", back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    paper_trades: Mapped[List["PaperTrade"]] = relationship(
        "PaperTrade", back_populates="user", cascade="all, delete-orphan"
    )


class Holding(Base):
    """User portfolio stock position."""
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    buy_price: Mapped[float] = mapped_column(Float, nullable=False)
    buy_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="holdings")


class UserProfile(Base):
    """Investor pattern, risk profiling answers, and adaptive rule diagnostics."""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    # Core Questionnaire Responses
    goal: Mapped[str] = mapped_column(String(100), default="Wealth Creation")
    horizon: Mapped[str] = mapped_column(String(50), default="3-5 Years")
    experience: Mapped[str] = mapped_column(String(50), default="Intermediate")
    trading_frequency: Mapped[str] = mapped_column(String(50), default="Monthly")
    fall_reaction: Mapped[str] = mapped_column(String(100), default="Hold and observe")
    savings_share: Mapped[str] = mapped_column(String(50), default="10-25%")
    preferred_sectors: Mapped[str] = mapped_column(String(255), default="Technology, Financials")

    # Quantitative Profiler Diagnostics
    risk_score: Mapped[float] = mapped_column(Float, default=50.0)
    suggested_profile: Mapped[str] = mapped_column(String(50), default="Moderate")  # Conservative, Moderate, Aggressive
    diversification_score: Mapped[float] = mapped_column(Float, default=50.0)
    concentration_status: Mapped[str] = mapped_column(String(100), default="Balanced")
    holding_style: Mapped[str] = mapped_column(String(50), default="Swing / Medium Term")
    why_this_profile: Mapped[str] = mapped_column(Text, default="Derived from balanced risk-tolerance score and multi-asset exposure.")
    answers_json: Mapped[str] = mapped_column(Text, default="{}")

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class PaperTrade(Base):
    """Simulated virtual trade execution record."""
    __tablename__ = "paper_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY or SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    brokerage_stt: Mapped[float] = mapped_column(Float, default=0.0)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)
    trade_date: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="paper_trades")
