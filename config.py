from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
NOTIFY_GROUP_ID: str = os.getenv("NOTIFY_GROUP_ID", "")
PROXYCHECK_API_KEY: str = os.getenv("PROXYCHECK_API_KEY", "")
IPINFO_API_TOKEN: str = os.getenv("IPINFO_API_TOKEN", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///cloak.db")
FLASK_HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT: int = int(os.getenv("PORT") or os.getenv("FLASK_PORT", "5000"))

# Default ISPs blocked on every new domain
DEFAULT_BLOCKED_ISPS: list[str] = [
    "Facebook Inc", "Facebook", "Facebook Ireland Ltd",
    "Facebook Singapore Pte Ltd.", "Facebook, Inc.", "Facebook Singapore Pte",
    "Facebook South Africa (Pty) Ltd", "Meta Platforms Ireland Limited",
    "CDN Facebook", "Facebook Inc.",
    "Amazon Corporate Services Pty Ltd", "Amazon Technologies", "Amazon",
    "Amazon Corporate Services Pty", "Amazon.com",
    "Amazon Data Services Ireland Ltd", "Amazon Web Services",
    "Amazon Wifi Servicos de Internet Ltda", "Amazon Data Services Brazil",
    "Amazon.com, Inc.", "Amazon Robotics LLC",
    "Amazon Data Services Ireland", "Amazon Web Services, LLC",
    "Amazon.com Tech Telecom", "Amazon Data Services Japan KK",
    "Amazon Corporate LLC",
    "Amazon Asia-Pacific Resources Private Limited",
    "Amazon Connection Technology Services (Beijing) Co",
    "Google", "Google Switzerland GmbH", "Google, LLC",
    "Google Peering at Global Switch SG", "Google Peering at Equinix SG",
    "Google Wi-Fi", "Google China Infotech Ou",
    "Google India's Corporate Network", "Google Corporate Network - Test",
    "Google Australia's Corporate Network", "Google Corporate Network Test",
    "Google CWB private VPN P2P", "Google Ireland Limited",
    "Google Corporate Network", "Google Cloud", "Google Fiber",
    "Googlebot", "Google Access LLC", "Google UK Limited", "Google Kenya",
    "Google LLC", "Google Fiber Inc.", "Google Proxy",
    "Digital Ocean", "Digital Ocean LLC", "Digital Ocean SRL",
    "Digital Ocean, Inc.",
    "Hetzner Online GmbH", "Hetzner", "Hetzner CC",
    "HETZNER (Pty) Ltd", "Hetzner-ZA",
    "Netstack Cloud Services", "Beget Ltd",
    "Kaspersky Lab AO", "Kaspersky Lab KDP",
    "Microsoft Corporation", "Microsoft Hosting",
    "Microsoft Deutschland MCIO GmbH",
    "Microsoft Mobile Alliance Internet Services Co., Ltd",
    "Microsoft Informatica Ltda", "Microsoft Limited", "Microsoft Azure",
    "Microsoft (China) Co., Ltd.",
    "Microsoft Mobile Alliance Internet Services Co., L",
    "Microsoft bingbot", "Microsoft Limited UK",
    "Microsoft (China) Co.",
    "Microsoft Mobile Alliance Internet Services Co.",
    "Microsoft Corp", "Microsoft French Call Center",
    "Microsoft GmbH ueber c/o Eurotel GmbH", "Microsoft",
    "Piggy Microsoft", "Piggyback Microsoft", "Piggyback For Microsoft",
    "Microsoft Singapore Pte. Ltd.", "Microsoft Corp, Tokyo",
    "Singapore Telecom/Microsoft Network", "Microsoft Mobile Oy",
    "OVH Hosting", "OVH Hosting LDA", "OVH Hosting Limited", "OVH Hosting Oy",
    "Cloudflare Sydney, LLC", "Cloudflare", "Cloudflare, Inc.",
    "CloudFlare Latin America S.R.L", "Cloudflare London, LLC",
    "CloudFlare Africa", "Cloudflare Inc", "Cloudflare London",
    "University of California", "TerraHost AS", "Web Hosted Group Ltd",
    "Zscaler", "Zscaler Switzerland GmbH", "ZSCALER, INC.",
    "Linode, LLC", "Linode", "Linode - Online Solution Int Ltd.",
    "Vultr Holdings LLC",
    "CenturyLink", "LEVEL3 / CENTURYLINK", "Centurylink Fiber Plus",
    "CenturyLink Ecuador",
    "QWARTA LLC", "Host Europe GmbH",
    "Hostinger International Limited", "Hostinger International Limited.",
    "IPXO",
    "ATN", "FTW", "VLL", "ASH", "RVA", "NCG", "NHA", "LDC", "CCO",
]
