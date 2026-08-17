from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_task_actions_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Статус", callback_data=f"status:{task_id}"),
                InlineKeyboardButton(text="Приоритет", callback_data=f"priority:{task_id}"),
            ],
            [
                InlineKeyboardButton(text="Делегировать", callback_data=f"delegate:{task_id}"),
                InlineKeyboardButton(text="Срок", callback_data=f"deadline:{task_id}"),
            ],
            [
                InlineKeyboardButton(text="Редактировать", callback_data=f"edit:{task_id}"),
                InlineKeyboardButton(text="Удалить", callback_data=f"delete:{task_id}"),
            ],
        ]
    )


def get_status_keyboard(task_id: int) -> InlineKeyboardMarkup:
    statuses = [
        "Не начата",
        "В работе",
        "На проверке",
        "Доработка",
        "Выполнена",
    ]
    buttons = [
        [InlineKeyboardButton(text=s, callback_data=f"set_status:{task_id}:{s}")]
        for s in statuses
    ]
    buttons.append(
        [InlineKeyboardButton(text="Назад", callback_data=f"task:{task_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_priority_keyboard(task_id: int) -> InlineKeyboardMarkup:
    priorities = ["Высокий", "Средний", "Низкий"]
    buttons = [
        [InlineKeyboardButton(text=p, callback_data=f"set_priority:{task_id}:{p}")]
        for p in priorities
    ]
    buttons.append(
        [InlineKeyboardButton(text="Назад", callback_data=f"task:{task_id}")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_edit_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Название", callback_data=f"edit_title:{task_id}"
                ),
                InlineKeyboardButton(
                    text="Описание", callback_data=f"edit_desc:{task_id}"
                ),
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data=f"task:{task_id}")
            ],
        ]
    )


def get_confirm_delete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить", callback_data=f"confirm_delete:{task_id}"
                ),
                InlineKeyboardButton(
                    text="Отмена", callback_data=f"task:{task_id}"
                ),
            ]
        ]
    )


def get_back_to_task_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад к задаче", callback_data=f"task:{task_id}")]
        ]
    )


def get_task_selection_keyboard(tasks: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for t in tasks:
        status_icons = {
            "Не начата": "⬜",
            "В работе": "🔵",
            "На проверке": "🟡",
            "Доработка": "🟠",
            "Выполнена": "✅",
        }
        icon = status_icons.get(t["status"], "❓")
        label = f"{icon} #{t['id']} — {t['title'][:40]}"
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"select:{t['id']}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
