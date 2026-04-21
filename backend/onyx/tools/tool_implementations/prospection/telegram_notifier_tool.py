"""
Telegram Notifier Tool — AGI Prospection Suite
Sends real-time notifications to a Telegram chat/channel when important
prospection events occur (new hot lead, objection handled, deal closed, etc.).

Requires:
  TELEGRAM_BOT_TOKEN — Bot token from @BotFather
  TELEGRAM_CHAT_ID  — Chat/channel ID to send messages to
"""
import json
import os
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


def _send_telegram_message(
    bot_token: str, chat_id: str, text: str, parse_mode: str = "Markdown"
) -> dict:
    """Send a message via the Telegram Bot API (no external deps)."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Telegram API error: {e}")
        return {"ok": False, "error": str(e)}


class TelegramNotifierTool(Tool[None]):
    NAME = "notify_telegram"
    DISPLAY_NAME = "Telegram Notifier"
    DESCRIPTION = (
        "Send a notification to Telegram. Use for alerts about hot leads, "
        "completed outreach sequences, objection wins, or any important prospection event."
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
                        "message": {
                            "type": "string",
                            "description": "The notification message to send. Supports Markdown formatting.",
                        },
                        "notification_type": {
                            "type": "string",
                            "enum": [
                                "hot_lead",
                                "outreach_sent",
                                "objection_handled",
                                "meeting_booked",
                                "deal_closed",
                                "dataset_ingested",
                                "alert",
                                "info",
                            ],
                            "description": "Type of notification — affects the emoji prefix.",
                        },
                        "prospect_name": {
                            "type": "string",
                            "description": "Optional: Name of the prospect this notification is about.",
                        },
                        "icp_score": {
                            "type": "integer",
                            "description": "Optional: ICP score if this is a lead notification.",
                        },
                    },
                    "required": ["message"],
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
        message = llm_kwargs.get("message", "")
        notif_type = llm_kwargs.get("notification_type", "info")
        prospect_name = llm_kwargs.get("prospect_name", "")
        icp_score = llm_kwargs.get("icp_score", None)

        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            error_result = {
                "status": "error",
                "error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env",
                "message_preview": message[:100],
            }
            self.emitter.emit(Packet(
                placement=placement,
                obj=CustomToolDelta(
                    tool_name=self.NAME, tool_id=self._id,
                    response_type="json", data=error_result,
                    file_ids=None, error="Telegram not configured",
                ),
            ))
            return ToolResponse(
                rich_response=CustomToolCallSummary(
                    tool_name=self.NAME, response_type="json",
                    tool_result=error_result, error="Telegram not configured",
                ),
                llm_facing_response=json.dumps(error_result, ensure_ascii=False),
            )

        # Build formatted message
        emoji_map = {
            "hot_lead": "🔥",
            "outreach_sent": "📨",
            "objection_handled": "🛡️",
            "meeting_booked": "📅",
            "deal_closed": "💰",
            "dataset_ingested": "📊",
            "alert": "🚨",
            "info": "ℹ️",
        }
        emoji = emoji_map.get(notif_type, "📌")

        formatted = f"{emoji} *AGI Prospection*\n\n"
        if prospect_name:
            formatted += f"👤 *Prospect:* {prospect_name}\n"
        if icp_score is not None:
            formatted += f"📊 *Score ICP:* {icp_score}/100\n"
        formatted += f"\n{message}"

        # Send via Telegram API
        api_result = _send_telegram_message(bot_token, chat_id, formatted)

        result = {
            "status": "sent" if api_result.get("ok") else "failed",
            "notification_type": notif_type,
            "telegram_response": api_result,
            "message_preview": formatted[:200],
        }

        self.emitter.emit(Packet(
            placement=placement,
            obj=CustomToolDelta(
                tool_name=self.NAME, tool_id=self._id,
                response_type="json", data=result,
                file_ids=None, error=None if api_result.get("ok") else str(api_result),
            ),
        ))
        return ToolResponse(
            rich_response=CustomToolCallSummary(
                tool_name=self.NAME, response_type="json",
                tool_result=result, error=None,
            ),
            llm_facing_response=json.dumps(result, ensure_ascii=False),
        )
