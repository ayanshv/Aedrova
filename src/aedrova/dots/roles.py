"""Curated role connector sets. Recommendations never confer provider access."""

ROLES = {
    "builder": ("Builder", ("github", "supabase"), ("vercel", "sentry")),
    "designer": ("Designer", ("figma", "notion"), ("google_drive",)),
    "marketing": (
        "Marketing",
        ("instagram", "tiktok"),
        ("meta_ads", "google_analytics", "posthog", "notion"),
    ),
    "finance": ("Finance", ("stripe",), ("quickbooks", "google_sheets", "notion")),
    "research": ("Research", ("llm", "search", "notion"), ("google_drive", "posthog")),
    "product": (
        "Product",
        ("notion", "posthog"),
        (
            "github",
            "supabase",
            "figma",
            "stripe",
            "search",
            "llm",
            "instagram",
            "tiktok",
            "google_drive",
        ),
    ),
}
NAMES = {
    "github": "GitHub",
    "supabase": "Supabase",
    "vercel": "Vercel",
    "sentry": "Sentry",
    "figma": "Figma",
    "notion": "Notion",
    "google_drive": "Google Drive",
    "instagram": "Instagram",
    "tiktok": "TikTok",
    "meta_ads": "Meta Ads",
    "google_analytics": "Google Analytics",
    "posthog": "PostHog",
    "stripe": "Stripe",
    "quickbooks": "QuickBooks",
    "google_sheets": "Google Sheets",
    "llm": "AI model",
    "search": "Web search",
}


def role_for(text):
    text = str(text or "").lower()
    prefix = text.split(" · ", 1)[0].strip()
    aliases = {"engineering": "builder", "design": "designer"}
    if prefix in ROLES:
        return prefix
    if prefix in aliases:
        return aliases[prefix]
    for key, words in {
        "designer": ("design", "creative"),
        "marketing": ("marketing", "social", "sales"),
        "finance": ("finance", "revenue", "billing", "accounting"),
        "research": ("research", "analyst"),
        "product": ("product", "roadmap"),
    }.items():
        if any(word in text for word in words):
            return key
    return "builder"


def recommendation_set(role):
    _, core, additional = ROLES[role if role in ROLES else "builder"]
    return tuple(dict.fromkeys((*core, *additional)))


def stored_role(role, purpose):
    label = ROLES[role][0]
    return label + (" · " + purpose.strip() if purpose.strip() else "")


def purpose_from(text):
    prefix, separator, purpose = str(text or "").partition(" · ")
    if separator and prefix.lower() in ROLES:
        return purpose
    return "" if prefix.lower() in ROLES else str(text or "")
