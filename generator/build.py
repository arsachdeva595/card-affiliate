#!/usr/bin/env python3
"""Programmatic SEO builder for Carrd affiliate pages.

Reads site.config.json + data/*.json and writes a static site to dist/.
No dependencies beyond the Python standard library.

    python3 generator/build.py
"""
import json
import re
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DIST = ROOT / "dist"
STATIC = ROOT / "static"

CFG = json.loads((ROOT / "site.config.json").read_text())
BASE = CFG["base_url"].rstrip("/")
AFF = CFG["affiliate_url"]
TODAY = date.today().isoformat()

HOWTO = json.loads((DATA / "howto.json").read_text())
COMPARE = json.loads((DATA / "compare.json").read_text())
USECASES = json.loads((DATA / "usecases.json").read_text())
PLANS = json.loads((DATA / "plans.json").read_text())

HOWTO_BY = {h["slug"]: h for h in HOWTO}
PAGES = []  # (path, priority) for the sitemap


def e(s):
    return escape(str(s), quote=True)


def aff_link(label, placement, cls="btn"):
    """Affiliate link. The data-* attributes feed the GA4 affiliate_click event."""
    return (
        f'<a class="{cls}" href="{e(AFF)}" rel="sponsored noopener" target="_blank" '
        f'data-aff="{e(placement)}">{e(label)}</a>'
    )


def cta_box(tier, placement, context=""):
    need = f"This needs <strong>Carrd {e(tier)}</strong>. " if tier and not tier.startswith("Free") else ""
    return f"""
<aside class="cta">
  <p>{need}{e(context) if context else "Carrd is the fastest way to get a good-looking one-page site live."}</p>
  {aff_link("Start your Carrd site →", placement)}
  <p class="fine">Pro plans start at a few dollars a year. <a href="/pricing/">Compare plans</a>.</p>
</aside>"""


def faq_html(faq):
    if not faq:
        return ""
    items = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    return f"<section><h2>FAQ</h2>{items}</section>"


def faq_schema(faq):
    if not faq:
        return None
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq
        ],
    }


def crumbs(trail):
    """trail: list of (name, path). Returns (html, schema)."""
    html = " › ".join(
        f'<a href="{p}">{e(n)}</a>' if i < len(trail) - 1 else f"<span>{e(n)}</span>"
        for i, (n, p) in enumerate(trail)
    )
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p} for i, (n, p) in enumerate(trail)
        ],
    }
    return f'<nav class="crumbs">{html}</nav>', schema


def page(path, title, description, body, schemas=(), priority="0.6", trail=None):
    """Wrap body in the layout and write dist/<path>/index.html."""
    canonical = BASE + path
    blocks = [s for s in schemas if s]
    crumb_html = ""
    if trail:
        crumb_html, crumb_schema = crumbs(trail)
        blocks.append(crumb_schema)
    blocks.append({
        "@context": "https://schema.org",
        "@type": "Article" if path != "/" else "WebSite",
        "headline": title,
        "name": title,
        "url": canonical,
        "dateModified": TODAY,
        "author": {"@type": "Organization", "name": CFG["author"]},
    })
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(b)}</script>' for b in blocks)
    ga = CFG.get("ga4_measurement_id", "")
    ga_tag = ""
    if ga and "XXXX" not in ga:
        ga_tag = f"""<script async src="https://www.googletagmanager.com/gtag/js?id={e(ga)}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{e(ga)}');</script>"""
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="article">
<link rel="stylesheet" href="/style.css">
{ga_tag}
{ld}
</head>
<body>
<header class="top"><a class="brand" href="/">{e(CFG["site_name"])}</a>
<nav><a href="/how-to/">Guides</a><a href="/for/">Use cases</a><a href="/vs/">Compare</a><a href="/pricing/">Pricing</a></nav></header>
<main>
{crumb_html}
{body}
</main>
<footer>
<p class="disclosure">Disclosure: some links on this site are referral links. If you upgrade to Carrd Pro through them, we may earn a commission at no extra cost to you. We're not affiliated with or endorsed by Carrd.</p>
<p><a href="/">Home</a> · <a href="/how-to/">Guides</a> · <a href="/vs/">Compare</a> · <a href="/pricing/">Pricing</a> · <a href="{e(CFG["carrd_hub_url"])}">startwith.carrd.co</a></p>
</footer>
<script src="/track.js" defer></script>
</body>
</html>
"""
    # Make root-relative links (/style.css, /pricing/) relative to this page, so the
    # site works at a domain root, under a sub-path (user.github.io/repo/) and when
    # index.html is opened straight from disk. Absolute https:// URLs are untouched.
    depth = len([p for p in path.split("/") if p])
    prefix = "../" * depth or "./"
    html = re.sub(r'(href|src)="/(?!/)', lambda m: f'{m[1]}="{prefix}', html)
    out = DIST / path.strip("/") / "index.html" if path != "/" else DIST / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    PAGES.append((path, priority))


def with_year(t):
    return f"{t} ({CFG['year']})" if len(t) <= 60 else t


def list_links(items):
    return "<ul>" + "".join(f'<li><a href="{p}">{e(t)}</a></li>' for t, p in items) + "</ul>"


# ---------- page types ----------

def build_howto():
    for h in HOWTO:
        path = f"/how-to/{h['slug']}/"
        steps = "".join(f"<li>{e(s)}</li>" for s in h["steps"])
        gotchas = "".join(f"<li>{e(g)}</li>" for g in h["gotchas"])
        related = [(HOWTO_BY[r]["title"], f"/how-to/{r}/") for r in h.get("related", []) if r in HOWTO_BY]
        body = f"""
