from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import Database
from bot.utils.fmt import fmt_timestamp
from bot.states.states import (
    SelectTask,
    EditName,
    AddDescription,
    SetDueDate,
    SetInCharge,
    SetPriority,
    EditStatus,
    CommentTask,
)
from bot.keyboards.inline import get_task_selection_keyboard

router = Router()
db = Database()


def _format_task(t: dict) -> str:
    status_icons = {
        "Не начата": "⬜",
        "В работе": "🔵",
        "На проверке": "🟡",
        "Доработка": "🟠",
        "Выполнена": "✅",
    }
    priority_icons = {"Высокий": "🔴", "Средний": "🟡", "Низкий": "🟢"}

    icon = status_icons.get(t["status"], "❓")
    p_icon = priority_icons.get(t["priority"], "")
    assignee = t.get("assigned_to_name") or "—"
    deadline = fmt_timestamp(t.get("planned_end_date"))
    closed_by = t.get("closed_by_name") or "—"
    comment_count = db.get_comment_count(t["id"])

    return (
        f"{icon} Задача #{t['id']} | {p_icon} {t['priority']}\n\n"
        f"Название: {t['title']}\n"
        f"Описание: {t.get('description') or '—'}\n\n"
        f"Статус: {t['status']}\n"
        f"Автор: @{t.get('username', '?')}\n"
        f"Исполнитель: {assignee}\n"
        f"Срок: {deadline}\n"
        f"Создано: {fmt_timestamp(t['created_at'])}\n"
        f"Завершено: {fmt_timestamp(t.get('completed_at'))}\n"
        f"Закрыл: {closed_by}\n"
        f"Комментарии: {comment_count}"
    )


async def _require_selected_task(message: Message, state: FSMContext) -> int | None:
    data = await state.get_data()
    task_id = data.get("selected_task_id")
    if not task_id:
        await message.answer(
            "Сначала выберите задачу: /select_task"
        )
        return None
    task = db.get_task_by_id(task_id)
    if not task:
        await state.update_data(selected_task_id=None)
        await message.answer(
            "Задача не найдена. Выберите заново: /select_task"
        )
        return None
    return task_id


@router.callback_query(F.data.startswith("select:"))
async def cb_select_task(callback: CallbackQuery, state: FSMContext) -> None:
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    await state.update_data(selected_task_id=task_id)
    await state.set_state(None)
    await callback.message.edit_text(
        f"Задача #{task_id} выбрана.\n\n{_format_task(task)}\n\n"
        "Теперь доступны команды:\n"
        "/edit_name — изменить название\n"
        "/add_description — добавить описание\n"
        "/set_duedate — установить срок\n"
        "/set_incharge — назначить исполнителя\n"
        "/set_priority — изменить приоритет\n"
        "/edit_status — изменить статус\n"
        "/comment — оставить комментарий\n"
        "/view_comments — посмотреть комментарии\n"
        "/set_done — закрыть задачу\n"
        "/delete_task — удалить задачу"
    )
    await callback.answer(f"Задача #{task_id} выбрана")


@router.message(F.text == "/select_task")
async def cmd_select_task(message: Message, state: FSMContext) -> None:
    tasks = db.get_all_tasks()
    if not tasks:
        await message.answer("Нет задач. Сначала создайте: /add")
        return

    await state.set_state(None)
    await message.answer(
        "Выберите задачу из списка:",
        reply_markup=get_task_selection_keyboard(tasks),
    )


