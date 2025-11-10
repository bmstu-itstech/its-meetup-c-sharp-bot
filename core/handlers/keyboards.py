from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from core import texts


def yes_no_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton(texts.buttons.yes),
        KeyboardButton(texts.buttons.no),
    )
    return keyboard


def skip_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(KeyboardButton(texts.buttons.skip))
    return keyboard


def back_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    keyboard.add(KeyboardButton(texts.buttons.back))
    return keyboard


def back_or_skip_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        KeyboardButton(texts.buttons.back),
        KeyboardButton(texts.buttons.skip),
    )
    return keyboard


def yes_no_back_keyboard() -> types.ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    keyboard.add(
        KeyboardButton(texts.buttons.yes),
        KeyboardButton(texts.buttons.no),
        KeyboardButton(texts.buttons.back),
    )
    return keyboard
