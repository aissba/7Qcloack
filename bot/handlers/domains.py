"""
Flow management commands:

/newflow     parkside-fr
/deleteflow  parkside-fr
/listflows
/setdomain   parkside-fr example.com
/previewflow parkside-fr
/stats       parkside-fr
/logs        parkside-fr
/checkip     1.2.3.4
"""
import ipaddress
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import (
    add_flow, remove_flow, get_all_flows, require_flow,
    get_active_links, token_url, set_domain,
)
from core.ipgeo import lookup as geo_lookup
from db.models import visit_stats, visit_logs


async def cmd_newflow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/newflow parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    if add_flow(flow_name):
        await update.message.reply_text(
            f"✅ Flow `{flow_name}` created.\n\n"
            f"Next steps:\n"
            f"1. `/setdomain {flow_name} example.com`\n"
            f"2. `/setmoney {flow_name} https://offer.com`\n"
            f"3. `/setcountry {flow_name} US,CA,GB`\n"
            f"4. `/setdevice {flow_name} mobile`\n"
            f"5. `/generate {flow_name}`",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(f"⚠️ Flow `{flow_name}` already exists.", parse_mode="Markdown")


async def cmd_deleteflow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/deleteflow parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    if remove_flow(flow_name):
        await update.message.reply_text(f"🗑 Flow `{flow_name}` deleted.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Flow `{flow_name}` not found.", parse_mode="Markdown")


async def cmd_listflows(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = get_all_flows()
    if not rows:
        await update.message.reply_text("No flows configured yet. Use `/newflow <name>` to create one.", parse_mode="Markdown")
        return
    lines = []
    for r in rows:
        domain  = r["domain"] or "_(no domain)_"
        status  = "✅" if (r["domain"] and r["money_url"]) else "⚠️"
        lines.append(f"{status} `{r['flow_name']}` — {domain}")
    await update.message.reply_text(f"*Cloak Flows ({len(rows)}):*\n\n" + "\n".join(lines), parse_mode="Markdown")


async def cmd_setdomain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setdomain parkside-fr example.com`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    domain    = ctx.args[1].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_domain(flow_name, domain)
    await update.message.reply_text(
        f"✅ Domain for flow `{flow_name}` set to `{domain}`", parse_mode="Markdown"
    )


async def cmd_previewflow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/previewflow parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        row = require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return

    domain    = row["domain"] or "_(not set)_"
    safe      = row["safe_url"]   or "_(safe_page.html served locally)_"
    money     = row["money_url"]  or "_(not set)_"
    countries = row["countries"]  or "_(all)_"
    device    = row["device_filter"] or "all"
    threshold = row["threshold"]
    created   = row["created_at"][:16] if row["created_at"] else "?"

    tokens = get_active_links(flow_name)
    if tokens and row["domain"]:
        t_url = token_url(row["domain"], tokens[0]["token"])
    else:
        t_url = "_(no token yet — use /generate)_"

    is_active = bool(row["domain"] and row["money_url"] and tokens)
    status = "✅ Active" if is_active else "⚠️  Incomplete setup"

    text = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Flow: {flow_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Domain    : `{domain}`\n"
        f"Safe URL  : {safe}\n"
        f"Money URL : {money}\n"
        f"Countries : `{countries}`\n"
        f"Threshold : `{threshold}`\n"
        f"Device    : `{device}`\n"
        f"Token URL : `{t_url}`\n"
        f"Status    : {status}\n"
        f"Created   : `{created}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/stats parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    s = visit_stats(flow_name)
    pct = f"{round(s['money']/s['total']*100)}%" if s["total"] else "0%"
    text = (
        f"📊 *Stats: {flow_name}*\n\n"
        f"Total visits : `{s['total']}`\n"
        f"🟢 Money     : `{s['money']}`\n"
        f"🔴 Safe      : `{s['safe']}`\n"
        f"Conversion   : `{pct}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: `/logs parkside-fr`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    rows = visit_logs(flow_name, limit=15)
    if not rows:
        await update.message.reply_text(f"No logs for flow `{flow_name}` yet.", parse_mode="Markdown")
        return
    lines = "\n".join(
        f"`{r['created_at'][5:16]}` {'🟢' if r['action']=='money' else '🔴'} "
        f"{r['country_code'] or '??'} {r['device_type'] or '?'} `{r['ip']}`"
        for r in rows
    )
    await update.message.reply_text(
        f"📋 *Logs: {flow_name}* (last 15)\n\n{lines}", parse_mode="Markdown"
    )


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
        f"🔍 *IP Info: `{ip}`*\n\n"
        f"Country : {info.get('country', 'N/A')} ({info.get('country_code', '?')})\n"
        f"ISP     : {info.get('isp', 'N/A')}\n"
        f"Org     : {info.get('org', 'N/A')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


def register(app):
    app.add_handler(CommandHandler("newflow",    cmd_newflow))
    app.add_handler(CommandHandler("deleteflow", cmd_deleteflow))
    app.add_handler(CommandHandler("listflows",  cmd_listflows))
    app.add_handler(CommandHandler("setdomain",  cmd_setdomain))
    app.add_handler(CommandHandler("previewflow",cmd_previewflow))
    app.add_handler(CommandHandler("stats",      cmd_stats))
    app.add_handler(CommandHandler("logs",       cmd_logs))
    app.add_handler(CommandHandler("checkip",    cmd_checkip))
