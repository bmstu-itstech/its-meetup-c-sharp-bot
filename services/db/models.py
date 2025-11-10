from datetime import datetime

from sqlalchemy import Column, BigInteger, DateTime, Text, Sequence, ForeignKey, Integer

from services.db.base import Base


class BaseModel(Base):
    __abstract__ = True

    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Registration(BaseModel):
    __tablename__ = "registrations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_chat_id     = Column(BigInteger, nullable=False)
    full_name        = Column(Text,      nullable=False)
    passport_series  = Column(Text,      nullable=False)
    passport_number  = Column(Text,      nullable=False)
    university       = Column(Text,      nullable=True)
    workplace        = Column(Text,      nullable=True)


class RegistrationRsvp(BaseModel):
    __tablename__ = "registrations_rsvp"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    registration_id = Column(ForeignKey("registrations.id", ondelete="CASCADE"), nullable=False)

    # status: registered | awaiting | confirmed | declined | waitlisted | invited | expired
    status                 = Column(Text,      nullable=False, default="registered")
    confirmation_deadline  = Column(DateTime,  nullable=True)
    confirmed_at           = Column(DateTime,  nullable=True)
    waitlist_position      = Column(Integer,   nullable=True)
    reminder_count         = Column(Integer,   nullable=False, default=0)


class UserConsent(BaseModel):
    __tablename__ = "user_consents"

    chat_id     = Column(BigInteger, primary_key=True)
    accepted_at = Column(DateTime,   nullable=False, default=datetime.utcnow)
