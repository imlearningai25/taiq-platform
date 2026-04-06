"""
Activity tracking and notification utility.
Call `track(db, user, action, description)` after any significant user action.
It logs to the DB and optionally sends an email notification.
"""
import logging
from app.models.models import ActivityLog
from app.core.email import send_email
from app.core.config import settings

logger = logging.getLogger(__name__)

# Actions that trigger an email notification to the user
NOTIFY_ACTIONS = {
    "profile_basic_updated",
    "profile_professional_updated",
    "password_changed",
    "job_applied",
    "application_withdrawn",
    "job_saved",
}

ACTION_ICONS = {
    "registered": "🎉",
    "email_verified": "✅",
    "login": "🔐",
    "profile_basic_updated": "👤",
    "profile_professional_updated": "📝",
    "password_changed": "🔒",
    "job_applied": "📋",
    "application_withdrawn": "↩️",
    "job_saved": "❤️",
    "job_unsaved": "💔",
    "company_created": "🏢",
    "job_posted": "💼",
    "job_deleted": "🗑️",
}


async def track(db, user, action: str, description: str, extra: dict = None):
    """Log an activity and optionally email the user."""
    log = ActivityLog(
        user_id=user.id,
        action=action,
        description=description,
        extra=extra or {},
    )
    db.add(log)

    if action in NOTIFY_ACTIONS:
        try:
            html = _activity_email_html(user, action, description)
            await send_email(
                to=user.email,
                subject=f"TaIQ — Account Activity: {description}",
                html_body=html,
            )
        except Exception as e:
            logger.warning(f"Activity email failed for user {user.id}: {e}")


def _activity_email_html(user, action: str, description: str) -> str:
    icon = ACTION_ICONS.get(action, "ℹ️")
    name = user.full_name or "there"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f4f6fb;font-family:'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(10,15,30,.1);">
        <tr>
          <td style="background:linear-gradient(135deg,#050c1f 0%,#0d2654 60%,#1a3a7a 100%);padding:32px 40px;text-align:center;">
            <span style="color:white;font-size:22px;font-weight:800;font-family:Georgia,serif;">TaIQ</span>
            <p style="color:rgba(255,255,255,.6);font-size:12px;margin:6px 0 0;">Account Activity Notification</p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;">
            <p style="font-size:28px;text-align:center;margin:0 0 16px;">{icon}</p>
            <h2 style="font-size:20px;font-weight:700;color:#0a0f1e;margin:0 0 8px;">Hi {name},</h2>
            <p style="color:#384060;font-size:15px;line-height:1.6;margin:0 0 20px;">
              We detected the following activity on your TaIQ account:
            </p>
            <div style="background:#f4f6fb;border-radius:10px;padding:16px 20px;margin-bottom:24px;">
              <p style="margin:0;font-size:15px;font-weight:600;color:#0a0f1e;">{description}</p>
            </div>
            <p style="color:#6b7899;font-size:13px;line-height:1.6;margin:0;">
              If this wasn't you, please change your password immediately and contact support at
              <a href="mailto:support@taiq.us" style="color:#0052cc;">support@taiq.us</a>.
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f4f6fb;border-top:1px solid #c8d0e4;padding:20px 40px;text-align:center;">
            <p style="color:#6b7899;font-size:12px;margin:0;">© 2025 TaIQ Inc.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
