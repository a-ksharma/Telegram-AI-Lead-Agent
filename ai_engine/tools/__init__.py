import json
from ai_engine.tools.calendar import check_calendar_availability, book_discovery_call, cancel_call
from ai_engine.tools.gmail import send_followup_email
from database.db import update_lead_priority, log_tool_call  # you'll add log_tool_call

TOOL_REGISTRY = {
    "check_calendar_availability": check_calendar_availability,
    "book_discovery_call": book_discovery_call,
    "cancel_call": cancel_call,
    "send_followup_email": send_followup_email,
    "update_lead_priority": update_lead_priority,
}

async def execute_tool(tool_name: str, tool_args: dict, telegram_user_id: int) -> str:
    """
    Execute a tool by name, log it, return result as JSON string.
    Always returns a string — this goes back into the Groq message array.
    """
    if tool_name not in TOOL_REGISTRY:
        result = {"success": False, "error": f"Unknown tool: {tool_name}"}
    else:
        try:
            result = await TOOL_REGISTRY[tool_name](**tool_args)
        except Exception as e:
            result = {"success": False, "error": str(e)}

    # Log to DB — non-blocking, never crash main flow
    try:
        await log_tool_call(
            telegram_user_id=telegram_user_id,
            tool_name=tool_name,
            inputs=tool_args,
            result=result,
            success=result.get("success", False)
        )
    except Exception:
        pass

    return json.dumps(result)