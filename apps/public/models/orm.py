"""
SQLAlchemy ORM models for Atlas declarative schema management.

These models define the database schema. Atlas introspects these
to generate and apply database migrations.
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class ABTest(Base):
    """A/B test configuration table."""

    __tablename__ = 'a_b_tests'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String, nullable=False)
    description = Column(String)
    element_selector = Column(String, nullable=False)  # CSS selector for target element
    is_active = Column(Boolean, nullable=False, default=False)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))
    modified = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    # Relationship to variants
    variants = relationship('ABTestVariant', back_populates='test', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ABTest(id={self.id}, name={self.name}, is_active={self.is_active})>'


class ABTestVariant(Base):
    """A/B test variant (one possible version)."""

    __tablename__ = 'a_b_test_variants'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    a_b_test_id = Column(UUID(as_uuid=True), ForeignKey('a_b_tests.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Variant A", "Variant B"
    content = Column(JSONB, nullable=False)  # Stores HTML and other variant data
    traffic_allocation_percent = Column(Integer, nullable=False, default=0)
    is_control = Column(Boolean, nullable=False, default=False)
    created = Column(DateTime(timezone=True), nullable=False, server_default=text('now()'))

    # Relationship to test
    test = relationship('ABTest', back_populates='variants')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'traffic_allocation_percent BETWEEN 0 AND 100',
            name='ck_traffic_allocation'
        ),
    )

    def __repr__(self):
        return f'<ABTestVariant(id={self.id}, name={self.name}, traffic_allocation={self.traffic_allocation_percent}%)>'
