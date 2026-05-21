"""
/generate    parkside-fr  → create new token, return URL
/regenerate  parkside-fr  → revoke all tokens, issue new one
/listlinks   parkside-fr  → show all active tokens + created date
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    require_flow, generate_token, regenerate_token,
    get_active_links, token_url,
)


async def cmd_generate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/generate parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        row = require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    if not row["domain"]:
        await update.message.reply_text(
            f"❌ Flow `{flow_name}` has no domain set.\nRun `/setdomain {flow_name} example.com` first.",
            parse_mode="Markdown",
        )
        return
    token = generate_token(flow_name)
    url   = token_url(row["domain"], token)
    await update.message.reply_text(
        f"🔗 *New token URL for flow `{flow_name}`:*\n`{url}`", parse_mode="Markdown"
    )


async def cmd_regenerate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/regenerate parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        row = require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    if not row["domain"]:
        await update.message.reply_text(
            f"❌ Flow `{flow_name}` has no domain set.", parse_mode="Markdown"
        )
        return
    token = regenerate_token(flow_name)
    url   = token_url(row["domain"], token)
    await update.message.reply_text(
        f"🔄 Old tokens revoked. New URL for flow `{flow_name}`:\n`{url}`", parse_mode="Markdown"
    )


async def cmd_listlinks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/listlinks parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    tokens = get_active_links(flow_name)
    if not tokens:
        await update.message.reply_text(f"No active tokens for flow `{flow_name}`.", parse_mode="Markdown")
        return
    lines = "\n".join(
        f"• `{token_url(t['domain'], t['token'])}` — {t['created_at'][:16]}"
        for t in tokens
    )
    await update.message.reply_text(
        f"*Active tokens for `{flow_name}`:*\n{lines}", parse_mode="Markdown"
    )


def register(app):
    app.add_handler(CommandHandler("generate",   cmd_generate))
    app.add_handler(CommandHandler("regenerate", cmd_regenerate))
    app.add_handler(CommandHandler("listlinks",  cmd_listlinks))
