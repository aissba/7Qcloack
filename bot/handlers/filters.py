"""
/setcountry   example.com US,CA,GB
/setthreshold example.com 75
/blockisp     example.com "Amazon Web Services"
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import require_domain, set_countries, set_threshold, add_blocked_isp


async def cmd_setcountry(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setcountry example.com US,CA,GB`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    countries = ctx.args[1].upper()
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_countries(domain, countries)
    await update.message.reply_text(
        f"✅ Allowed countries for `{domain}`: `{countries}`", parse_mode="Markdown"
    )


async def cmd_setthreshold(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setthreshold example.com 75`", parse_mode="Markdown")
        return
    domain = ctx.args[0].lower()
    try:
        threshold = int(ctx.args[1])
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_threshold(domain, threshold)
    await update.message.reply_text(
        f"✅ Threshold for `{domain}` set to `{threshold}`", parse_mode="Markdown"
    )


async def cmd_blockisp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            'Usage: `/blockisp example.com "Amazon Web Services"`', parse_mode="Markdown"
        )
        return
    domain = ctx.args[0].lower()
    isp_name = " ".join(ctx.args[1:])
    try:
        require_domain(domain)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    add_blocked_isp(domain, isp_name)
    await update.message.reply_text(
        f"🚫 ISP `{isp_name}` blocked for `{domain}`", parse_mode="Markdown"
    )


def register(app):
    app.add_handler(CommandHandler("setcountry",   cmd_setcountry))
    app.add_handler(CommandHandler("setthreshold", cmd_setthreshold))
    app.add_handler(CommandHandler("blockisp",     cmd_blockisp))
