from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, timezone

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_lead(telegram_user_id, username, first_message):
    supabase.table("leads").upsert({
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_message": first_message,
        "last_active_at": datetime.now(timezone.utc).isoformat()
    },on_conflict="telegram_user_id"
    ).execute()

def save_message(telegram_user_id, role, content):
    result = supabase.table("chat_history").select("id", count="exact").eq("telegram_user_id", telegram_user_id).execute()
    sequence_number = result.count + 1

    supabase.table("chat_history").insert(
        {"telegram_user_id": telegram_user_id, "role": role, "content": content, "sequence_number": sequence_number}
    ).execute()

def get_chat_history(telegram_user_id):
    result = supabase.table("chat_history").select("*").eq("telegram_user_id", telegram_user_id).order("sequence_number").execute()
    return result.data

def update_lead_status(telegram_user_id, status, is_escalated = False):
    supabase.table("leads").update({
        "status": status,
        "is_escalated": is_escalated,
        "last_active_at": datetime.now(timezone.utc).isoformat()
    }).eq("telegram_user_id", telegram_user_id).execute()

def save_onboarding_data(telegram_user_id: int, data: dict):
    now = datetime.now(timezone.utc).isoformat()
    
    supabase.table("leads").update({
        "business_type": data.get("business_type"),
        "automation_interest": data.get("automation_interest"),
        "looking_for": data.get("looking_for"),
        "budget_range": data.get("budget_range"),
        "timeline": data.get("timeline"),
        "onboarding_complete": True,
        "last_active_at": now
    }).eq("telegram_user_id", telegram_user_id).execute()

    supabase.table("onboarding_history").insert({
        "telegram_user_id": telegram_user_id,
        "business_type": data.get("business_type"),
        "automation_interest": data.get("automation_interest"),
        "looking_for": data.get("looking_for"),
        "budget_range": data.get("budget_range"),
        "timeline": data.get("timeline"),
        "submitted_at": now
    }).execute()


async def log_tool_call(telegram_user_id, tool_name, inputs, result, success):
    supabase.table("tool_call_logs").insert({
        "telegram_user_id": telegram_user_id,
        "tool_name": tool_name,
        "inputs": inputs,      
        "result": result,
        "success": success,
        "called_at": datetime.now(timezone.utc).isoformat()
    }).execute()

async def update_lead_priority(telegram_user_id: int, priority: str) -> dict:
    try:
        supabase.table("leads").update({"priority": priority}).eq("telegram_user_id", telegram_user_id).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
# Reading Functions

def get_all_leads():
    """
    Fetch all leads ordered by most recently active.
    Returns a list of dicts (one per lead), or [] on error.
    """
    try:
        response = supabase.table("leads").select("*").order("last_active_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_all_leads: {e}")
        return []


def get_lead_by_id(telegram_user_id: int):
    """
    Fetch a single lead row by telegram_user_id.
    Returns a dict or None.
    """
    try:
        response = (
            supabase.table("leads")
            .select("*")
            .eq("telegram_user_id", telegram_user_id)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[DB ERROR] get_lead_by_id: {e}")
        return None


def get_chat_history_for_lead(telegram_user_id: int):
    """
    Fetch full conversation history for a lead, ordered chronologically.
    Returns list of dicts with role/content/created_at.
    """
    try:
        response = (
            supabase.table("chat_history")
            .select("role, content, created_at, sequence_number")
            .eq("telegram_user_id", telegram_user_id)
            .order("sequence_number", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_chat_history_for_lead: {e}")
        return []


def get_bookings_for_lead(telegram_user_id: int):
    """
    Fetch all bookings for a specific lead.
    Returns list of dicts.
    """
    try:
        response = (
            supabase.table("bookings")
            .select("*")
            .eq("telegram_user_id", telegram_user_id)
            .order("scheduled_at", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_bookings_for_lead: {e}")
        return []


def get_all_bookings():
    """
    Fetch all bookings across all leads, ordered by scheduled time.
    Used in the Bookings page of the dashboard.
    Returns list of dicts.
    """
    try:
        response = (
            supabase.table("bookings")
            .select("*")
            .order("scheduled_at", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_all_bookings: {e}")
        return []


def get_tool_call_logs_for_lead(telegram_user_id: int):
    """
    Fetch all tool call logs for a specific lead.
    Returns list of dicts ordered by most recent first.
    """
    try:
        response = (
            supabase.table("tool_call_logs")
            .select("*")
            .eq("telegram_user_id", telegram_user_id)
            .order("called_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_tool_call_logs_for_lead: {e}")
        return []


def get_escalated_leads():
    """
    Fetch all leads where is_escalated = True.
    Returns list of dicts ordered by most recently active.
    """
    try:
        response = (
            supabase.table("leads")
            .select("*")
            .eq("is_escalated", True)
            .order("last_active_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        print(f"[DB ERROR] get_escalated_leads: {e}")
        return []


def update_lead_status(telegram_user_id: int, new_status: str):
    """
    Update the status field of a lead.
    Valid values: new / engaged / qualified / escalated / closed
    Used by the dashboard's quick-action buttons.
    Returns {"success": True} or {"success": False, "error": ...}
    """
    try:
        supabase.table("leads").update({"status": new_status}).eq(
            "telegram_user_id", telegram_user_id
        ).execute()
        return {"success": True}
    except Exception as e:
        print(f"[DB ERROR] update_lead_status: {e}")
        return {"success": False, "error": str(e)}


def get_leads_overview_stats():
    """
    Aggregate stats for the Overview page.
    Returns a dict:
    {
        "total": int,
        "by_status": {"new": int, "engaged": int, ...},
        "escalated_count": int,
        "today_count": int,
    }
    Computed in Python from a single all-leads fetch (avoids multiple round trips).
    """
    try:
        from datetime import datetime, timezone

        all_leads = get_all_leads()
        today = datetime.now(timezone.utc).date()

        by_status = {"new": 0, "engaged": 0, "qualified": 0, "escalated": 0, "closed": 0}
        escalated_count = 0
        today_count = 0

        for lead in all_leads:
            status = lead.get("status", "new")
            if status in by_status:
                by_status[status] += 1
            if lead.get("is_escalated"):
                escalated_count += 1
            created_raw = lead.get("created_at", "")
            if created_raw:
                created_date = datetime.fromisoformat(created_raw.replace("Z", "+00:00")).date()
                if created_date == today:
                    today_count += 1

        return {
            "total": len(all_leads),
            "by_status": by_status,
            "escalated_count": escalated_count,
            "today_count": today_count,
        }
    except Exception as e:
        print(f"[DB ERROR] get_leads_overview_stats: {e}")
        return {"total": 0, "by_status": {}, "escalated_count": 0, "today_count": 0}