"""Curated role connector sets. Recommendations never confer provider access."""

ROLES = {
    "builder": ("Builder", ("github", "supabase"), ("vercel", "sentry")),
    "designer": ("Designer", ("figma", "notion"), ("google_drive",)),
    "marketing": (
        "Marketing",
        ("buffer",),
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
    "buffer": "Buffer",
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


RESPONSIBILITIES = {
    "builder": (
        "Explain the codebase, repository changes, open issues and deployments.",
        "Spot risk in recent changes and say what to check before shipping.",
        "Propose changes and next steps. Execution and approvals stay with the team.",
    ),
    "designer": (
        "Describe design files and shared pages: their structure, frames and labels.",
        "Review design decisions against what the team has said it wants.",
        "Suggest improvements and flag inconsistencies, without claiming to see images.",
    ),
    "marketing": (
        "Plan audiences, campaigns and calendars, and draft platform-specific copy.",
        "Offer variations, hashtags and calls to action, and label every assumption.",
        "Drafts are never publication consent; the team reviews and approves in Social.",
    ),
    "finance": (
        "Report balances and money facts exactly as the connected account shows them.",
        "Explain what a number does and does not mean. It is not accounting or tax advice.",
        "Flag anything that looks off and ask the right person to confirm.",
    ),
    "research": (
        "Investigate a question with live sources and say how reliable each one is.",
        "Compare options and summarize findings with the links you actually used.",
        "Separate what is established from what is claimed or uncertain.",
    ),
    "product": (
        "Keep track of what the team is building, why, and what has been decided.",
        "Connect requests to the roadmap, open work and shared evidence.",
        "Turn discussion into clear next steps and open questions.",
    ),
}

SOURCE_SCOPE = {
    "github": "repository details, recent commits, open issues and deployments",
    "supabase": "project health and region only; never rows, SQL or keys",
    "vercel": "project details and recent deployments",
    "figma": "file structure: the top pages and their frames, not images",
    "notion": "one shared page and its first 20 blocks, not nested pages",
    "stripe": "account balance only; no customer data",
    "instagram": "the professional profile and recent posts",
    "tiktok": "the authorized profile and recent public videos",
    "search": "live web research on its saved topic, with sources",
    "buffer": "the connected organization and its social channels",
}
