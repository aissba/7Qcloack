"""
User-Agent parser — detects device type and OS from the UA string.

device_type : "mobile" | "tablet" | "desktop" | "bot" | "unknown"
os          : "android" | "ios" | "windows" | "macos" | "linux" | "other"

device_filter values stored per domain:
  "all"     → allow every real device
  "mobile"  → only mobile + tablet
  "desktop" → only desktop
  "android" → only Android devices
  "ios"     → only iOS devices
  "windows" → only Windows desktops
  "macos"   → only macOS desktops
"""


class UAResult:
    __slots__ = ("device_type", "os")

    def __init__(self, device_type: str, os: str):
        self.device_type = device_type  # mobile | tablet | desktop | bot | unknown
        self.os = os                    # android | ios | windows | macos | linux | other


def parse(user_agent: str) -> UAResult:
    ua = (user_agent or "").lower()

    # ── Bot / crawler detection ────────────────────────────────────────────────
    bot_keywords = (
        "bot", "crawl", "spider", "slurp", "facebook", "pinterest",
        "whatsapp", "telegram", "twitterbot", "linkedinbot", "googlebot",
        "bingbot", "yandex", "baidu", "duckduck", "semrush", "ahrefsbot",
        "mj12bot", "dotbot", "petalbot", "applebot", "headless",
    )
    if any(k in ua for k in bot_keywords):
        return UAResult("bot", _detect_os(ua))

    # ── Mobile / Tablet ────────────────────────────────────────────────────────
    if "ipad" in ua:
        return UAResult("tablet", "ios")
    if "android" in ua and "mobile" not in ua:
        return UAResult("tablet", "android")
    if any(k in ua for k in ("iphone", "ipod")):
        return UAResult("mobile", "ios")
    if "android" in ua and "mobile" in ua:
        return UAResult("mobile", "android")
    if any(k in ua for k in ("windows phone", "iemobile", "wpdesktop")):
        return UAResult("mobile", "windows")
    if any(k in ua for k in ("blackberry", "bb10", "symbian", "nokia", "opera mini", "opera mobi")):
        return UAResult("mobile", "other")

    # ── Desktop ────────────────────────────────────────────────────────────────
    os = _detect_os(ua)
    if os in ("windows", "macos", "linux"):
        return UAResult("desktop", os)

    return UAResult("unknown", "other")


def _detect_os(ua: str) -> str:
    if "windows" in ua:
        return "windows"
    if "macintosh" in ua or "mac os x" in ua:
        return "macos"
    if "android" in ua:
        return "android"
    if "iphone" in ua or "ipad" in ua or "ipod" in ua:
        return "ios"
    if "linux" in ua:
        return "linux"
    return "other"


# ── Filter decision ────────────────────────────────────────────────────────────

def is_allowed(ua_result: UAResult, device_filter: str) -> bool:
    """
    Return True if the visitor's device matches the domain's device_filter.

    device_filter values:
      all      → always True (except bots)
      mobile   → mobile or tablet
      desktop  → desktop
      android  → os == android
      ios      → os == ios
      windows  → os == windows
      macos    → os == macos
    """
    # Bots always blocked regardless of filter
    if ua_result.device_type == "bot":
        return False

    f = (device_filter or "all").lower()

    if f == "all":
        return ua_result.device_type not in ("bot", "unknown")
    if f == "mobile":
        return ua_result.device_type in ("mobile", "tablet")
    if f == "desktop":
        return ua_result.device_type == "desktop"
    if f in ("android", "ios", "windows", "macos"):
        return ua_result.os == f

    return True
