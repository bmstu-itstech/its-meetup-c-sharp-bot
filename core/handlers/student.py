import logging
import re

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import Message, ReplyKeyboardRemove, ParseMode, ChatType
from datetime import datetime

from core import texts
from core import states
from core.handlers import keyboards
from common.repository import dp
from services.db.storage import Storage
from config import config


logger = logging.getLogger(__name__)

DATA_FULL_NAME_KEY = "full_name"
DATA_PASSPORT_SERIES_KEY = "passport_series"
DATA_PASSPORT_NUMBER_KEY = "passport_number"
DATA_UNIVERSITY_KEY = "university"
DATA_WORKPLACE_KEY = "workplace"
DATA_REGISTRATION_ID_KEY = "registration_id"


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state="*", commands=["start"])
async def send_start(message: Message, state: FSMContext, store: Storage):
    await state.finish()
    if not await store.has_consent(message.chat.id):
        await message.answer(
            texts.registration.consent_text,
            reply_markup=keyboards.yes_no_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return await states.Registration.consent.set()
    existing = await store.last_registration_by_chat(message.chat.id)
    if existing:
        async with state.proxy() as data:
            data[DATA_REGISTRATION_ID_KEY] = int(existing.id)
        await message.answer(
            "\n".join([
                texts.registration.already_registered_intro,
                "",
                texts.registration.review(existing.full_name, existing.passport_series, existing.passport_number, existing.university, existing.workplace),
                "",
                texts.registration.edit_question
            ]),
            reply_markup=keyboards.yes_no_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        await states.Registration.start.set()
    else:
        await message.answer(
            texts.registration.intro,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML,
        )
        await ask_full_name(message)


async def ask_full_name(message: Message):
    await message.answer(
        texts.registration.ask_full_name,
        reply_markup=keyboards.back_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await states.Registration.input_full_name.set()


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.start)
async def handle_start_decision(message: Message, state: FSMContext):
    if message.text == texts.buttons.yes:
        return await ask_full_name(message)
    if message.text == texts.buttons.no:
        await state.finish()
        return await message.answer(texts.registration.edit_flow_cancelled)
    return await message.answer(texts.errors.invalid_input_button)


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.input_full_name)
async def handle_full_name(message: Message, state: FSMContext, store: Storage):
    if message.text == texts.buttons.back:
        await state.finish()
        return await send_start(message, state, store)
    words = [w for w in message.text.split() if w]
    if len(words) < 2:
        return await message.answer(texts.registration.invalid_full_name)
    normalized = []
    for word in words:
        if '-' in word:
            normalized.append('-'.join([w.capitalize() for w in word.split('-')]))
        else:
            normalized.append(word.capitalize())
    async with state.proxy() as data:
        data[DATA_FULL_NAME_KEY] = ' '.join(normalized)
    await ask_passport(message)


async def ask_passport(message: Message):
    await message.answer(
        texts.registration.ask_passport,
        reply_markup=keyboards.back_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await states.Registration.input_passport.set()


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.input_passport)
async def handle_passport(message: Message, state: FSMContext):
    if message.text == texts.buttons.back:
        return await ask_full_name(message)
    raw = message.text.replace(" ", "")
    if not re.fullmatch(r"\d{10}", raw):
        return await message.answer(texts.registration.invalid_passport, parse_mode=ParseMode.HTML)
    series, number = raw[:4], raw[4:]
    async with state.proxy() as data:
        data[DATA_PASSPORT_SERIES_KEY] = series
        data[DATA_PASSPORT_NUMBER_KEY] = number
    await ask_university(message)


async def ask_university(message: Message):
    await message.answer(
        texts.registration.ask_university,
        reply_markup=keyboards.back_or_skip_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await states.Registration.input_university.set()


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.input_university)
async def handle_university(message: Message, state: FSMContext):
    if message.text == texts.buttons.back:
        return await ask_passport(message)
    text = None if message.text == texts.buttons.skip else message.text.strip()
    async with state.proxy() as data:
        data[DATA_UNIVERSITY_KEY] = text
    await ask_workplace(message)


async def ask_workplace(message: Message):
    await message.answer(
        texts.registration.ask_workplace,
        reply_markup=keyboards.back_or_skip_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await states.Registration.input_workplace.set()


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.input_workplace)
async def handle_workplace(message: Message, state: FSMContext):
    if message.text == texts.buttons.back:
        return await ask_university(message)
    text = None if message.text == texts.buttons.skip else message.text.strip()
    async with state.proxy() as data:
        data[DATA_WORKPLACE_KEY] = text
        full_name = data[DATA_FULL_NAME_KEY]
        series = data[DATA_PASSPORT_SERIES_KEY]
        number = data[DATA_PASSPORT_NUMBER_KEY]
        university = data[DATA_UNIVERSITY_KEY]
        workplace = data[DATA_WORKPLACE_KEY]
    await message.answer(
        texts.registration.review(full_name, series, number, university, workplace),
        reply_markup=keyboards.yes_no_back_keyboard(),
        parse_mode=ParseMode.HTML,
    )
    await states.Registration.confirm.set()


@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.confirm)
async def handle_confirm(message: Message, state: FSMContext, store: Storage):
    if message.text == texts.buttons.back:
        return await ask_workplace(message)
    if message.text == texts.buttons.yes:
        async with state.proxy() as data:
            reg_id = data.get(DATA_REGISTRATION_ID_KEY)
            if reg_id:
                await store.update_registration(
                    int(reg_id),
                    full_name=data[DATA_FULL_NAME_KEY],
                    passport_series=data[DATA_PASSPORT_SERIES_KEY],
                    passport_number=data[DATA_PASSPORT_NUMBER_KEY],
                    university=data[DATA_UNIVERSITY_KEY],
                    workplace=data[DATA_WORKPLACE_KEY],
                )
            else:
                await store.save_registration(
                    user_chat_id=message.chat.id,
                    full_name=data[DATA_FULL_NAME_KEY],
                    passport_series=data[DATA_PASSPORT_SERIES_KEY],
                    passport_number=data[DATA_PASSPORT_NUMBER_KEY],
                    university=data[DATA_UNIVERSITY_KEY],
                    workplace=data[DATA_WORKPLACE_KEY],
                )
        await state.finish()
        await message.answer(texts.registration.registration_finished, reply_markup=ReplyKeyboardRemove())
        return
    if message.text == texts.buttons.no:
        await state.finish()
        await send_start(message, state, store)
        return
    await message.answer(texts.errors.invalid_input_button)

