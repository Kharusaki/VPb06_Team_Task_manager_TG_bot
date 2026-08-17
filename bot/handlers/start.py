import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.config import BASE_DIR

router = Router()
WELCOME_IMAGE = BASE_DIR / "assets" / "welcome.png"


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = message.from_user.first_name or "Команда"

    caption = (
        f"Привет, {name}! Я — TaskBot.\n\n"
        "Собираю задачи всей команды в одном месте.\n"
        "Создавай, делегируй, отслеживай — всё через Telegram.\n\n"
        "Быстрый старт:\n"
        "/add — создать задачу\n"
        "/list — посмотреть все задачи\n"
        "/select_task — выбрать задачу для редактирования\n"
        "/help — полный список команд"
    )

    if WELCOME_IMAGE.exists():
        try:
            photo = FSInputFile(str(WELCOME_IMAGE))
            await message.answer_photo(photo=photo, caption=caption)
            return
        except Exception as e:
            logging.warning("Не удалось отправить приветственное фото: %s", e)

    await message.answer(caption)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено. Готов к работе.")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "Справка по командам бота\n\n"
        "Основные:\n"
        "/start — приветствие и подсказка\n"
        "/add — добавить новую задачу\n"
        "/list — показать все задачи\n"
        "/list_csv — скачать CSV-файл со всеми задачами\n"
        "/select_task — выбрать задачу из списка для редактирования\n"
        "/cancel — отменить текущее действие\n\n"
        "Для выбранной задачи (сначала выполните /select_task):\n"
        "/edit_name — изменить название\n"
        "/add_description — добавить или заменить описание\n"
        "/set_duedate — установить/отредактировать плановый срок\n"
        "/set_incharge — назначить/заменить исполнителя\n"
        "/set_priority — установить приоритет (Высокий/Средний/Низкий)\n"
        "/edit_status — изменить статус\n"
        "   Не начата -> В работе -> На проверке -> Доработка -> Выполнена\n"
        "/comment — оставить комментарий для заказчика\n"
        "/view_comments — посмотреть все комментарии\n"
        "/set_done — закрыть задачу (авто-таймстемп + исполнитель)\n"
        "/delete_task — удалить задачу из базы\n\n"
        "Поток работы:\n"
        "1. Создайте задачу: /add\n"
        "2. Выберите её: /select_task\n"
        "3. Редактируйте через команды выше"
    )
