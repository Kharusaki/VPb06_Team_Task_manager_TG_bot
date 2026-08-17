from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.db.database import Database
from bot.states.states import AddTask
from bot.utils.csv_export import generate_tasks_csv
from bot.utils.fmt import fmt_timestamp

router = Router()
db = Database()


@router.message(F.text == "/add")
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(AddTask.waiting_title)
    await message.answer("Введите название задачи:")


@router.message(AddTask.waiting_title)
async def process_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return
    await state.update_data(title=title)
    await state.set_state(AddTask.waiting_description)
    await message.answer("Введите описание задачи (или отправьте — чтобы пропустить):")


@router.message(AddTask.waiting_description)
async def process_description(message: Message, state: FSMContext) -> None:
    description = "" if message.text.strip() == "—" else message.text.strip()
    await state.update_data(description=description)
    await state.set_state(AddTask.waiting_planned_date)
    await message.answer(
        "Укажите плановый срок (ДД.ММ.ГГГГ) или отправьте — чтобы пропустить:"
    )


@router.message(AddTask.waiting_planned_date)
async def process_planned_date(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    planned_date = None

    if text != "—":
        from datetime import datetime

        try:
            parsed = datetime.strptime(text, "%d.%m.%Y")
            planned_date = parsed.isoformat()
        except ValueError:
            await message.answer(
                "Неверный формат даты. Используйте ДД.ММ.ГГГГ или отправьте —:"
            )
            return

    data = await state.get_data()

    if data.get("_editing_deadline"):
        task_id = data["task_id"]
        db.update_planned_date(task_id, planned_date)
        await state.clear()
        from bot.handlers.edit import _format_task
        task = db.get_task_by_id(task_id)
        if task:
            from bot.keyboards.inline import get_task_actions_keyboard
            await message.answer(
                _format_task(task), reply_markup=get_task_actions_keyboard(task_id)
            )
        return

    task_id = db.add_task(
        title=data["title"],
        description=data["description"],
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.first_name or "",
        planned_end_date=planned_date,
    )
    await state.clear()

    deadline_info = f"\nСрок: {text}" if planned_date else ""
    await message.answer(
        f"Задача #{task_id} создана!\n\n"
        f"Название: {data['title']}\n"
        f"Описание: {data['description'] or '—'}"
        f"{deadline_info}"
    )


@router.message(F.text == "/list")
async def cmd_list(message: Message) -> None:
    tasks = db.get_all_tasks()
    if not tasks:
        await message.answer("Пока нет задач. Добавьте первую: /add")
        return

    status_icons = {
        "Не начата": "⬜",
        "В работе": "🔵",
        "На проверке": "🟡",
        "Доработка": "🟠",
        "Выполнена": "✅",
    }
    priority_icons = {
        "Высокий": "🔴",
        "Средний": "🟡",
        "Низкий": "🟢",
    }

    lines = []
    for t in tasks:
        icon = status_icons.get(t["status"], "❓")
        p_icon = priority_icons.get(t["priority"], "")
        assignee = t.get("assigned_to_name") or "—"
        deadline = fmt_timestamp(t.get("planned_end_date"))
        lines.append(
            f"{icon} #{t['id']} | {p_icon} {t['priority']}\n"
            f"   {t['title']}\n"
            f"   Автор: @{t.get('username', '?')} | Исполнитель: {assignee}\n"
            f"   Срок: {deadline}\n"
        )

    text = "\n".join(lines)
    for chunk in _split_text(text):
        await message.answer(chunk)


@router.message(F.text == "/list_csv")
async def cmd_list_csv(message: Message) -> None:
    tasks = db.get_all_tasks()
    if not tasks:
        await message.answer("Пока нет задач для выгрузки.")
        return

    csv_data = generate_tasks_csv(tasks)
    file = BufferedInputFile(csv_data.read(), filename="tasks.csv")
    await message.answer_document(file, caption=f"Экспорт задач ({len(tasks)} шт.)")


def _split_text(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        idx = text.rfind("\n", 0, max_len)
        if idx == -1:
            idx = max_len
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")
    return chunks
