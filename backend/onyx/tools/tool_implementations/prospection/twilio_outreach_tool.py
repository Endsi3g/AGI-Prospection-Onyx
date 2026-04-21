"""
Twilio Outreach Tool — AGI Prospection Suite
Send SMS messages or initiate voice calls to prospects via the Twilio API.
Uses urllib only (no twilio SDK required).

Requires:
  TWILIO_ACCOUNT_SID  — Twilio Account SID
  TWILIO_AUTH_TOKEN   — Twilio Auth Token
  TWILIO_PHONE_NUMBER — Your Twilio phone number (E.164 format, e.g. +15551234567)
"""
import json
import os
import base64
import urllib.request
import urllib.parse
from typing import Any
from typing_extensions import override
from onyx.chat.emitter import Emitter
from onyx.server.query_and_chat.placement import Placement
from onyx.server.query_and_chat.streaming_models import CustomToolDelta, CustomToolStart, Packet
from onyx.tools.interface import Tool
from onyx.tools.models import CustomToolCallSummary, ToolResponse
from onyx.utils.logger import setup_logger

logger = setup_logger()


def _twilio_api_request(
    account_sid: str,
    auth_token: str,
    resource: str,
    payload: dict,
) -> dict:
    """Make a request to the Twilio REST API (no SDK required)."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/{resource}.json"
    data = urllib.parse.urlencode(payload).encode("utf-8")

    # Basic auth header
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else str(e)
        logger.error(f"Twilio API error: {e.code} — {body}")
        return {"error": body, "status_code": e.code}
    except Exception as e:
        logger.error(f"Twilio request error: {e}")
        return {"error": str(e)}


class TwilioOutreachTool(Tool[None]):
    NAME = "twilio_outreach"
    DISPLAY_NAME = "Twilio SMS & Voice"
    DESCRIPTION = (
        "Send SMS messages or initiate voice calls to prospects via Twilio. "
        "Use for automated outreach, appointment confirmations, or follow-up reminders."
    )

    def __init__(self, tool_id: int, emitter: Emitter) -> None:
        super().__init__(emitter=emitter)
        self._id = tool_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self.NAME

    @property
    def description(self) -> str:
        return self.DESCRIPTION

    @property
    def display_name(self) -> str:
        return self.DISPLAY_NAME

    @override
    def tool_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["sms", "call"],
                            "description": "Action to perform: 'sms' to send a text message, 'call' to initiate a voice call.",
                        },
                        "to_phone": {
                            "type": "string",
                            "description": "Recipient phone number in E.164 format (e.g., +15145551234).",
                        },
                        "message": {
                            "type": "string",
                            "description": "For SMS: the message body. For calls: the TwiML message to speak.",
                        },
                        "prospect_name": {
                            "type": "string",
                            "description": "Name of the prospect (for logging/tracking).",
                        },
                        "company_name": {
                            "type": "string",
                            "description": "Company name of the prospect (for logging/tracking).",
                        },
                    },
                    "required": ["action", "to_phone", "message"],
                },
            },
        }

    @override
    def emit_start(self, placement: Placement) -> None:
        self.emitter.emit(Packet(
            placement=placement,
            obj=CustomToolStart(tool_name=self.NAME, tool_id=self._id),
        ))

    @override
    def run(self, placement: Placement, override_kwargs: None = None, **llm_kwargs: Any) -> ToolResponse:
        action = llm_kwargs.get("action", "sms")
        to_phone = llm_kwargs.get("to_phone", "")
        message = llm_kwargs.get("message", "")
        prospect_name = llm_kwargs.get("prospect_name", "Inconnu")
        company_name = llm_kwargs.get("company_name", "")

        account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        from_phone = os.environ.get("TWILIO_PHONE_NUMBER", "")

        if not all([account_sid, auth_token, from_phone]):
            error_result = {
                "status": "error",
                "error": (
                    "Twilio not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, "
                    "and TWILIO_PHONE_NUMBER in your .env file."
                ),
                "action": action,
                "to": to_phone,
            }
            self.emitter.emit(Packet(
                placement=placement,
                obj=CustomToolDelta(
                    tool_name=self.NAME, tool_id=self._id,
                    response_type="json", data=error_result,
                    file_ids=None, error="Twilio not configured",
                ),
            ))
            return ToolResponse(
                rich_response=CustomToolCallSummary(
                    tool_name=self.NAME, response_type="json",
                    tool_result=error_result, error="Twilio not configured",
                ),
                llm_facing_response=json.dumps(error_result, ensure_ascii=False),
            )

        # Validate phone number format
        if not to_phone.startswith("+"):
            to_phone = f"+1{to_phone.lstrip('0')}"

        if action == "sms":
            payload = {
                "From": from_phone,
                "To": to_phone,
                "Body": message,
            }
            api_result = _twilio_api_request(account_sid, auth_token, "Messages", payload)
        elif action == "call":
            # TwiML for voice call
            twiml = (
                f'<Response><Say voice="alice" language="fr-CA">{message}</Say></Response>'
            )
            payload = {
                "From": from_phone,
                "To": to_phone,
                "Twiml": twiml,
            }
            api_result = _twilio_api_request(account_sid, auth_token, "Calls", payload)
        else:
            api_result = {"error": f"Unknown action: {action}"}

        # Build response
        is_success = "sid" in api_result and "error" not in api_result
        result = {
            "status": "sent" if is_success else "failed",
            "action": action,
            "to": to_phone,
            "prospect": prospect_name,
            "company": company_name,
            "twilio_sid": api_result.get("sid", "N/A"),
            "message_preview": message[:100],
            "twilio_response": {
                k: v for k, v in api_result.items()
                if k in ("sid", "status", "error", "error_code", "error_message", "date_created")
            },
        }

        self.emitter.emit(Packet(
            placement=placement,
            obj=CustomToolDelta(
                tool_name=self.NAME, tool_id=self._id,
                response_type="json", data=result,
                file_ids=None, error=None if is_success else str(api_result.get("error")),
            ),
        ))
        return ToolResponse(
            rich_response=CustomToolCallSummary(
                tool_name=self.NAME, response_type="json",
                tool_result=result, error=None,
            ),
            llm_facing_response=json.dumps(result, ensure_ascii=False),
        )