@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state=states.Registration.consent)
async def handle_consent(message: Message, state: FSMContext, store: Storage):
    if message.text == texts.buttons.yes:
        await store.save_consent(message.chat.id)
        await message.answer(
            texts.registration.intro,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode=ParseMode.HTML,
        )
        return await ask_full_name(message)
    if message.text == texts.buttons.no:
        return await message.answer(texts.registration.consent_required)
    return await message.answer(texts.errors.invalid_input_button)

@dp.message_handler(ChatTypeFilter(ChatType.PRIVATE), state="*")
async def handle_rsvp(message: Message, store: Storage):
    # Process RSVP yes/no if user is awaiting or invited
    if message.text not in (texts.buttons.yes, texts.buttons.no):
        return
    reg = await store.last_registration_by_chat(message.chat.id)
    if not reg:
        return
    rsvp = await store.ensure_rsvp(reg.id)
    if rsvp.status not in ("awaiting", "invited", "waitlisted"):
        return
    if message.text == texts.buttons.yes:
        confirmed = await store.count_confirmed()
        if confirmed < config.capacity:
            await store.update_rsvp(reg.id, status="confirmed", confirmed_at=datetime.utcnow())
            await message.answer(texts.registration.confirmed_ok, reply_markup=ReplyKeyboardRemove())
        else:
            pos = await store.max_waitlist_position() + 1
            await store.update_rsvp(reg.id, status="waitlisted", waitlist_position=pos)
            await message.answer(texts.registration.waitlisted_info.format(pos=pos), reply_markup=ReplyKeyboardRemove())
    else:
        await store.update_rsvp(reg.id, status="declined")
        await message.answer(texts.registration.declined_ok, reply_markup=ReplyKeyboardRemove())
        # Try invite next from waitlist
        nxt = await store.next_waitlist_candidate()
        if nxt:
            await store.update_rsvp(nxt.registration_id, status="invited")
            try:
                target_reg = await store.get_registration(nxt.registration_id)
                await message.bot.send_message(target_reg.user_chat_id, texts.registration.invited_from_waitlist, reply_markup=keyboards.yes_no_keyboard())
            except Exception:
                pass
