"""
/setsafe   parkside-fr https://safe-page.com   (optional — safe traffic served via safe_page.html)
/setmoney  parkside-fr https://money-page.com
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import require_flow, set_safe_url, set_money_url


async def cmd_setsafe(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setsafe parkside-fr https://safe-page.com`", parse_mode="Markdown")
        return
    flow_name, url = ctx.args[0].lower(), ctx.args[1]
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_safe_url(flow_name, url)
    await update.message.reply_text(f"✅ Safe URL for flow `{flow_name}` set to:\n`{url}`", parse_mode="Markdown")


async def cmd_setmoney(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setmoney parkside-fr https://money-page.com`", parse_mode="Markdown")
        return
    flow_name, url = ctx.args[0].lower(), ctx.args[1]
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_money_url(flow_name, url)
    await update.message.reply_text(f"✅ Money URL for flow `{flow_name}` set to:\n`{url}`", parse_mode="Markdown")


def register(app):
    app.add_handler(CommandHandler("setsafe",  cmd_setsafe))
    app.add_handler(CommandHandler("setmoney", cmd_setmoney))
