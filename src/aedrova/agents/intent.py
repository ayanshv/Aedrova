"""Tell a request to build or change software from a question about it.

A request like "can you build a python calculator locally?" must start a real build in the
person's project, not paste code into the chat. Questions, explanations and everyday writing
("write an email", "make a summary") stay replies.
"""

import re

OPENERS = (
    r"(?:(?:hey|hi|ok|okay|so|then|now|also|and|alright)[,\s]+)*"
    r"(?:please\s+)?"
    r"(?:(?:can|could|would|will)\s+(?:you|u|we)\s+(?:please\s+)?"
    r"|(?:i|we)\s+(?:need|want|would\s+like|'d\s+like|’d\s+like)\s+(?:you\s+)?to\s+"
    r"|(?:i|we)\s+(?:need|want)\s+you\s+to\s+"
    r"|go\s+ahead\s+and\s+|let(?:'|’)?s\s+|help\s+(?:me|us)\s+(?:to\s+)?"
    r"|i(?:'|’)d\s+like\s+you\s+to\s+)?"
)
STRONG = (
    r"build|implement|refactor|scaffold|debug|deploy|compile|program|develop|code|prototype|"
    r"architect|bootstrap"
)
WEAK = (
    r"create|make|write|generate|add|set\s+up|setup|fix|update|change|modify|edit|rename|"
    r"delete|remove|convert|port|install|integrate|improve|optimi[sz]e|design|put\s+together"
)
SOFTWARE = re.compile(
    r"\b(?:app|apps|application|program|script|scripts|calculator|website|web\s*site|site|"
    r"web\s*page|page|landing\s+page|component|function|functions|class|classes|module|package|"
    r"library|api|endpoint|server|backend|back-end|frontend|front-end|ui|interface|feature|"
    r"bug|bugs|test|tests|file|files|project|repo|repository|codebase|code|cli|command[-\s]line|"
    r"tool|bot|game|plugin|extension|widget|dashboard|form|database|schema|migration|query|"
    r"service|html|css|python|javascript|typescript|react|swift|rust|java|node|flask|django|"
    r"tkinter|sql|json|regex|algorithm|workflow|pipeline|config|dockerfile|readme|button|"
    r"navbar|login|signup|theme|dark\s+mode|animation|template|prompt|webhook|scraper)\b",
    re.IGNORECASE,
)
LOCAL = re.compile(
    r"\b(?:locally|on\s+my\s+(?:computer|mac|machine|laptop)|in\s+my\s+(?:project|repo|"
    r"codebase|folder)|\.py|\.js|\.ts|\.html|\.swift)\b",
    re.IGNORECASE,
)
EXPLAIN = re.compile(
    r"^(?:how|what|why|when|where|who|which|is|are|do|does|did|should|explain|describe|"
    r"summari[sz]e|tell|show\s+me\s+how|list|compare|review|analy[sz]e|translate|define|"
    r"give\s+me\s+(?:a\s+)?(?:summary|overview|explanation))\b",
    re.IGNORECASE,
)
VERB = re.compile(
    r"^" + OPENERS + r"(?P<verb>(?:" + STRONG + r")|(?:" + WEAK + r"))\b(?P<rest>.*)$",
    re.IGNORECASE | re.DOTALL,
)
STRONG_VERB = re.compile(r"^(?:" + STRONG + r")$", re.IGNORECASE)
WANT = re.compile(
    r"^" + OPENERS + r"(?:i|we)\s+(?:need|want)\s+(?:a|an|the|some)\s+(?P<rest>.+)$",
    re.IGNORECASE | re.DOTALL,
)


def wants_build(text):
    """True when the message asks the agent to create or change software."""
    value = re.sub(r"```[\s\S]*?```|`[^`]*`", " code ", str(text or ""))
    value = " ".join(value.split())
    if not value or len(value) > 4000:
        return False
    stripped = re.sub(r"^" + OPENERS, "", value, count=1, flags=re.IGNORECASE)
    if EXPLAIN.match(stripped) or EXPLAIN.match(value):
        return False
    if re.search(r"\b(?:don't|do not|dont|never)\b", value, re.IGNORECASE):
        return False
    wanted = WANT.match(value)
    if wanted:
        return bool(SOFTWARE.search(wanted["rest"]))
    match = VERB.match(value)
    if not match or not match["rest"].strip():
        return False
    if STRONG_VERB.match(match["verb"].strip()):
        return True
    return bool(SOFTWARE.search(match["rest"]) or LOCAL.search(match["rest"]))
