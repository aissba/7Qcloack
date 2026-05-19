"""
/generate    example.com  → create new token, return URL
/regenerate  example.com  → revoke all tokens, issue new one
/listlinks   example.com  → show all active tokens + created date
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    require_domain, generate_token, regenerate_token,
    get_active_links, token_url,
)


async def cmd_generate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/generate example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    token = generate_token(domain)
    url = token_url(domain, token)
    await update.message.reply_text(
        f"🔗 New token URL for `{domain}`:\n`{url}`", parse_mode="Markdown"
    )


async def cmd_regenerate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/regenerate example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    token = regenerate_token(domain)
    url = token_url(domain, token)
    await update.message.reply_text(
        f"🔄 Old tokens revoked. New URL for `{domain}`:\n`{url}`", parse_mode="Markdown"
    )


async def cmd_listlinks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/listlinks example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    tokens = get_active_links(domain)
    if not tokens:
        await update.message.reply_text(f"No active tokens for `{domain}`.", parse_mode="Markdown")
        return
    lines = "\n".join(
        f"• `{token_url(domain, t['token'])}` — {t['created_at'][:16]}"
        for t in tokens
    )
    await update.message.reply_text(
        f"*Active tokens for `{domain}`:*\n{lines}", parse_mode="Markdown"
    )


def register(app):
    app.add_handler(CommandHandler("generate",   cmd_generate))
    app.add_handler(CommandHandler("regenerate", cmd_regenerate))
    app.add_handler(CommandHandler("listlinks",  cmd_listlinks))