<article>
<h1>{e(h['title'])}</h1>
<p class="lede">{e(h['summary'])}</p>
<p class="tier">Plan needed: <strong>{e(h['tier'])}</strong></p>
{cta_box(h['tier'], f"howto-{h['slug']}-top")}
<section><h2>Step by step</h2><ol class="steps">{steps}</ol></section>
<section><h2>Common problems</h2><ul>{gotchas}</ul></section>
{faq_html(h.get('faq'))}
{cta_box(h['tier'], f"howto-{h['slug']}-bottom", "Ready to set it up? Create your site, then follow the steps above.")}
<section><h2>Related guides</h2>{list_links(related)}</section>
</article>"""
        page(path, with_year(h["title"]), h["summary"][:155], body,
             [faq_schema(h.get("faq"))], "0.8",
             [("Home", "/"), ("Guides", "/how-to/"), (h["title"], path)])

    items = [(h["title"], f"/how-to/{h['slug']}/") for h in HOWTO]
    page("/how-to/", "Carrd Guides & Tutorials", "Step-by-step Carrd tutorials: analytics, custom domains, forms, embeds, Spotify, payments and more.",
         f"<h1>Carrd guides & tutorials</h1><p class='lede'>Practical, step-by-step guides for the things people actually get stuck on in Carrd.</p>{list_links(items)}",
         priority="0.7", trail=[("Home", "/"), ("Guides", "/how-to/")])


def build_compare():
    for c in COMPARE:
        path = f"/vs/{c['slug']}/"
        title = f"Carrd vs {c['competitor']}: Which Should You Use?"
        rows = "".join(f"<tr><th>{e(r[0])}</th><td>{e(r[1])}</td><td>{e(r[2])}</td></tr>" for r in c["rows"])
        pc = "".join(f"<li>{e(x)}</li>" for x in c["pick_carrd"])
        po = "".join(f"<li>{e(x)}</li>" for x in c["pick_other"])
        others = [(f"Carrd vs {o['competitor']}", f"/vs/{o['slug']}/") for o in COMPARE if o["slug"] != c["slug"]][:4]
        body = f"""
<article>
<h1>{e(title)}</h1>
<p class="lede">{e(c['one_liner'])}</p>
<div class="table-wrap"><table><thead><tr><th></th><th>Carrd</th><th>{e(c['competitor'])}</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="split">
<section><h2>Choose Carrd if…</h2><ul>{pc}</ul></section>
<section><h2>Choose {e(c['competitor'])} if…</h2><ul>{po}</ul></section>
</div>
<section><h2>Verdict</h2><p>{e(c['verdict'])}</p></section>
{cta_box("", f"vs-{c['slug']}", "Carrd has a free plan, so you can build your page before paying anything.")}
<section><h2>Other comparisons</h2>{list_links(others + [("All Carrd alternatives", "/alternatives/")])}</section>
<p class="fine">Competitor features and pricing change often. Check {e(c['competitor'])}'s current plans before deciding.</p>
</article>"""
        page(path, title, c["one_liner"][:155], body, priority="0.8",
             trail=[("Home", "/"), ("Compare", "/vs/"), (f"vs {c['competitor']}", path)])

    items = [(f"Carrd vs {c['competitor']}", f"/vs/{c['slug']}/") for c in COMPARE]
    page("/vs/", "Carrd Comparisons", "Honest head-to-head comparisons of Carrd with Linktree, Wix, Squarespace, Framer, Webflow and more.",
         f"<h1>Carrd vs everything</h1><p class='lede'>When Carrd is the right tool, and when it isn't.</p>{list_links(items)}",
         priority="0.7", trail=[("Home", "/"), ("Compare", "/vs/")])


def build_usecases():
    for u in USECASES:
        path = f"/for/{u['slug']}/"
        secs = "".join(f"<li>{e(s)}</li>" for s in u["sections"])
        tips = "".join(f"<li>{e(t)}</li>" for t in u["tips"])
        others = [(o["title"], f"/for/{o['slug']}/") for o in USECASES if o["slug"] != u["slug"]][:4]
        body = f"""
