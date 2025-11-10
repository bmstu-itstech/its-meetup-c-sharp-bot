import logging

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from services.db import models

logger = logging.getLogger(__name__)


class RegistrationNotFoundException(Exception):
    def __init__(self, registration_id: int):
        super().__init__(f"registration not found: {registration_id}")


class Storage:
    _db: AsyncSession

    def __init__(self, conn: AsyncSession):
        self._db = conn

    async def save_registration(
        self,
        *,
        user_chat_id: int,
        full_name: str,
        passport_series: str,
        passport_number: str,
        university: str | None,
        workplace: str | None,
    ) -> int:
        model = models.Registration(
            user_chat_id=user_chat_id,
            full_name=full_name,
            passport_series=passport_series,
            passport_number=passport_number,
            university=university,
            workplace=workplace,
        )
        self._db.add(model)
        await self._db.commit()
        await self._db.refresh(model)
        logger.info(f"Saved registration for chat id {user_chat_id}")
        return int(model.id)

    async def get_registration(self, registration_id: int) -> models.Registration:
        stmt = select(models.Registration).filter_by(id=registration_id)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise RegistrationNotFoundException(registration_id)
        return model

    async def list_registrations(self) -> list[models.Registration]:
        stmt = select(models.Registration).order_by(models.Registration.created_on.desc())
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def update_registration(
        self,
        registration_id: int,
        *,
        full_name: str,
        passport_series: str,
        passport_number: str,
        university: str | None,
        workplace: str | None,
    ) -> None:
        model = await self.get_registration(registration_id)
        model.full_name = full_name
        model.passport_series = passport_series
        model.passport_number = passport_number
        model.university = university
        model.workplace = workplace
        await self._db.commit()

    async def last_registration_by_chat(self, chat_id: int) -> models.Registration | None:
        stmt = select(models.Registration).filter_by(user_chat_id=chat_id).order_by(models.Registration.created_on.desc())
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def count_registrations(self) -> int:
        stmt = select(func.count(models.Registration.id))
        result = await self._db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def clear_registrations(self) -> None:
        await self._db.execute(delete(models.Registration))
        await self._db.commit()

    # RSVP methods
    async def get_rsvp(self, registration_id: int) -> models.RegistrationRsvp | None:
        stmt = select(models.RegistrationRsvp).filter_by(registration_id=registration_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_rsvp(self, registration_id: int) -> models.RegistrationRsvp:
        rsvp = await self.get_rsvp(registration_id)
        if rsvp:
            return rsvp
        rsvp = models.RegistrationRsvp(registration_id=registration_id, status="registered")
        self._db.add(rsvp)
        await self._db.commit()
        await self._db.refresh(rsvp)
        return rsvp

    async def update_rsvp(
        self,
        registration_id: int,
        *,
        status: str | None = None,
        confirmation_deadline = None,
        confirmed_at = None,
        waitlist_position: int | None = None,
        reminder_count: int | None = None,
    ) -> models.RegistrationRsvp:
        rsvp = await self.ensure_rsvp(registration_id)
        if status is not None:
            rsvp.status = status
        if confirmation_deadline is not None:
            rsvp.confirmation_deadline = confirmation_deadline
        if confirmed_at is not None:
            rsvp.confirmed_at = confirmed_at
        if waitlist_position is not None:
            rsvp.waitlist_position = waitlist_position
        if reminder_count is not None:
            rsvp.reminder_count = reminder_count
        await self._db.commit()
        return rsvp

    async def count_confirmed(self) -> int:
        stmt = select(func.count(models.RegistrationRsvp.id)).filter_by(status="confirmed")
        result = await self._db.execute(stmt)
        return int(result.scalar_one() or 0)

    async def max_waitlist_position(self) -> int:
        stmt = select(func.max(models.RegistrationRsvp.waitlist_position))
        result = await self._db.execute(stmt)
        value = result.scalar_one()
        return int(value or 0)

    async def next_waitlist_candidate(self) -> models.RegistrationRsvp | None:
        stmt = select(models.RegistrationRsvp).where(
            models.RegistrationRsvp.status == "waitlisted"
        ).order_by(models.RegistrationRsvp.waitlist_position.asc()).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    # Consent
    async def has_consent(self, chat_id: int) -> bool:
        stmt = select(models.UserConsent).filter_by(chat_id=chat_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def save_consent(self, chat_id: int) -> None:
        exists = await self.has_consent(chat_id)
        if exists:
            return
        self._db.add(models.UserConsent(chat_id=chat_id))
        await self._db.commit()
