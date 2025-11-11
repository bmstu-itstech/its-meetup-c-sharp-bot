from aiogram.dispatcher.filters.state import State, StatesGroup


class Registration(StatesGroup):
    start = State()
    consent = State()
    input_full_name = State()
    input_is_student = State()
    input_study_group = State()
    input_passport = State()
    input_university = State()
    input_workplace = State()
    confirm = State()