<article>
<h1>{e(u['title'])}</h1>
<p class="lede">{e(u['why'])}</p>
<p class="tier">For: {e(u['audience'])} · Recommended plan: <strong>{e(u['plan'])}</strong></p>
<section><h2>What to put on the page</h2><ol>{secs}</ol></section>
<section><h2>Which Carrd plan you need</h2><p>{e(u['plan_reason'])}</p></section>
{cta_box(u['plan'], f"for-{u['slug']}")}
<section><h2>Tips</h2><ul>{tips}</ul></section>
<section><h2>More ways to use Carrd</h2>{list_links(others)}</section>
</article>"""
        page(path, with_year(u["title"]), u["why"][:155], body, priority="0.8",
             trail=[("Home", "/"), ("Use cases", "/for/"), (u["audience"], path)])

    items = [(u["title"], f"/for/{u['slug']}/") for u in USECASES]
    page("/for/", "What Can You Build with Carrd?", "Carrd use cases: portfolios, commissions, link-in-bio, landing pages, resumes, musicians, events and more.",
         f"<h1>What can you build with Carrd?</h1>{list_links(items)}",
         priority="0.7", trail=[("Home", "/"), ("Use cases", "/for/")])


def plans_table():
    cols = ""
    for p in PLANS["plans"]:
        inc = "".join(f"<li>✓ {e(x)}</li>" for x in p["includes"])
        lack = "".join(f"<li class='no'>✗ {e(x)}</li>" for x in p["lacks"])
        rec = " rec" if p.get("recommended") else ""
        cols += f"<div class='plan{rec}'><h3>{e(p['name'])}</h3><p class='price'>{e(p['price'])}</p><p class='fine'>{e(p['for'])}</p><ul>{inc}{lack}</ul></div>"
    return f"<div class='plans'>{cols}</div>"


def build_money_pages():
    # Pricing: "carrd pricing", "carrd pro", "carrd pro plan", "carrd pro lite"
    feature_links = [(h["title"], f"/how-to/{h['slug']}/") for h in HOWTO]
    faq = [
        ["How much is Carrd Pro?", "Carrd Pro is billed yearly in three tiers: Pro Lite, Pro Standard and Pro Plus. See the table above for current prices."],
        ["Which Carrd plan should I get?", "Pro Standard for most people: it's the cheapest plan with a custom domain, forms and embeds (analytics, Spotify, pixels). Pro Lite only removes branding."],
        ["Is Carrd Pro worth it?", "If you need a custom domain or a form, yes. It costs less for a whole year than many site builders charge for one month."],
        ["Is Carrd billed monthly?", "No. Carrd Pro plans are billed yearly."],
    ]
    body = f"""
<article>
<h1>Carrd Pricing {CFG['year']}: Which Pro Plan Do You Need?</h1>
<p class="lede">Carrd is free to start. You only pay when you need a custom domain, forms, embeds or no branding, and paid plans are billed yearly.</p>
{plans_table()}
<p class="fine">Prices shown are Carrd's published USD prices and may change. Always check the final price at checkout.</p>
<section><h2>Quick picker</h2>
<ul>
<li><strong>Just want the badge gone?</strong> Pro Lite.</li>
<li><strong>Need yourname.com, a contact form, Google Analytics or a Spotify player?</strong> Pro Standard.</li>
<li><strong>Need password protection or lots of sites for clients?</strong> Pro Plus.</li>
</ul></section>
{cta_box("Pro Standard", "pricing", "Most people end up on Pro Standard. Start free and upgrade from inside the editor when you need it.")}
<section><h2>What each paid feature unlocks (guides)</h2>{list_links(feature_links)}</section>
{faq_html(faq)}
</article>"""
    page("/pricing/", f"Carrd Pricing {CFG['year']}: Pro Lite vs Standard vs Plus Explained",
         "Carrd pricing explained: what's free, what Pro Lite, Pro Standard and Pro Plus include, and which plan you actually need.",
         body, [faq_schema(faq)], "0.9", [("Home", "/"), ("Pricing", "/pricing/")])

    # "is carrd free"
    free = PLANS["plans"][0]
    faq2 = [
        ["Is Carrd completely free?", "Carrd has a real free plan with no time limit. Custom domains, forms and embeds are paid."],
        ["What's the catch with free Carrd?", "A Carrd branding badge, a .carrd.co address, a small number of sites, and no forms or custom code."],
        ["Do free Carrd sites expire?", "No. Free sites stay up as long as they follow Carrd's terms."],
    ]
    body = f"""
<article>
<h1>Is Carrd Free? What You Get (and Don't) on the Free Plan</h1>
<p class="lede">Yes, Carrd is free with no time limit. Here's exactly where the free plan runs out.</p>
<div class="split"><section><h2>Free includes</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in free['includes'])}</ul></section>
<section><h2>Free doesn't include</h2><ul>{''.join(f'<li>{e(x)}</li>' for x in free['lacks'])}</ul></section></div>
{cta_box("", "is-free", "Build on the free plan first. You only need to upgrade when you hit one of the limits above.")}
{faq_html(faq2)}
<p>See <a href="/pricing/">Carrd pricing</a> for what each Pro tier adds.</p>
</article>"""
    page("/is-carrd-free/", "Is Carrd Free? Free Plan Limits Explained", "Is Carrd free? Yes. Here's what the free plan includes and when you'd need Pro.",
         body, [faq_schema(faq2)], "0.8", [("Home", "/"), ("Is Carrd free?", "/is-carrd-free/")])

    # "carrd referral code". Honest: no invented discount.
    body = f"""
<article>
<h1>Carrd Referral Code / Link</h1>
<p class="lede">Looking for a Carrd referral code? Here's ours. Signing up through it supports this site at no extra cost to you.</p>
<p>{aff_link("Use our Carrd referral link →", "referral-page")}</p>
<section><h2>Is there a Carrd discount code?</h2>
<p>Carrd doesn't generally run public coupon codes, and Pro is already cheap because it's billed yearly. Be wary of sites promising large 'Carrd coupons'. Check the price at checkout before you pay.</p></section>
<section><h2>Save money anyway</h2><ul>
<li>Start on the free plan and upgrade only when you need a paid feature.</li>
<li>Pick the lowest tier that covers what you need. See the <a href="/pricing/">plan picker</a>.</li>
<li>Use one Pro account for several sites instead of paying per site.</li>
</ul></section>
</article>"""
    page("/referral-code/", "Carrd Referral Code & Discount (Honest Answer)",
         "Carrd referral link, and whether Carrd discount codes exist. How to pay the least for Carrd Pro.",
         body, priority="0.8", trail=[("Home", "/"), ("Referral code", "/referral-code/")])

    # "carrd alternative" / "websites like carrd"
    rows = "".join(f"<li><a href='/vs/{c['slug']}/'><strong>{e(c['competitor'])}</strong></a>: {e(c['one_liner'])}</li>" for c in COMPARE)
    body = f"""
<article>
<h1>Carrd Alternatives: {len(COMPARE)} Websites Like Carrd, Compared</h1>
<p class="lede">Carrd is the simplest, cheapest way to build a one-page site. Here's when something else fits better.</p>
<ul class="alts">{rows}</ul>
<section><h2>When Carrd is still the right choice</h2><p>If your site is one page (portfolio, link-in-bio, landing page, commissions, event), the alternatives mostly add cost and complexity you won't use.</p></section>
{cta_box("", "alternatives")}
</article>"""
    page("/alternatives/", f"Carrd Alternatives ({CFG['year']}): Websites Like Carrd Compared",
         "The best Carrd alternatives compared honestly, and when you should just stick with Carrd.",
         body, priority="0.8", trail=[("Home", "/"), ("Alternatives", "/alternatives/")])


def build_tricks():
    # "carrd tricks" (22.2k/mo): one hub that sends traffic to every guide.
    items = "".join(
        f"<li><h3><a href='/how-to/{h['slug']}/'>{e(h['title'])}</a></h3><p>{e(h['summary'])} "
        f"<span class='fine'>Plan: {e(h['tier'])}</span></p></li>"
        for h in HOWTO
    )
    body = f"""
