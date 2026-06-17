TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Check available time slots on the admin's Google Calendar for a discovery call. Call this when a lead asks when to meet, or when you want to suggest slots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "How many days ahead to check for availability. Default 5."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_discovery_call",
            "description": "Book a discovery call on Google Calendar with a Google Meet link. Call this only after the lead has confirmed a specific slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_name": {"type": "string", "description": "Full name of the lead"},
                    "lead_email": {"type": "string", "description": "Email address of the lead"},
                    "slot_datetime": {"type": "string", "description": "The ISO datetime string from the 'iso' field of the check_calendar_availability result. Example: 2025-06-18T10:00:00+05:30. Never construct this yourself."}
                },
                "required": ["lead_name", "lead_email", "slot_datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_followup_email",
            "description": "Send a follow-up email to a qualified or escalated lead summarizing the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_name": {"type": "string"},
                    "lead_email": {"type": "string"},
                    "summary": {"type": "string", "description": "Brief summary of what was discussed and next steps"}
                },
                "required": ["lead_name", "lead_email", "summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_call",
            "description": "Cancel a previously booked discovery call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "calendar_event_id": {"type": "string", "description": "Google Calendar event ID to cancel"}
                },
                "required": ["calendar_event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_priority",
            "description": "Update the priority of a lead in the database when you detect they are high-value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telegram_user_id": {"type": "integer"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                },
                "required": ["telegram_user_id", "priority"]
            }
        }
    }
]