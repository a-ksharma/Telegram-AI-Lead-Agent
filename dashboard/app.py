import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import datetime, timezone

from database.db import (
    get_all_leads,
    get_lead_by_id,
    get_chat_history_for_lead,
    get_bookings_for_lead,
    get_all_bookings,
    get_tool_call_logs_for_lead,
    get_escalated_leads,
    update_lead_status,
    get_leads_overview_stats,
)


st.set_page_config(
    page_title="Lead Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    /* ── Base ── */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #0f1117;
        border-right: 1px solid #1e2130;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"] {
        background: #1a1d2e;
        border: 1px solid #2d3148;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="metric-container"] label {
        color: #94a3b8 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ── Chat bubbles ── */
    .chat-bubble-user {
        background: #1e293b;
        border-left: 3px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.9rem;
        color: #e2e8f0;
    }
    .chat-bubble-assistant {
        background: #0f2027;
        border-left: 3px solid #10b981;
        border-radius: 0 8px 8px 0;
        padding: 10px 14px;
        margin: 6px 0;
        font-size: 0.9rem;
        color: #d1fae5;
    }
    .chat-timestamp {
        font-size: 0.7rem;
        color: #475569;
        margin-bottom: 2px;
    }

    /* ── Status badges ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .badge-new       { background: #1e3a5f; color: #93c5fd; }
    .badge-engaged   { background: #1e3a5f; color: #a5f3fc; }
    .badge-qualified { background: #14532d; color: #86efac; }
    .badge-escalated { background: #4c1d1d; color: #fca5a5; }
    .badge-closed    { background: #1e1e2e; color: #94a3b8; }

    /* ── Section headers ── */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #475569;
        margin-bottom: 8px;
        margin-top: 24px;
    }

    /* ── Tool log card ── */
    .tool-log-card {
        background: #11131e;
        border: 1px solid #1e2130;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 6px 0;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        color: #94a3b8;
    }
    .tool-log-card .tool-name {
        color: #a78bfa;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .tool-log-success { border-left: 3px solid #10b981; }
    .tool-log-fail    { border-left: 3px solid #ef4444; }

    /* ── Booking card ── */
    .booking-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 8px 0;
    }
    .booking-meet-link {
        display: inline-block;
        margin-top: 8px;
        padding: 4px 12px;
        background: #064e3b;
        color: #6ee7b7;
        border-radius: 6px;
        font-size: 0.8rem;
        text-decoration: none;
    }

    /* ── Divider ── */
    hr { border-color: #1e2130; }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_OPTIONS = ["new", "engaged", "qualified", "escalated", "closed"]
PRIORITY_COLORS = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def badge(status: str) -> str:
    s = (status or "new").lower()
    return f'<span class="badge badge-{s}">{s}</span>'


def fmt_dt(raw: str) -> str:
    """Convert ISO timestamp to readable local format."""
    if not raw:
        return "—"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %I:%M %p UTC")
    except Exception:
        return raw


def priority_icon(p: str) -> str:
    return PRIORITY_COLORS.get((p or "low").lower(), "⚪")


with st.sidebar:
    st.markdown("## Lead Agent")
    st.markdown("**Internal Admin Dashboard**")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["Overview", "All Leads", "Lead Detail", "Escalated", "Bookings"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if st.button("Refresh Data", width='stretch'):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        "<div style='color:#475569;font-size:0.75rem;margin-top:auto'>Built with Streamlit + Supabase</div>",
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=60)
def cached_all_leads():
    return get_all_leads()


@st.cache_data(ttl=60)
def cached_stats():
    return get_leads_overview_stats()


@st.cache_data(ttl=60)
def cached_escalated():
    return get_escalated_leads()


@st.cache_data(ttl=60)
def cached_all_bookings():
    return get_all_bookings()



if page == "Overview":
    st.title("Overview")
    st.markdown("Real-time snapshot of your lead pipeline.")

    stats = cached_stats()
    by_status = stats.get("by_status", {})

    # ── KPI Row ──
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leads", stats.get("total", 0))
    col2.metric("New Today", stats.get("today_count", 0))
    col3.metric("Escalated", stats.get("escalated_count", 0))
    col4.metric("Qualified", by_status.get("qualified", 0))

    st.markdown("---")

    
    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### Status Breakdown")
        if by_status and any(by_status.values()):
            status_df = pd.DataFrame(
                {"Status": list(by_status.keys()), "Count": list(by_status.values())}
            )
            st.bar_chart(status_df.set_index("Status"), width='stretch', height=280)
        else:
            st.info("No lead data yet.")

    with right:
        st.markdown("#### Pipeline Health")
        total = stats.get("total", 0)
        if total > 0:
            for s, count in by_status.items():
                pct = int((count / total) * 100)
                st.markdown(
                    f"""
                    <div style="margin:8px 0">
                        <div style="display:flex;justify-content:space-between;font-size:0.82rem;color:#94a3b8">
                            <span>{s.capitalize()}</span><span>{count} ({pct}%)</span>
                        </div>
                        <div style="background:#1e2130;border-radius:4px;height:6px;margin-top:4px">
                            <div style="background:#6366f1;width:{pct}%;height:6px;border-radius:4px"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No leads to display.")

    st.markdown("---")

    
    st.markdown("#### Recent Activity")
    leads = cached_all_leads()
    if leads:
        recent = leads[:5]
        for lead in recent:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"**{lead.get('name') or 'Unknown'}** `@{lead.get('username') or 'n/a'}`")
                c2.markdown(badge(lead.get("status", "new")), unsafe_allow_html=True)
                c3.markdown(f"{priority_icon(lead.get('priority', 'low'))} {lead.get('priority', 'low').capitalize()}")
                c4.markdown(f"<span style='color:#475569;font-size:0.8rem'>{fmt_dt(lead.get('last_active_at', ''))}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:6px 0'>", unsafe_allow_html=True)
    else:
        st.info("No leads found. The bot hasn't received any messages yet.")




elif page == "All Leads":
    st.title("All Leads")

    leads = cached_all_leads()

    if not leads:
        st.info("No leads in the database yet.")
        st.stop()

    
    with st.expander("Filter & Search", expanded=True):
        fcol1, fcol2, fcol3 = st.columns(3)

        search_query = fcol1.text_input("Search by name / username", placeholder="e.g. Rahul")
        status_filter = fcol2.multiselect(
            "Status", STATUS_OPTIONS, default=STATUS_OPTIONS
        )
        priority_filter = fcol3.multiselect(
            "Priority", ["high", "medium", "low"], default=["high", "medium", "low"]
        )

    
    filtered = [
        l for l in leads
        if (l.get("status", "new") in status_filter)
        and (l.get("priority", "low") in priority_filter)
        and (
            search_query.lower() in (l.get("name") or "").lower()
            or search_query.lower() in (l.get("username") or "").lower()
            or search_query == ""
        )
    ]

    st.markdown(f"Showing **{len(filtered)}** of **{len(leads)}** leads")
    st.markdown("---")

    if not filtered:
        st.warning("No leads match your filters.")
        st.stop()

    
    hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([3, 2, 1.5, 1.5, 2.5, 1])
    for label, col in zip(
        ["Name / Username", "First Message", "Status", "Priority", "Last Active", "Detail"],
        [hc1, hc2, hc3, hc4, hc5, hc6],
    ):
        col.markdown(f"<div class='section-label'>{label}</div>", unsafe_allow_html=True)

    
    for lead in filtered:
        uid = lead.get("telegram_user_id")
        rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([3, 2, 1.5, 1.5, 2.5, 1])

        rc1.markdown(
            f"**{lead.get('name') or 'Unknown'}**<br>"
            f"<span style='color:#475569;font-size:0.78rem'>@{lead.get('username') or 'no handle'} · `{uid}`</span>",
            unsafe_allow_html=True,
        )
        first_msg = (lead.get("first_message") or "")[:60]
        rc2.markdown(f"<span style='color:#94a3b8;font-size:0.82rem'>{first_msg}…</span>", unsafe_allow_html=True)
        rc3.markdown(badge(lead.get("status", "new")), unsafe_allow_html=True)
        rc4.markdown(f"{priority_icon(lead.get('priority', 'low'))} {(lead.get('priority') or 'low').capitalize()}")
        rc5.markdown(
            f"<span style='color:#475569;font-size:0.8rem'>{fmt_dt(lead.get('last_active_at', ''))}</span>",
            unsafe_allow_html=True,
        )
        if rc6.button("View", key=f"view_{uid}"):
            st.session_state["selected_lead_id"] = uid
            
            st.session_state["nav_to_detail"] = True
            st.rerun()

        st.markdown("<hr style='margin:4px 0;border-color:#1e2130'>", unsafe_allow_html=True)

    
    if st.session_state.get("nav_to_detail"):
        st.session_state["nav_to_detail"] = False
        
        st.info("Click **Lead Detail** in the sidebar to view the selected lead.")




elif page == "Lead Detail":
    st.title("Lead Detail")

    leads = cached_all_leads()
    if not leads:
        st.info("No leads in the database.")
        st.stop()

    
    lead_options = {
        f"{l.get('name') or 'Unknown'} (@{l.get('username') or 'n/a'}) — {l.get('telegram_user_id')}": l.get("telegram_user_id")
        for l in leads
    }

    
    default_label = None
    if "selected_lead_id" in st.session_state:
        for label, uid in lead_options.items():
            if uid == st.session_state["selected_lead_id"]:
                default_label = label
                break

    selected_label = st.selectbox(
        "Select a lead",
        list(lead_options.keys()),
        index=list(lead_options.keys()).index(default_label) if default_label else 0,
    )

    selected_uid = lead_options[selected_label]
    lead = get_lead_by_id(selected_uid)

    if not lead:
        st.error("Could not load lead data.")
        st.stop()

    
    st.markdown("---")
    top_left, top_right = st.columns([3, 1])

    with top_left:
        st.markdown(
            f"## {lead.get('name') or 'Unknown Lead'}"
            f"&nbsp;&nbsp;{badge(lead.get('status', 'new'))}",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='color:#64748b'>@{lead.get('username') or 'no handle'} &nbsp;·&nbsp; "
            f"Telegram ID: `{selected_uid}` &nbsp;·&nbsp; "
            f"Priority: {priority_icon(lead.get('priority', 'low'))} {(lead.get('priority') or 'low').capitalize()}</span>",
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown("<div class='section-label'>Update Status</div>", unsafe_allow_html=True)
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=STATUS_OPTIONS.index(lead.get("status", "new")),
            label_visibility="collapsed",
            key="status_select",
        )
        if st.button("Save Status", width='stretch'):
            result = update_lead_status(selected_uid, new_status)
            if result.get("success"):
                st.success("Status updated.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Failed: {result.get('error')}")

    st.markdown("---")

    
    tab1, tab2, tab3, tab4 = st.tabs(["Profile", "Conversation", "Bookings", "Tool Logs"])

    
    with tab1:
        cols = st.columns(2)

        with cols[0]:
            st.markdown("<div class='section-label'>Contact Info</div>", unsafe_allow_html=True)
            st.markdown(f"**Email:** {lead.get('email') or '—'}")
            st.markdown(f"**Username:** @{lead.get('username') or '—'}")
            st.markdown(f"**First Contact:** {fmt_dt(lead.get('created_at', ''))}")
            st.markdown(f"**Last Active:** {fmt_dt(lead.get('last_active_at', ''))}")
            st.markdown(f"**Escalated:** {'Yes' if lead.get('is_escalated') else 'No'}")

            st.markdown("<div class='section-label'>First Message</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='chat-bubble-user'>{lead.get('first_message') or '—'}</div>",
                unsafe_allow_html=True,
            )

        with cols[1]:
            st.markdown("<div class='section-label'>Onboarding Answers</div>", unsafe_allow_html=True)
            onboarding_complete = lead.get("onboarding_complete", False)
            if onboarding_complete:
                fields = [
                    ("Business Type", "business_type"),
                    ("Automation Interest", "automation_interest"),
                    ("Looking For", "looking_for"),
                    ("Budget Range", "budget_range"),
                    ("Timeline", "timeline"),
                ]
                for label, key in fields:
                    val = lead.get(key) or "—"
                    st.markdown(f"**{label}:** {val}")
            else:
                st.info("Onboarding not yet completed by this lead.")

    
    with tab2:
        history = get_chat_history_for_lead(selected_uid)
        if not history:
            st.info("No conversation history found.")
        else:
            st.markdown(f"**{len(history)} messages** in this conversation")
            st.markdown("")
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                ts = fmt_dt(msg.get("created_at", ""))
                css_class = "chat-bubble-user" if role == "user" else "chat-bubble-assistant"
                role_label = "Lead" if role == "user" else "Bot"
                st.markdown(
                    f"""
                    <div class="chat-timestamp">{role_label} · {ts}</div>
                    <div class="{css_class}">{content}</div>
                    """,
                    unsafe_allow_html=True,
                )

    
    with tab3:
        bookings = get_bookings_for_lead(selected_uid)
        if not bookings:
            st.info("No bookings found for this lead.")
        else:
            for b in bookings:
                meet_link = b.get("google_meet_link") or ""
                meet_html = (
                    f'<a href="{meet_link}" target="_blank" class="booking-meet-link">🎥 Join Meet</a>'
                    if meet_link else "<span style='color:#475569'>No Meet link</span>"
                )
                st.markdown(
                    f"""
                    <div class="booking-card">
                        <div style="font-weight:600;color:#e2e8f0"> {fmt_dt(b.get('scheduled_at', ''))}</div>
                        <div style="margin-top:6px;font-size:0.82rem;color:#94a3b8">
                            Status: <strong>{b.get('status', '—')}</strong>
                            &nbsp;·&nbsp; Event ID: <code>{b.get('calendar_event_id', '—')}</code>
                        </div>
                        {meet_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    
    with tab4:
        logs = get_tool_call_logs_for_lead(selected_uid)
        if not logs:
            st.info("No tool calls recorded for this lead.")
        else:
            st.markdown(f"**{len(logs)} tool calls** recorded")
            for log in logs:
                success = log.get("success", False)
                card_class = "tool-log-success" if success else "tool-log-fail"
                status_icon = "✅" if success else "❌"
                tool_name = log.get("tool_name", "unknown")
                called_at = fmt_dt(log.get("called_at", ""))
                inputs = log.get("inputs") or {}
                result = log.get("result") or {}

                st.markdown(
                    f"""
                    <div class="tool-log-card {card_class}">
                        <span class="tool-name">{status_icon} {tool_name}</span>
                        <span style="color:#475569;font-size:0.75rem;float:right">{called_at}</span>
                        <div style="margin-top:8px">
                            <div style="color:#64748b;font-size:0.75rem">INPUTS</div>
                            <div>{inputs}</div>
                        </div>
                        <div style="margin-top:6px">
                            <div style="color:#64748b;font-size:0.75rem">RESULT</div>
                            <div>{result}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )




elif page == "Escalated":
    st.title("Escalated Leads")
    st.markdown("Leads that need human attention. Resolve by updating their status.")

    escalated = cached_escalated()

    if not escalated:
        st.success("No escalated leads right now. The bot is handling everything.")
        st.stop()

    st.markdown(f"**{len(escalated)} leads** need your attention")
    st.markdown("---")

    for lead in escalated:
        uid = lead.get("telegram_user_id")
        with st.container():
            left, right = st.columns([5, 2])

            with left:
                st.markdown(
                    f"### {lead.get('name') or 'Unknown'} &nbsp; {badge(lead.get('status', 'escalated'))}",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='color:#64748b'>@{lead.get('username') or 'n/a'} · `{uid}` · "
                    f"Last active: {fmt_dt(lead.get('last_active_at', ''))}</span>",
                    unsafe_allow_html=True,
                )
                first_msg = lead.get("first_message") or "—"
                st.markdown(
                    f"<div class='chat-bubble-user' style='margin-top:8px'>{first_msg}</div>",
                    unsafe_allow_html=True,
                )

            with right:
                st.markdown("<div class='section-label'>Quick Action</div>", unsafe_allow_html=True)
                if st.button("Mark Resolved → Qualified", key=f"resolve_{uid}", width='stretch'):
                    update_lead_status(uid, "qualified")
                    st.cache_data.clear()
                    st.success(f"Lead {uid} marked as qualified.")
                    st.rerun()
                if st.button("Close Lead", key=f"close_{uid}", width='stretch'):
                    update_lead_status(uid, "closed")
                    st.cache_data.clear()
                    st.success(f"Lead {uid} closed.")
                    st.rerun()
                # Store uid and hint to go to detail
                if st.button("View Full Detail", key=f"detail_{uid}", width='stretch'):
                    st.session_state["selected_lead_id"] = uid
                    st.info("Click **Lead Detail** in the sidebar.")

        st.markdown("---")



elif page == "Bookings":
    st.title("Bookings")
    st.markdown("All discovery calls scheduled via the bot.")

    bookings = cached_all_bookings()

    if not bookings:
        st.info("No calls booked yet. Bookings will appear here once leads schedule through the bot.")
        st.stop()

   
    b_status_filter = st.multiselect(
        "Filter by booking status",
        ["scheduled", "cancelled", "completed"],
        default=["scheduled", "completed"],
    )

    filtered_bookings = [b for b in bookings if b.get("status", "scheduled") in b_status_filter]
    st.markdown(f"**{len(filtered_bookings)}** bookings shown")
    st.markdown("---")

    if not filtered_bookings:
        st.warning("No bookings match the selected status filters.")
        st.stop()

    for b in filtered_bookings:
        uid = b.get("telegram_user_id")
        meet_link = b.get("google_meet_link") or ""
        status = b.get("status", "scheduled")
        status_color = {"scheduled": "#6366f1", "cancelled": "#ef4444", "completed": "#10b981"}.get(status, "#94a3b8")

        col1, col2, col3 = st.columns([3, 2, 2])

        col1.markdown(
            f"**{fmt_dt(b.get('scheduled_at', ''))}**<br>"
            f"<span style='color:#64748b;font-size:0.8rem'>Lead ID: `{uid}`</span>",
            unsafe_allow_html=True,
        )
        col2.markdown(
            f"<span style='color:{status_color};font-weight:600;text-transform:uppercase;font-size:0.8rem'>{status}</span>",
            unsafe_allow_html=True,
        )

        if meet_link:
            col3.markdown(
                f'<a href="{meet_link}" target="_blank" class="booking-meet-link">🎥 Join Google Meet</a>',
                unsafe_allow_html=True,
            )
        else:
            col3.markdown("<span style='color:#475569;font-size:0.8rem'>No Meet link</span>", unsafe_allow_html=True)

        st.markdown("<hr style='margin:6px 0;border-color:#1e2130'>", unsafe_allow_html=True)