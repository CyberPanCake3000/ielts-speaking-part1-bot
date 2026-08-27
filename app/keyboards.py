from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎤 Practice", callback_data="practice"),
        InlineKeyboardButton(text="📊 My stats", callback_data="stats"),
    )
    builder.row(
        InlineKeyboardButton(text="⏰ Reminder settings", callback_data="reminder_settings"),
    )
    return builder.as_markup()


def reminder_times() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for time in ["08:00", "10:00", "13:00", "18:00", "20:00", "21:00"]:
        builder.button(text=time, callback_data=f"set_time:{time}")
    builder.adjust(2)
    return builder.as_markup()


def reminder_toggle(enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔕 Turn off" if enabled else "🔔 Turn on",
        callback_data="reminder_toggle",
    )
    builder.button(text="Change time", callback_data="change_time")
    builder.adjust(1)
    return builder.as_markup()
