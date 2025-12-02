import io
import csv
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, InputFile, ParseMode
import asyncio
import os

from common.repository import dp
from services.db.storage import Storage
from core.filters.admin import AdminFilter
from config import config
from datetime import datetime, timedelta
from core import texts
from core.handlers import keyboards


@dp.message_handler(AdminFilter(), Command("export"), state="*")
async def export_registrations(message: Message, store: Storage):
    regs = await store.list_registrations()
    if not regs:
        return await message.answer("Пока нет регистраций.")

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "user_chat_id", "full_name", "passport_series", "passport_number", "university", "workplace", "created_on"])
    for r in regs:
        writer.writerow([
            r.id,
            r.user_chat_id,
            r.full_name,
            r.passport_series,
            r.passport_number,
            r.university or "",
            r.workplace or "",
            r.created_on.isoformat() if getattr(r, "created_on", None) else "",
        ])
    data = buffer.getvalue().encode("utf-8")
    file_obj = io.BytesIO(data)
    file_obj.seek(0)
    input_file = InputFile(file_obj, filename="registrations.csv")
    await message.answer_document(input_file, caption="Список регистраций")


@dp.message_handler(AdminFilter(), Command("start_rsvp"), state="*")
async def start_rsvp(message: Message, store: Storage):
    regs = await store.list_registrations()
    if not regs:
        return await message.answer("Нет регистраций.")
    deadline = datetime.utcnow() + timedelta(hours=config.rsvp_window_hours)
    sent = 0
    for r in regs:
        rsvp = await store.ensure_rsvp(r.id)
        if rsvp.status in ("confirmed", "declined"):
            continue
        await store.update_rsvp(r.id, status="awaiting", confirmation_deadline=deadline)
        try:
            await message.bot.send_message(r.user_chat_id, texts.registration.invite_rsvp, reply_markup=keyboards.yes_no_keyboard())
            sent += 1
        except Exception:
            continue
    await message.answer(f"RSVP запущен. Отправлено: {sent}. Дедлайн: {deadline.strftime('%d.%m %H:%M')}")


@dp.message_handler(AdminFilter(), Command("stats"), state="*")
async def stats(message: Message, store: Storage):
    confirmed = await store.count_confirmed()
    total = await store.count_registrations()
    await message.answer(f"Статистика:\nВсего регистраций: {total}\nПодтверждено: {confirmed}/{config.capacity}")


@dp.message_handler(AdminFilter(), Command("broadcast"), state="*")
async def broadcast(message: Message, store: Storage):
    text = message.get_args().strip()
    if not text:
        return await message.answer("Использование: /broadcast текст сообщения")
    chat_ids = await store.list_all_chat_ids()
    if not chat_ids:
        return await message.answer("Нет пользователей для рассылки.")
    sent = 0
    failed = 0
    for idx, chat_id in enumerate(chat_ids, start=1):
        try:
            await message.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            failed += 1
        if idx % 25 == 0:
            await asyncio.sleep(0.05)
    await message.answer(f"Рассылка завершена. Отправлено: {sent}, ошибок: {failed}.")


INSTRUCTION_TEXT = "\n".join((
    "Митап стартует уже через 2 часа: показываем, как добраться до места встречи, 345 аудитории Главного здания МГТУ",
    "",
    "Открывай видео, бери с собой отличное настроение, заряд концентрации и приготовься к насыщенному вечеру!",
    "",
    "Не забудь взять паспорт, если не являешься студентом МГТУ им. Н. Э. Баумана. Это нужно для входа на территорию Университета."
))


@dp.message_handler(AdminFilter(), Command("send_instruction"), state="*")
async def send_instruction(message: Message, store: Storage):
    # Resolve assets/instruction.MOV and optional preview file from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    video_path = os.path.join(project_root, "assets", "instruction.MOV")
    preview_path = os.path.join(project_root, "assets", "preview.jpg")
    if not os.path.exists(video_path):
        return await message.answer("Файл видео не найден. Поместите его в assets/instruction.MOV и повторите попытку.")
    chat_ids = await store.list_all_chat_ids()
    if not chat_ids:
        return await message.answer("Нет пользователей для рассылки.")
    await message.answer(f"Начинаю рассылку инструкции. Получателей: {len(chat_ids)}")
    try:
        kwargs = {
            "video": InputFile(video_path),
            "caption": INSTRUCTION_TEXT,
            "parse_mode": ParseMode.HTML,
        }
        if preview_path and os.path.exists(preview_path):
            kwargs["thumb"] = InputFile(preview_path)
        preview_msg = await message.bot.send_video(message.chat.id, **kwargs)
        file_id = preview_msg.video.file_id if getattr(preview_msg, "video", None) else None
        if not file_id:
            return await message.answer("Не удалось получить file_id видео. Проверьте файл и повторите попытку.")
    except Exception as e:
        return await message.answer(f"Ошибка загрузки видео: {e}")
    sent = 0
    failed = 0
    for idx, chat_id in enumerate(chat_ids, start=1):
        try:
            send_kwargs = {
                "video": file_id,
                "caption": INSTRUCTION_TEXT,
                "parse_mode": ParseMode.HTML,
            }
            if preview_path and os.path.exists(preview_path):
                send_kwargs["thumb"] = InputFile(preview_path)
            await message.bot.send_video(chat_id, **send_kwargs)
            sent += 1
        except Exception:
            failed += 1
        if idx % 20 == 0:
            await asyncio.sleep(0.1)
    await message.answer(f"Рассылка инструкции завершена. Отправлено: {sent}, ошибок: {failed}.")
