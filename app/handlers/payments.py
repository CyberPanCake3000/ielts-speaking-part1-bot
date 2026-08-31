from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.config import settings
from app.database import Database, has_unlimited_access
from app.keyboards import main_menu, paywall_menu

router = Router()

PAYLOAD_SINGLE = "single_question"
PAYLOAD_WEEKLY = "weekly_subscription"
PAYLOAD_UNLIMITED = "unlimited_access"

SUBSCRIPTION_DAYS = 7


async def send_paywall(message: Message) -> None:
    await message.answer(
        "🔓 <b>Get more IELTS practice</b>\n\nChoose an option:",
        reply_markup=paywall_menu(),
    )


@router.message(Command("buy"))
async def buy_command(message: Message):
    await send_paywall(message)


@router.callback_query(F.data == "show_paywall")
async def show_paywall_callback(callback: CallbackQuery):
    await send_paywall(callback.message)
    await callback.answer()


@router.callback_query(F.data == "buy_single")
async def buy_single(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="1 extra practice question",
        description="Unlock one extra IELTS Speaking Part 1 practice attempt.",
        payload=PAYLOAD_SINGLE,
        currency="XTR",
        prices=[LabeledPrice(label="1 extra question", amount=settings.stars_price_single_question)],
        provider_token="",
    )
    await callback.answer()


@router.callback_query(F.data == "buy_weekly")
async def buy_weekly(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="1 week of unlimited practice",
        description=f"Unlimited IELTS Speaking Part 1 practice for {SUBSCRIPTION_DAYS} days.",
        payload=PAYLOAD_WEEKLY,
        currency="XTR",
        prices=[LabeledPrice(label="1 week unlimited", amount=settings.stars_price_weekly)],
        provider_token="",
    )
    await callback.answer()


@router.callback_query(F.data == "buy_unlimited")
async def buy_unlimited(callback: CallbackQuery):
    await callback.message.answer_invoice(
        title="Unlimited IELTS practice forever",
        description="Unlock unlimited IELTS Speaking Part 1 practice sessions, forever.",
        payload=PAYLOAD_UNLIMITED,
        currency="XTR",
        prices=[LabeledPrice(label="Unlimited access", amount=settings.stars_price_unlimited)],
        provider_token="",
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, db: Database):
    telegram_id = message.from_user.id
    payload = message.successful_payment.invoice_payload

    if payload == PAYLOAD_SINGLE:
        await db.grant_extra_attempts(telegram_id, 1)
        text = "🎉 Payment received! You've got 1 extra practice question — use /topic any time."
    elif payload == PAYLOAD_WEEKLY:
        await db.extend_subscription(telegram_id, SUBSCRIPTION_DAYS)
        text = (
            f"🎉 Payment received! You have unlimited practice for the next "
            f"{SUBSCRIPTION_DAYS} days."
        )
    elif payload == PAYLOAD_UNLIMITED:
        await db.upsert_user(telegram_id, is_unlimited=True)
        text = "🎉 Payment received! You now have unlimited IELTS practice sessions, forever. Thank you for the support!"
    else:
        text = "🎉 Payment received!"

    user = await db.get_user(telegram_id)
    await message.answer(text, reply_markup=main_menu(unlimited=has_unlimited_access(user)))
