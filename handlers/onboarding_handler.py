from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from database.db import upsert_lead, save_onboarding_data, save_message
from handlers.message_handler import handle_message


BUSINESS_TYPE, AUTOMATION_INTEREST, LOOKING_FOR, BUDGET, TIMELINE, CONFIRM = range(6)

BUSINESS_OPTIONS = [
    "E-commerce", "Healthcare", "Real Estate",
    "Education", "Finance", "Hospitality", "Other"
]

AUTOMATION_OPTIONS = [
    "Customer Support", "Lead Generation", "Invoice & Billing",
    "Inventory Management", "Marketing Campaigns", "Other"
]

LOOKING_FOR_OPTIONS = [
    "AI Chatbot", "Workflow Automation", "Custom Software",
    "Consulting / Strategy", "Not Sure Yet", "Other"
]

BUDGET_OPTIONS = [
    "Under $500", "$500 - $2000", "$2000 - $5000",
    "Above $5000", "Not decided yet"
]

TIMELINE_OPTIONS = [
    "ASAP", "Within 1 month", "1-3 months",
    "3-6 months", "Just exploring"
]


def build_keyboard(options: list, include_type_option: bool = True) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
    if include_type_option:
        rows.append([InlineKeyboardButton("Type my own answer", callback_data="__type__")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    upsert_lead(user.id, user.username, "/start")

    context.user_data["onboarding"] = {}
    context.user_data["awaiting_custom_input_for"] = None
    context.user_data["onboarding_summary"] = ""

    await update.message.reply_text(
        f"Hey {user.first_name}! Welcome. I'm the AI assistant for our agency.\n\n"
        "I'll ask you a few quick questions to understand your needs better. "
        "Let's start!\n\n"
        "*What type of business are you in?*",
        parse_mode="Markdown",
        reply_markup=build_keyboard(BUSINESS_OPTIONS)
    )
    return BUSINESS_TYPE


async def handle_business_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "__type__":
        context.user_data["awaiting_custom_input_for"] = "business_type"
        await query.edit_message_text("Please type your business type:")
        return BUSINESS_TYPE

    context.user_data["onboarding"]["business_type"] = query.data
    await query.edit_message_text(f"Business type: *{query.data}*", parse_mode="Markdown")
    await query.get_bot().send_message(
        chat_id=query.message.chat_id,
        text="*What kind of automation are you most interested in?*",
        parse_mode="Markdown",
        reply_markup=build_keyboard(AUTOMATION_OPTIONS)
    )
    return AUTOMATION_INTEREST


async def handle_automation_interest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "__type__":
        context.user_data["awaiting_custom_input_for"] = "automation_interest"
        await query.edit_message_text("Please describe the automation you have in mind:")
        return AUTOMATION_INTEREST

    context.user_data["onboarding"]["automation_interest"] = query.data
    await query.edit_message_text(f"Automation interest: *{query.data}*", parse_mode="Markdown")
    await query.get_bot().send_message(
        chat_id=query.message.chat_id,
        text="*What specifically are you looking to get from us?*",
        parse_mode="Markdown",
        reply_markup=build_keyboard(LOOKING_FOR_OPTIONS)
    )
    return LOOKING_FOR


async def handle_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "__type__":
        context.user_data["awaiting_custom_input_for"] = "looking_for"
        await query.edit_message_text("Tell us what you're looking for:")
        return LOOKING_FOR

    context.user_data["onboarding"]["looking_for"] = query.data
    await query.edit_message_text(f"Looking for: *{query.data}*", parse_mode="Markdown")
    await query.get_bot().send_message(
        chat_id=query.message.chat_id,
        text="*What's your approximate budget for this project?*",
        parse_mode="Markdown",
        reply_markup=build_keyboard(BUDGET_OPTIONS)
    )
    return BUDGET


async def handle_budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "__type__":
        context.user_data["awaiting_custom_input_for"] = "budget_range"
        await query.edit_message_text("Please type your budget range:")
        return BUDGET

    context.user_data["onboarding"]["budget_range"] = query.data
    await query.edit_message_text(f"Budget: *{query.data}*", parse_mode="Markdown")
    await query.get_bot().send_message(
        chat_id=query.message.chat_id,
        text="*What's your timeline for getting started?*",
        parse_mode="Markdown",
        reply_markup=build_keyboard(TIMELINE_OPTIONS)
    )
    return TIMELINE


async def handle_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "__type__":
        context.user_data["awaiting_custom_input_for"] = "timeline"
        await query.edit_message_text("Please type your expected timeline:")
        return TIMELINE

    await query.edit_message_text(f"Timeline: *{query.data}*", parse_mode="Markdown")
    context.user_data["onboarding"]["timeline"] = query.data
    return await finish_onboarding(update, context, via_query=True)


async def handle_custom_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles free-text answers when user chose 'Type my own answer'."""
    field = context.user_data.get("awaiting_custom_input_for")
    text = update.message.text.strip()

    if not field:
        await handle_message(update, context)
        return ConversationHandler.END

    context.user_data["onboarding"][field] = text
    context.user_data["awaiting_custom_input_for"] = None

    state_map = {
        "business_type": (AUTOMATION_INTEREST, "*What kind of automation are you most interested in?*", AUTOMATION_OPTIONS),
        "automation_interest": (LOOKING_FOR, "*What specifically are you looking to get from us?*", LOOKING_FOR_OPTIONS),
        "looking_for": (BUDGET, "*What's your approximate budget for this project?*", BUDGET_OPTIONS),
        "budget_range": (TIMELINE, "*What's your timeline for getting started?*", TIMELINE_OPTIONS),
        "timeline": (None, None, None),
    }

    next_state, next_question, next_options = state_map[field]

    if next_state is None:
        return await finish_onboarding(update, context, via_query=False)

    await update.message.reply_text(
        f"Got it!\n\n{next_question}",
        parse_mode="Markdown",
        reply_markup=build_keyboard(next_options)
    )
    return next_state


async def finish_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE, via_query: bool) -> int:
    user = update.effective_user
    onboarding = context.user_data.get("onboarding", {})

    save_onboarding_data(user.id, onboarding)

    summary = (
        f"*Business:* {onboarding.get('business_type', '—')}\n"
        f"*Automation interest:* {onboarding.get('automation_interest', '—')}\n"
        f"*Looking for:* {onboarding.get('looking_for', '—')}\n"
        f"*Budget:* {onboarding.get('budget_range', '—')}\n"
        f"*Timeline:* {onboarding.get('timeline', '—')}"
    )

    escalate_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Talk to a human now", callback_data="__escalate__")]
    ])

    confirm_text = (
        "Thanks! Here's what I've noted:\n\n"
        f"{summary}\n\n"
        "I'll now connect you with our AI assistant who can answer your questions in detail. "
        "Or if you'd prefer, you can talk to a human right away."
    )

    if via_query:
        await update.callback_query.get_bot().send_message(
            chat_id=update.callback_query.message.chat_id,
            text=confirm_text,
            parse_mode="Markdown",
            reply_markup=escalate_keyboard
        )
    else:
        await update.message.reply_text(
            confirm_text, parse_mode="Markdown", reply_markup=escalate_keyboard
        )

    context.user_data["onboarding_summary"] = summary
    return CONFIRM


async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    

    if query.data == "__escalate__":
        user = update.effective_user
        from config import ADMIN_CHAT_ID
        from database.db import update_lead_status

        update_lead_status(user.id, "escalated", is_escalated=True)

        alert = (
            f"*Escalation at onboarding stage*\n"
            f"User: @{user.username or 'N/A'} (ID: `{user.id}`)\n"
            f"Requested human contact immediately after onboarding."
        )
        try:
            await query.get_bot().send_message(
                chat_id=int(ADMIN_CHAT_ID),
                text=alert,
                parse_mode="HTML"
            )
        except Exception as e:
            pass

        await query.edit_message_text(
            "Got it! Someone from our team will reach out to you shortly. "
            "In the meantime, feel free to ask me anything!"
        )

    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            BUSINESS_TYPE: [
                CallbackQueryHandler(handle_business_type),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_text_input),
            ],
            AUTOMATION_INTEREST: [
                CallbackQueryHandler(handle_automation_interest),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_text_input),
            ],
            LOOKING_FOR: [
                CallbackQueryHandler(handle_looking_for),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_text_input),
            ],
            BUDGET: [
                CallbackQueryHandler(handle_budget),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_text_input),
            ],
            TIMELINE: [
                CallbackQueryHandler(handle_timeline),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_text_input),
            ],
            CONFIRM: [
                CallbackQueryHandler(handle_confirm),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )