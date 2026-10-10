"""Self-contained OAuth callback page. No user input, remote assets, or scripts."""

import base64
from functools import lru_cache
from pathlib import Path

CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
    "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
)


@lru_cache(maxsize=2)
def render_callback(success=True):
    logo = Path(__file__).parents[1] / "desktop" / "assets" / "aedrova.png"
    image = base64.b64encode(logo.read_bytes()).decode("ascii")
    heading = "Your space is waiting." if success else "Let’s try that again."
    description = (
        "Return to Aedrova to finish signing in. You can close this tab."
        if success
        else "Sign-in was not completed. Return to Aedrova to try again."
    )
    status = "CONTINUE IN THE APP" if success else "SIGN-IN PAUSED"
    # All interpolated content is fixed application text or a local base64 PNG.
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Aedrova · Your space to build</title>
<style>
:root {{color-scheme: light dark; --bg:#f5f5f7; --ink:#1d1d1f; --muted:#6e6e73;
--glass:rgba(255,255,255,.72); --line:rgba(0,0,0,.06); --shadow:rgba(34,45,80,.08)}}
* {{box-sizing:border-box}} body {{margin:0; min-height:100svh; display:grid; place-items:center;
background:var(--bg);
 color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;

-webkit-font-smoothing:antialiased; padding:32px 20px; overflow-x:hidden}}
.aura {{position:fixed;
 width:min(780px,100vw);
 height:580px;
 border-radius:50%;
 pointer-events:none;

background:radial-gradient(ellipse at 24% 46%,rgba(136,220,202,.25),transparent 52%),
radial-gradient(ellipse at 72% 30%,rgba(170,157,241,.22),transparent 52%),
radial-gradient(ellipse at 52% 77%,rgba(124,171,241,.2),transparent 55%);
filter:blur(48px)}}
main {{position:relative; width:min(100%,560px); text-align:center; border-radius:24px;
padding:34px 48px 44px; background:var(--glass); border:1px solid var(--line);
box-shadow:0 24px 90px var(--shadow),inset 0 1px 0 rgba(255,255,255,.35);
backdrop-filter:blur(24px);
 -webkit-backdrop-filter:blur(24px);
 animation:arrive .65s ease-out both}}
.brand {{font-size:18px; font-weight:600; letter-spacing:-.5px; margin:0}}
.mark {{width:160px;height:160px; position:relative; margin:24px auto 20px}}
.mark img {{position:absolute;
width:400px;
height:400px;
 max-width:none;
left:50%;
top:50%;
transform:translate(-50%,-50%)}}
.kicker {{font-size:11px;font-weight:600;letter-spacing:2px;color:var(--muted);margin:0 0 18px}}
h1 {{font-size:clamp(32px,6vw,42px);
 font-weight:600;
 line-height:1.08;
 letter-spacing:-1.5px;
 margin:0 0 20px}}
.description {{font-size:16px;line-height:1.65;color:var(--muted);max-width:340px;margin:0 auto}}
.hint {{margin:30px 0 0;
 padding-top:24px;
border-top:1px solid var(--line);
font-size:13px;
line-height:1.6;
color:var(--muted)}}
.hint strong {{color:var(--ink);font-weight:500}}
footer {{position:relative;
margin-top:28px;
font-size:12px;
letter-spacing:.1px;
color:var(--muted);
text-align:center}}
.wrap {{display:flex;align-items:center;flex-direction:column;width:100%}}
@keyframes arrive {{from {{opacity:0;
transform:translateY(10px)}} to {{opacity:1;
transform:translateY(0)}}}}
@media(prefers-color-scheme:dark) {{:root {{--bg:#000;--ink:#f5f5f7;--muted:#a1a1a6;
--glass:rgba(28,28,30,.78);--line:rgba(255,255,255,.08);--shadow:rgba(0,0,0,.35)}}
main {{box-shadow:0 24px 90px var(--shadow),inset 0 1px 0 rgba(255,255,255,.06)}}}}
@media(max-width:420px) {{main {{padding:28px 24px 32px}} .mark {{margin-top:16px}}}}
@media(prefers-reduced-motion:reduce) {{main {{animation:none}}}}
@media(prefers-reduced-transparency:reduce) {{main {{background:var(--bg);backdrop-filter:none}}}}
</style></head><body><div class="aura" aria-hidden="true"></div>
<div class="wrap"><main aria-labelledby="title"><p class="brand">Aedrova</p>
<div class="mark"><img src="data:image/png;base64,{image}" alt="" aria-hidden="true"></div>
<p class="kicker">{status}</p><h1 id="title">{heading}</h1>
<p class="description">{description}</p>
<p class="hint">Switch to the <strong>Aedrova app</strong>
 in your Dock<br>or use <strong>⌘ Tab</strong>
 to return.</p>
</main><footer>Your team. Your ideas. One place to build.</footer></div></body></html>""".encode()
