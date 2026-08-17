from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.db.database import Database
from bot.utils.fmt import fmt_timestamp
from bot.states.states import EditName, AddDescription, SetInCharge, AddTask
from bot.keyboards.inline import (
    get_task_actions_keyboard,
    get_status_keyboard,
    get_priority_keyboard,
    get_edit_keyboard,
    get_back_to_task_keyboard,
)

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


@router.callback_query(F.data.startswith("task:"))
async def cb_task_detail(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    text = _format_task(task)
    keyboard = get_task_actions_keyboard(task_id)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("status:"))
async def cb_status_menu(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    text = f"Выберите статус для задачи #{task_id}:\nТекущий: {task['status']}"
    await callback.message.edit_text(text, reply_markup=get_status_keyboard(task_id))
    await callback.answer()


@router.callback_query(F.data.startswith("set_status:"))
async def cb_set_status(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    task_id = int(parts[1])
    new_status = ":".join(parts[2:])

    db.update_task_status(task_id, new_status)

    if new_status == "Выполнена":
        user_name = callback.from_user.username or callback.from_user.first_name
        db.set_completed_by(task_id, user_name)

    task = db.get_task_by_id(task_id)
    if task:
        text = _format_task(task)
        await callback.message.edit_text(
            text, reply_markup=get_task_actions_keyboard(task_id)
        )
    await callback.answer(f"Статус изменён на: {new_status}")


@router.callback_query(F.data.startswith("priority:"))
async def cb_priority_menu(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    text = f"Выберите приоритет для задачи #{task_id}:\nТекущий: {task['priority']}"
    await callback.message.edit_text(text, reply_markup=get_priority_keyboard(task_id))
    await callback.answer()


@router.callback_query(F.data.startswith("set_priority:"))
async def cb_set_priority(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    task_id = int(parts[1])
    new_priority = parts[2]

    db.update_task_priority(task_id, new_priority)
    task = db.get_task_by_id(task_id)
    if task:
        text = _format_task(task)
        await callback.message.edit_text(
            text, reply_markup=get_task_actions_keyboard(task_id)
        )
    await callback.answer(f"Приоритет изменён на: {new_priority}")


@router.callback_query(F.data.startswith("edit:"))
async def cb_edit_menu(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    text = f"Редактирование задачи #{task_id}:\n{task['title']}"
    await callback.message.edit_text(text, reply_markup=get_edit_keyboard(task_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit_title:"))
async def cb_edit_title(callback: CallbackQuery, state: FSMContext) -> None:
    task_id = int(callback.data.split(":")[1])
    await state.set_state(EditName.waiting_new_title)
    await state.update_data(task_id=task_id)
    await callback.message.edit_text(
        "Введите новое название:",
        reply_markup=get_back_to_task_keyboard(task_id),
    )
    await callback.answer()


@router.message(EditName.waiting_new_title)
async def process_new_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_id = data.get("task_id") or data.get("selected_task_id")
    if not task_id:
        await state.clear()
        await message.answer("Задача не выбрана. Используйте /select_task")
        return

    new_title = message.text.strip()
    if not new_title:
        await message.answer("Название не может быть пустым. Попробуйте ещё раз:")
        return

    db.update_task_title(task_id, new_title)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        text = _format_task(task)
        await message.answer(text, reply_markup=get_task_actions_keyboard(task_id))


@router.callback_query(F.data.startswith("edit_desc:"))
async def cb_edit_desc(callback: CallbackQuery, state: FSMContext) -> None:
    task_id = int(callback.data.split(":")[1])
    await state.set_state(AddDescription.waiting_new_description)
    await state.update_data(task_id=task_id)
    await callback.message.edit_text(
        "Введите новое описание:",
        reply_markup=get_back_to_task_keyboard(task_id),
    )
    await callback.answer()


@router.message(AddDescription.waiting_new_description)
async def process_new_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_id = data.get("task_id") or data.get("selected_task_id")
    if not task_id:
        await state.clear()
        await message.answer("Задача не выбрана. Используйте /select_task")
        return

    new_desc = "" if message.text.strip() == "—" else message.text.strip()
    db.update_task_description(task_id, new_desc)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        text = _format_task(task)
        await message.answer(text, reply_markup=get_task_actions_keyboard(task_id))


@router.callback_query(F.data.startswith("delegate:"))
async def cb_delegate(callback: CallbackQuery, state: FSMContext) -> None:
    task_id = int(callback.data.split(":")[1])
    await state.set_state(SetInCharge.waiting_user)
    await state.update_data(task_id=task_id)
    await callback.message.edit_text(
        "Введите @username или ID пользователя, которому делегируется задача:",
        reply_markup=get_back_to_task_keyboard(task_id),
    )
    await callback.answer()


@router.message(SetInCharge.waiting_user)
async def process_delegate(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_id = data.get("task_id") or data.get("selected_task_id")
    if not task_id:
        await state.clear()
        await message.answer("Задача не выбрана. Используйте /select_task")
        return

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

    db.delegate_task(task_id, assigned_id, assigned_name)
    await state.set_state(None)

    task = db.get_task_by_id(task_id)
    if task:
        formatted = _format_task(task)
        await message.answer(formatted, reply_markup=get_task_actions_keyboard(task_id))


@router.callback_query(F.data.startswith("deadline:"))
async def cb_set_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    task_id = int(callback.data.split(":")[1])
    await state.set_state(AddTask.waiting_planned_date)
    await state.update_data(task_id=task_id, _editing_deadline=True)
    await callback.message.edit_text(
        "Введите новый срок (ДД.ММ.ГГГГ) или — чтобы убрать:",
        reply_markup=get_back_to_task_keyboard(task_id),
    )
    await callback.answer()
