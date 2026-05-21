"""
/setcountry   parkside-fr US,CA,GB
/setthreshold parkside-fr 20000
/blockisp     parkside-fr "Amazon Web Services"
"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from core.domain_manager import require_flow, set_countries, set_threshold, add_blocked_isp


async def cmd_setcountry(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setcountry parkside-fr US,CA,GB`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    countries = ctx.args[1].upper()
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_countries(flow_name, countries)
    await update.message.reply_text(
        f"✅ Allowed countries for flow `{flow_name}`: `{countries}`", parse_mode="Markdown"
    )


async def cmd_setthreshold(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text("Usage: `/setthreshold parkside-fr 20000`", parse_mode="Markdown")
        return
    flow_name = ctx.args[0].lower()
    try:
        threshold = int(ctx.args[1])
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    set_threshold(flow_name, threshold)
    await update.message.reply_text(
        f"✅ Threshold for flow `{flow_name}` set to `{threshold}`", parse_mode="Markdown"
    )


async def cmd_blockisp(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            'Usage: `/blockisp parkside-fr "Amazon Web Services"`', parse_mode="Markdown"
        )
        return
    flow_name = ctx.args[0].lower()
    isp_name  = " ".join(ctx.args[1:])
    try:
        require_flow(flow_name)
    except ValueError as e:
        await update.message.reply_text(str(e), parse_mode="Markdown")
        return
    add_blocked_isp(flow_name, isp_name)
    await update.message.reply_text(
        f"🚫 ISP `{isp_name}` blocked for flow `{flow_name}`", parse_mode="Markdown"
    )


def register(app):
    app.add_handler(CommandHandler("setcountry",   cmd_setcountry))
    app.add_handler(CommandHandler("setthreshold", cmd_setthreshold))
    app.add_handler(CommandHandler("blockisp",     cmd_blockisp))
