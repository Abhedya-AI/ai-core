"""notification_agent.py — Compatibility shim for legacy notifications module.

The canonical implementation is in app.modules.agents.notification.notification_agent
"""

from app.modules.agents.notification.notification_agent import NotificationAgent

__all__ = ["NotificationAgent"]