@router.message(F.text == "/edit_name")
async def cmd_edit_name(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    await state.set_state(EditName.waiting_new_title)
    await message.answer(
        f"Текущее название: {task['title']}\n\nВведите новое название:"
    )


@router.message(EditName.waiting_new_title)
async def process_edit_name(message: Message, state: FSMContext) -> None:
    new_title = message.text.strip()
    if not new_title:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.update_task_title(task_id, new_title)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Название обновлено.\n\n{_format_task(task)}")


@router.message(F.text == "/add_description")
async def cmd_add_description(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    current = task.get("description") or "—"
    await state.set_state(AddDescription.waiting_new_description)
    await message.answer(
        f"Текущее описание: {current}\n\n"
        "Введите новое описание (или — чтобы очистить):"
    )


@router.message(AddDescription.waiting_new_description)
async def process_add_description(message: Message, state: FSMContext) -> None:
    new_desc = "" if message.text.strip() == "—" else message.text.strip()

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.update_task_description(task_id, new_desc)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Описание обновлено.\n\n{_format_task(task)}")


@router.message(F.text == "/set_duedate")
async def cmd_set_duedate(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    current = task.get("planned_end_date") or "—"
    await state.set_state(SetDueDate.waiting_date)
    await message.answer(
        f"Текущий срок: {current}\n\n"
        "Введите срок (ДД.ММ.ГГГГ) или — чтобы убрать:"
    )


@router.message(SetDueDate.waiting_date)
async def process_set_duedate(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    planned_date = None

    if text != "—":
        try:
            parsed = datetime.strptime(text, "%d.%m.%Y")
            planned_date = parsed.isoformat()
        except ValueError:
            await message.answer(
                "Неверный формат. Используйте ДД.ММ.ГГГГ или —:"
            )
            return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.update_planned_date(task_id, planned_date)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Срок обновлён.\n\n{_format_task(task)}")


@router.message(F.text == "/set_incharge")
async def cmd_set_incharge(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    current = task.get("assigned_to_name") or "—"
    await state.set_state(SetInCharge.waiting_user)
    await message.answer(
        f"Текущий исполнитель: {current}\n\n"
        "Введите @username или ID пользователя:"
    )


@router.message(SetInCharge.waiting_user)
async def process_set_incharge(message: Message, state: FSMContext) -> None:
    text = message.text.strip()

    if text.startswith("@"):
        assigned_name = text
        assigned_id = 0
    else:
        try:
            assigned_id = int(text)
            assigned_name = text
        except ValueError:
            await message.answer(
                "Некорректный формат. Введите @username или числовой ID:"
            )
            return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.delegate_task(task_id, assigned_id, assigned_name)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Исполнитель обновлён.\n\n{_format_task(task)}")


@router.message(F.text == "/set_priority")
async def cmd_set_priority(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    await state.set_state(SetPriority.choosing)
    await message.answer(
        f"Текущий приоритет: {task['priority']}\n\n"
        "Выберите новый приоритет:\n"
        "1 — Высокий\n"
        "2 — Средний\n"
        "3 — Низкий\n\n"
        "Введите номер или название:"
    )


@router.message(SetPriority.choosing)
async def process_set_priority(message: Message, state: FSMContext) -> None:
    mapping = {
        "1": "Высокий",
        "2": "Средний",
        "3": "Низкий",
        "высокий": "Высокий",
        "средний": "Средний",
        "низкий": "Низкий",
    }
    text = message.text.strip().lower()
    priority = mapping.get(text)
    if not priority:
        await message.answer(
            "Некорректный ввод. Введите 1/2/3 или название приоритета:"
        )
        return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.update_task_priority(task_id, priority)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Приоритет обновлён.\n\n{_format_task(task)}")


@router.message(F.text == "/edit_status")
async def cmd_edit_status(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    await state.set_state(EditStatus.choosing)
    await message.answer(
        f"Текущий статус: {task['status']}\n\n"
        "Выберите новый статус:\n"
        "1 — Не начата\n"
        "2 — В работе\n"
        "3 — На проверке\n"
        "4 — Доработка\n"
        "5 — Выполнена\n\n"
        "Введите номер или название:"
    )


@router.message(EditStatus.choosing)
async def process_edit_status(message: Message, state: FSMContext) -> None:
    mapping = {
        "1": "Не начата",
        "2": "В работе",
        "3": "На проверке",
        "4": "Доработка",
        "5": "Выполнена",
        "не начата": "Не начата",
        "в работе": "В работе",
        "на проверке": "На проверке",
        "доработка": "Доработка",
        "выполнена": "Выполнена",
    }
    text = message.text.strip().lower()
    status = mapping.get(text)
    if not status:
        await message.answer(
            "Некорректный ввод. Введите 1-5 или название статуса:"
        )
        return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    db.update_task_status(task_id, status)

    if status == "Выполнена":
        user_name = message.from_user.username or message.from_user.first_name
        db.set_completed_by(task_id, user_name)

    await state.set_state(None)
    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(f"Статус обновлён.\n\n{_format_task(task)}")


@router.message(F.text == "/set_done")
async def cmd_set_done(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return

    user_name = message.from_user.username or message.from_user.first_name
    db.update_task_status(task_id, "Выполнена")
    db.set_completed_by(task_id, user_name)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(
            f"Задача #{task_id} закрыта как выполненная.\n\n{_format_task(task)}"
        )


@router.message(F.text == "/comment")
async def cmd_comment(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return
    task = db.get_task_by_id(task_id)
    await state.set_state(CommentTask.waiting_text)
    await message.answer(
        f"Задача #{task_id}: {task['title']}\n\n"
        "Введите комментарий для заказчика задачи:"
    )


@router.message(CommentTask.waiting_text)
async def process_comment(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text:
        await message.answer("Комментарий не может быть пустым. Попробуйте ещё раз:")
        return

    data = await state.get_data()
    task_id = data["selected_task_id"]
    user_name = message.from_user.username or message.from_user.first_name

    db.add_comment(
        task_id=task_id,
        user_id=message.from_user.id,
        username=user_name,
        text=text,
    )
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        await message.answer(
            f"Комментарий добавлен к задаче #{task_id}.\n\n{_format_task(task)}"
        )


@router.message(F.text == "/view_comments")
async def cmd_view_comments(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return

    comments = db.get_comments_by_task(task_id)
    task = db.get_task_by_id(task_id)
    task_title = task["title"] if task else f"#{task_id}"

    if not comments:
        await message.answer(f"Задача {task_title}: комментариев пока нет.")
        return

    lines = [f"Комментарии к задаче {task_title}:\n"]
    for c in comments:
        ts = fmt_timestamp(c["created_at"])
        lines.append(f"@{c['username']} [{ts}]:\n{c['text']}\n")

    for chunk in _split_text("\n".join(lines)):
        await message.answer(chunk)


@router.message(F.text == "/delete_task")
async def cmd_delete_task(message: Message, state: FSMContext) -> None:
    task_id = await _require_selected_task(message, state)
    if not task_id:
        return

    task = db.get_task_by_id(task_id)
    db.delete_task(task_id)
    await state.update_data(selected_task_id=None)

    title = task["title"] if task else f"#{task_id}"
    await message.answer(f"Задача {title} удалена.")


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
