"""renderer.py — Multi-Format Message Renderer.

Renders notification templates into channel-specific output:
  - Plain text (SMS, Voice)
  - HTML (Email)
  - Markdown (Slack, Teams)
  - Rich cards (Teams adaptive cards, Slack blocks)
  - JSON payloads (Webhooks)
"""

import re
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.modules.agents.notification.models import NotificationChannel, RenderedMessage
from app.modules.agents.notification.templates import NotificationTemplate

log = get_logger("agents.notification.renderer")


def _substitute(template_str: str, variables: dict[str, Any]) -> str:
    """Replace {{variable}} placeholders with values from the variables dict."""

    def replacer(match: re.Match) -> str:
        key = match.group(1).strip()
        value = variables.get(key, f"[{key}]")
        return str(value)

    return re.sub(r"\{\{(\w+)\}\}", replacer, template_str)


class MessageRenderer:
    """
    Produces channel-specific RenderedMessage objects from a template and variables.
    Each channel receives the format most appropriate for it.
    """

    def render(
        self,
        template: NotificationTemplate,
        channel: NotificationChannel,
        variables: dict[str, Any],
        locale: str = "en",
    ) -> RenderedMessage:
        """
        Render a notification template for a specific channel.

        Args:
            template: NotificationTemplate to render.
            channel: Target delivery channel.
            variables: Variable substitutions for template placeholders.
            locale: Locale code for localization (default: 'en').

        Returns:
            RenderedMessage ready for dispatch.
        """
        # Ensure timestamp is always present
        variables.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
        variables.setdefault("event_type", template.event_type)
        variables.setdefault("details", "See ABHEDYA dashboard for full details.")

        # Convert list actions to formatted strings
        if "actions" in variables and isinstance(variables["actions"], list):
            variables["actions_html"] = "".join(
                f"<li>{a}</li>" for a in variables["actions"]
            )
            variables["actions"] = "\n".join(f"• {a}" for a in variables["actions"])
        else:
            variables.setdefault("actions", "Refer to ABHEDYA dashboard.")
            variables.setdefault("actions_html", "<li>Refer to ABHEDYA dashboard.</li>")

        subject = _substitute(template.subject_template, variables)
        body_text = _substitute(template.body_text_template, variables)
        body_html = _substitute(template.body_html_template, variables)
        body_md = _substitute(template.body_markdown_template, variables)

        # Rich card for Teams / Slack
        rich_card = self._build_rich_card(template, variables, channel)

        # For SMS / Voice, truncate to concise plain text (160 chars for SMS)
        if channel in (NotificationChannel.SMS,):
            sms_body = self._truncate_for_sms(body_text)
            return RenderedMessage(
                subject=subject,
                body_text=sms_body,
                body_html="",
                body_markdown="",
                rich_card={},
                channel=channel,
                locale=locale,
                template_id=template.template_id,
                template_version=template.version,
            )

        if channel == NotificationChannel.VOICE:
            return RenderedMessage(
                subject=subject,
                body_text=self._truncate_for_voice(body_text),
                body_html="",
                body_markdown="",
                rich_card={},
                channel=channel,
                locale=locale,
                template_id=template.template_id,
                template_version=template.version,
            )

        if channel in (NotificationChannel.SLACK,):
            return RenderedMessage(
                subject=subject,
                body_text=body_text,
                body_html="",
                body_markdown=body_md,
                rich_card=rich_card,
                channel=channel,
                locale=locale,
                template_id=template.template_id,
                template_version=template.version,
            )

        if channel in (NotificationChannel.TEAMS,):
            return RenderedMessage(
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                body_markdown=body_md,
                rich_card=rich_card,
                channel=channel,
                locale=locale,
                template_id=template.template_id,
                template_version=template.version,
            )

        # Default: full message
        return RenderedMessage(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            body_markdown=body_md,
            rich_card=rich_card,
            channel=channel,
            locale=locale,
            template_id=template.template_id,
            template_version=template.version,
        )

    def _truncate_for_sms(self, text: str, max_chars: int = 160) -> str:
        """Truncate notification body to SMS character limit."""
        return text[:max_chars - 3] + "..." if len(text) > max_chars else text

    def _truncate_for_voice(self, text: str, max_words: int = 50) -> str:
        """Reduce notification to a concise voice-readable script."""
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + ". Please check ABHEDYA for details."
        return text

    def _build_rich_card(
        self,
        template: NotificationTemplate,
        variables: dict[str, Any],
        channel: NotificationChannel,
    ) -> dict[str, Any]:
        """Build a rich card payload for Teams Adaptive Cards or Slack Block Kit."""
        if channel == NotificationChannel.TEAMS:
            return {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": _substitute(template.subject_template, variables),
                     "weight": "Bolder", "size": "Medium"},
                    {"type": "TextBlock", "text": _substitute(template.body_text_template, variables),
                     "wrap": True},
                ],
                "actions": [
                    {"type": "Action.OpenUrl", "title": "View in ABHEDYA",
                     "url": f"https://abhedya.plant.example/events/{variables.get('incident_id', '')}"},
                ],
            }
        elif channel == NotificationChannel.SLACK:
            return {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text",
                                 "text": _substitute(template.subject_template, variables)},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn",
                                 "text": _substitute(template.body_markdown_template, variables)},
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {"type": "button", "text": {"type": "plain_text", "text": "Acknowledge"},
                             "value": f"ack:{variables.get('incident_id', '')}",
                             "style": "danger"},
                        ],
                    },
                ]
            }
        return {}
