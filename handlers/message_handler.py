import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from ai_engine import get_ai_response
from database.db import get_chat_history, upsert_lead, save_message, update_lead_status
from config import ADMIN_CHAT_ID

conversation_history = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.message.from_user.username
    text = update.message.text

    if user_id not in conversation_history:
        conversation_history[user_id] = get_chat_history(user_id)

    upsert_lead(user_id, username, text)
    save_message(user_id, 'user', text)

    
    onboarding_context = context.user_data.get("onboarding_summary", "")

    ai_response = await get_ai_response(
        conversation_history[user_id],
        text,
        onboarding_context=onboarding_context,
        telegram_user_id=user_id
    )

    print("DEBUG ai_response:", ai_response)

    update_lead_status(user_id, ai_response["status"], ai_response["is_escalated"])

    alert_text = f"Escalation Alert!\nUser ID: {user_id}\nUsername: @{username}\nLast message: {text}"

    if ai_response["is_escalated"]:
        try:
            await context.bot.send_message(ADMIN_CHAT_ID, alert_text)
        except Exception:
            pass  # never block user reply because of this

    save_message(user_id, 'assistant', ai_response["reply"])

    await update.message.reply_text(ai_response['reply'])


    conversation_history[user_id].append({
        'role': 'user',
        'content': text
    })

    conversation_history[user_id].append({
        'role': 'assistant',
        'content': ai_response["reply"]
    })
