"""notifications/__init__.py — Legacy alias, redirects to notification module.

The canonical module is app.modules.agents.notification
"""

from app.modules.agents.notification.notification_agent import NotificationAgent

__all__ = ["NotificationAgent"]