<article>
<h1>{len(HOWTO)} Carrd Tricks Most People Don't Know</h1>
<p class="lede">From real analytics to Spotify players and payment buttons, here's what Carrd can do beyond a basic page. Each trick links to a full step-by-step guide.</p>
<ol class="tricks">{items}</ol>
{cta_box("", "tricks", "Most of these tricks use Pro Standard features. Build free first and upgrade when you need one.")}
</article>"""
    page("/carrd-tricks/", f"Carrd Tricks ({CFG['year']}): {len(HOWTO)} Things You Didn't Know Carrd Could Do",
         "Carrd tricks and hacks: analytics, custom domains, forms, Spotify embeds, custom code, payments, multi-page sites and more.",
         body, priority="0.9", trail=[("Home", "/"), ("Carrd tricks", "/carrd-tricks/")])


def build_home():
    g = list_links([(h["title"], f"/how-to/{h['slug']}/") for h in HOWTO[:6]])
    u = list_links([(x["title"], f"/for/{x['slug']}/") for x in USECASES[:6]])
    c = list_links([(f"Carrd vs {x['competitor']}", f"/vs/{x['slug']}/") for x in COMPARE[:6]])
    body = f"""
<section class="hero">
<h1>Build it with Carrd</h1>
<p class="lede">Independent guides, comparisons and plan advice for Carrd, the simple one-page website builder.</p>
{aff_link("Start a free Carrd site →", "home-hero")}
<p class="fine"><a href="/pricing/">Which plan do I need?</a> · <a href="/is-carrd-free/">Is Carrd free?</a> · <a href="/carrd-tricks/">Carrd tricks</a></p>
</section>
<div class="grid">
<section><h2>Guides</h2>{g}<a href="/how-to/">All guides →</a></section>
<section><h2>Use cases</h2>{u}<a href="/for/">All use cases →</a></section>
<section><h2>Comparisons</h2>{c}<a href="/alternatives/">All alternatives →</a></section>
</div>"""
    page("/", f"{CFG['site_name']}: Carrd Guides, Pricing & Comparisons",
         "Independent Carrd tutorials, pricing breakdowns and comparisons. Learn what you can build and which plan you need.",
         body, priority="1.0")


def build_meta_files():
    urls = "".join(
        f"<url><loc>{e(BASE + p)}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>" for p, pr in PAGES
    )
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n'
    )
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    # llms.txt: a plain summary for AI assistants (ChatGPT/Perplexity already send traffic).
    lines = [f"# {CFG['site_name']}", "", "> Independent guides to Carrd (carrd.co): tutorials, pricing and comparisons.", ""]
    lines += ["## Guides"] + [f"- [{h['title']}]({BASE}/how-to/{h['slug']}/): {h['summary']}" for h in HOWTO]
    lines += ["", "## Comparisons"] + [f"- [Carrd vs {c['competitor']}]({BASE}/vs/{c['slug']}/): {c['one_liner']}" for c in COMPARE]
    lines += ["", "## Use cases"] + [f"- [{u['title']}]({BASE}/for/{u['slug']}/)" for u in USECASES]
    lines += ["", "## Plans", f"- [Carrd pricing]({BASE}/pricing/)", f"- [Is Carrd free?]({BASE}/is-carrd-free/)"]
    (DIST / "llms.txt").write_text("\n".join(lines) + "\n")
    key = CFG.get("indexnow_key", "")
    if key:
        (DIST / f"{key}.txt").write_text(key)
    (DIST / "urls.txt").write_text("\n".join(BASE + p for p, _ in PAGES) + "\n")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    for f in STATIC.iterdir():
        shutil.copy(f, DIST / f.name)
    build_home()
    build_howto()
    build_usecases()
    build_compare()
    build_money_pages()
    build_tricks()
    build_meta_files()

    warnings = []
    if "YOUR_CODE" in AFF:
        warnings.append("affiliate_url still has the YOUR_CODE placeholder (site.config.json)")
    if "XXXX" in CFG.get("ga4_measurement_id", ""):
        warnings.append("ga4_measurement_id not set, so affiliate clicks won't be tracked")
    if not PLANS.get("verified"):
        warnings.append(PLANS["verify_note"])
    if not CFG.get("indexnow_key"):
        warnings.append("indexnow_key empty, so Bing/Yandex instant indexing is off")
    print(f"Built {len(PAGES)} pages → {DIST}")
    for w in warnings:
        print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
