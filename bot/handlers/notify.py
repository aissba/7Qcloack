"""
/setgroup    -1003570299128       (sets group for ALL domains)
/notifyon    example.com
/notifyoff   example.com
/notifylevel example.com all|money|safe
/testnotify  example.com          (sends a test message to the group immediately)
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    get_all_domains, require_domain, get_domain,
    set_notify_group, set_notify_enabled, set_notify_level,
)

logger = logging.getLogger(__name__)


async def cmd_setgroup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/setgroup -1003570299128`", parse_mode="Markdown")
        return
    group_id = ctx.args[0]
    domains = get_all_domains()
    for row in domains:
        set_notify_group(row["domain"], group_id)
    count = len(domains)
    await update.message.reply_text(
        f"✅ Notification group `{group_id}` applied to {count} domain(s).", parse_mode="Markdown"
    )


async def cmd_notifyon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/notifyon example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_enabled(domain, True)
    await update.message.reply_text(f"🔔 Notifications enabled for `{domain}`", parse_mode="Markdown")


async def cmd_notifyoff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/notifyoff example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_enabled(domain, False)
    await update.message.reply_text(f"🔕 Notifications disabled for `{domain}`", parse_mode="Markdown")


async def cmd_notifylevel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: `/notifylevel example.com all|money|safe`", parse_mode="Markdown"
        )
        return
    domain = ctx.args[0].lower()
    level = ctx.args[1].lower()
    if level not in ("all", "money", "safe"):
        await update.message.reply_text("Level must be `all`, `money`, or `safe`.", parse_mode="Markdown")
        return
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_level(domain, level)
    await update.message.reply_text(
        f"✅ Notify level for `{domain}` set to `{level}`", parse_mode="Markdown"
    )


async def cmd_testnotify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Send a test notification to the configured group right now."""
    if not ctx.args:
        await update.message.reply_text("Usage: `/testnotify example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        row = require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    group_id = row["notify_group"]
    notify_enabled = row["notify_enabled"]

    if not group_id:
        await update.message.reply_text(
            "❌ No group set. Run `/setgroup -1003570299128` first.", parse_mode="Markdown"
        )
        return

    # Send test regardless of notify_enabled so you can always verify connectivity
    try:
        chat_id = int(group_id)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🔔 *Test notification* for `{domain}`\n\n"
                f"If you see this, notifications are working correctly.\n"
                f"notify\\_enabled = `{bool(notify_enabled)}`\n"
                f"group\\_id = `{group_id}`"
            ),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            f"✅ Test message sent to group `{group_id}`", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Failed to send: `{e}`", parse_mode="Markdown"
        )


async def send_visit_notification(bot, domain: str, action: str, ip: str, geo: dict, proxy: bool, device_type: str = "", os: str = ""):
    """
    Scheduled by app/routes.py onto the bot's event loop after each visit.
    """
    row = get_domain(domain)
    if not row:
        logger.warning("send_visit_notification: domain %s not found", domain)
        return

    if not row["notify_enabled"]:
        logger.debug("Notifications disabled for %s", domain)
        return

    group_id = row["notify_group"]
    if not group_id:
        logger.warning("No notify_group set for %s", domain)
        return

    level = row["notify_level"] or "all"
    if level != "all" and level != action:
        logger.debug("Skipping notification: level=%s action=%s", level, action)
        return

    flag = "🟢" if action == "money" else "🔴"
    proxy_tag = " 🕵️ *proxy/VPN*" if proxy else ""

    # Device icon
    device_icon = {"mobile": "📱", "tablet": "📟", "desktop": "🖥", "bot": "🤖"}.get(device_type, "❓")
    os_label    = {"android": "Android", "ios": "iOS", "windows": "Windows", "macos": "macOS", "linux": "Linux"}.get(os, os or "?")

    text = (
        f"{flag} *{action.upper()}* visit on `{domain}`{proxy_tag}\n"
        f"IP      : `{ip}`\n"
        f"Country : {geo.get('country', 'N/A')} ({geo.get('country_code', '?')})\n"
        f"ISP     : {geo.get('isp', 'N/A')}\n"
        f"Device  : {device_icon} {device_type or '?'} / {os_label}"
    )

    try:
        chat_id = int(group_id)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        logger.info("Notification sent to %s for %s action=%s", group_id, domain, action)
    except Exception as e:
        logger.error("Notification failed for %s → group %s: %s", domain, group_id, e)


def register(app):
    app.add_handler(CommandHandler("setgroup",    cmd_setgroup))
    app.add_handler(CommandHandler("notifyon",    cmd_notifyon))
    app.add_handler(CommandHandler("notifyoff",   cmd_notifyoff))
    app.add_handler(CommandHandler("notifylevel", cmd_notifylevel))
    app.add_handler(CommandHandler("testnotify",  cmd_testnotify))
