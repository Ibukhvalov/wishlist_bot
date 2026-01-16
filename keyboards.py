from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_actions_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 List Gifts", callback_data="list"),
                InlineKeyboardButton(text="💬 Comment", callback_data="comment")
            ],
            [
                InlineKeyboardButton(text="🔒 Reserve", callback_data="reserve"),
                InlineKeyboardButton(text="🔓 Unreserve", callback_data="unreserve")
            ],
            [
                InlineKeyboardButton(text="👀 Add", callback_data="add"),
                InlineKeyboardButton(text="🗑️ Delete", callback_data="delete"),
            ]
        ]
    )
    return kb
