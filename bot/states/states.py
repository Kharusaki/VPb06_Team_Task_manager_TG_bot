from aiogram.fsm.state import State, StatesGroup


class AddTask(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_planned_date = State()


class SelectTask(StatesGroup):
    choosing = State()


class EditName(StatesGroup):
    waiting_new_title = State()


class AddDescription(StatesGroup):
    waiting_new_description = State()


class SetDueDate(StatesGroup):
    waiting_date = State()


class SetInCharge(StatesGroup):
    waiting_user = State()


class SetPriority(StatesGroup):
    choosing = State()


class EditStatus(StatesGroup):
    choosing = State()


class CommentTask(StatesGroup):
    waiting_text = State()
