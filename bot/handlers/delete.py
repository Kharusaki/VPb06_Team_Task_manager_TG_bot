from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.db.database import Database
from bot.keyboards.inline import get_confirm_delete_keyboard

router = Router()
db = Database()


@router.callback_query(F.data.startswith("delete:"))
async def cb_delete_confirm(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    task = db.get_task_by_id(task_id)
    if not task:
        await callback.answer("Задача не найдена", show_alert=True)
        return

    text = (
        f"Удалить задачу #{task_id}?\n\n"
        f"{task['title']}\n\n"
        f"Это действие необратимо."
    )
    await callback.message.edit_text(text, reply_markup=get_confirm_delete_keyboard(task_id))
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def cb_confirm_delete(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    db.delete_task(task_id)
    await callback.message.edit_text(f"Задача #{task_id} удалена.")
    await callback.answer("Задача удалена")
