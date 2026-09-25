# Carrd affiliate pSEO strategy

Goal: send as many **paying** visitors as possible to carrd.co through the referral link.
Carrd pays only when someone upgrades to Pro, so the aim is buyer traffic, not just traffic.

---

## 1. What the GA data says (Jan 1 – Sep 25, 2026)

| Signal | Number | What it means |
|---|---|---|
| Active users | 1,911 | Small base, but growing |
| Weekly new users, wk 17–32 | 47–85 | Old baseline |
| Weekly new users, wk 33 onward | 107–222 | **About 2x step-up since mid-August.** Something started ranking. Find out which page/query in Bing Webmaster Tools and build more of it |
| Singapore | 562 users (29%) | **Mostly bots.** Together with Ashburn, Boardman, The Dalles, Prineville and similar (all cloud datacenters), roughly 30–35% of "users" are probably crawlers. Real humans ≈ 1,250 |
| Direct | 839 | Inflated by the same bots |
| Qualified / converted leads | 0 / 0 | **No conversion tracking.** You can't tell which pages earn money. Fix first (see §4) |
| Returning users | ~1–5% | Normal for a pass-through affiliate site. Don't optimise for retention |

### The biggest insight: this is a Bing site, not a Google site

| Source | Sessions |
|---|---|
| Bing + cn.bing | 628 |
| Yahoo (all country subdomains) | 104 |
| Ecosia | 82 |
| ChatGPT (search runs on Bing's index) | 82 |
| DuckDuckGo | 54 |
| **Bing-powered total** | **≈ 950** |
| Google + Gemini | 263 |

Bing-powered engines send **~3.6x more** than Google. So:

- **IndexNow** (built in: `generator/indexnow.py`) gets new pages into Bing within hours, not weeks.
- Verify the site in **Bing Webmaster Tools** and submit the sitemap. Its keyword report shows which queries drive the mid-August jump.
- Bing rewards **exact-match titles and H1s** more than Google does. That's why every page title contains the target keyword verbatim ("How to Add Google Analytics (GA4) to Carrd", "Carrd vs Linktree").
- AI assistants (ChatGPT 82, Claude/Gemini/Perplexity ~9) are your fourth channel. `llms.txt`, clear FAQ blocks and direct one-sentence answers help them cite you.

---

## 2. Keyword research, sorted by value to an affiliate

The raw list contains a lot of noise. Here's how it breaks down:

| Bucket | Keywords (monthly vol) | Buyer intent | Action |
|---|---|---|---|
| **Money: plans & features** | website builder 1,900 · pricing 390 · alternative 320 · landing page 320 · pro 260 · pro plan 260 · referral code 260 · is carrd free 260 · portfolio 260 · websites like carrd 210 · vs linktree 140 · reviews 140 · one page website 140 · pro lite 110 · google analytics for carrd 90 | **High** | ✅ Built (pricing, is-free, referral, alternatives, vs/*, for/*, how-to/*) |
| **Tricks / tutorials** | tricks 22,200 · tutorial 480 · how to use 90 · spotify 140 · edit 70 · redirect 10 | Medium: many tricks need Pro | ✅ Built (`/carrd-tricks/` + 11 how-to pages) |
| **Templates** | templates 5,400 · templates free 1,000 · inspo 590 · examples 260+170 · aesthetic/cute/tumblr ~550 · layouts 140 | Medium: everyone who uses a template has to sign up | ⏭ Phase 2: needs real templates you build (see §5) |
| **Resources (decor)** | pngs, dividers, gifs, blinkies, stamps, symbols, fonts, colors, backgrounds (~2,000 combined) | Low: mostly teens on the free plan | Link-bait only. Low priority |
| **Fandom niches** | fictionkin, ffxiv, enstars, kin, osdd, radqueer, mdzs… (10–170 each) | Very low | One hub page (`/for/fandom-bio/`) is enough |
| **Navigational** | login 6,600 · dashboard 210 · sign in 90 · is carrd down 90 | None: people want carrd.co itself | Skip |
| **Junk** | "carrd game" 201,000 (almost certainly a misspelling of "card game") · access stout · pro say · pro fogger · *tutorial for unrelated tools | None | Ignore; don't let the big number mislead you |

**Takeaway:** the *money* bucket is only ~5,000 searches/month, but those searchers are deciding whether to pay. One visitor from "carrd pricing" is worth more than 50 from "carrd pngs".

---

## 3. The pSEO architecture (what's in this repo)

Carrd sites are one page, and `#section` URLs all count as one page for search engines, so **you can't do pSEO on startwith.carrd.co itself**. This repo generates a separate static site (41 pages today) for a custom domain, and your Carrd site becomes the brand front door that links to it.

| Template | URL | Count | Target pattern |
|---|---|---|---|
| Feature how-to | `/how-to/{feature}/` | 11 | "carrd {feature}", "how to add {x} to carrd". Each one says which plan the feature needs, so the reader already knows why they'd upgrade |
| Use case | `/for/{audience}/` | 12 | "carrd {portfolio / commissions / landing page…}" |
| Comparison | `/vs/{competitor}/` | 9 | "carrd vs {x}", "{x} or carrd" |
| Money hubs | `/pricing/`, `/is-carrd-free/`, `/referral-code/`, `/alternatives/`, `/carrd-tricks/` | 5 | the highest-intent queries |
| Index hubs | `/`, `/how-to/`, `/for/`, `/vs/` | 4 | internal linking |

Each page includes:
- a CTA box that states the required plan ("This needs Carrd Pro Standard"), top and bottom
- a referral link with `rel="sponsored"` and a GA4 `affiliate_click` event tagged with its placement
- FAQPage + BreadcrumbList + Article JSON-LD, canonical tag, OG tags
- related-page links (every page is at most 2 clicks from home)
- an FTC-style affiliate disclosure in the footer

**Adding pages means adding rows to `data/*.json`, not writing code.** For example, 10 more `vs` entries is 10 more pages.

---

## 4. Do these first (week 1)

1. **Put your real referral link** in `site.config.json → affiliate_url`, and read Carrd's referral terms (some programs ban brand-keyword ads or "coupon" claims. The referral page is written to stay honest).
2. **Set up GA4 conversions**: add your measurement ID, then in GA4 → Admin → Events mark `affiliate_click` as a **Key event**. Your "0 conversions" becomes a per-page, per-placement revenue map.
3. **Verify prices** in `data/plans.json` against carrd.co/pro, then set `"verified": true`. The build warns until you do.
4. **Buy a domain** (for example startwithcarrd.com), deploy (see README), point DNS, set `indexnow_key`.
5. **Bing Webmaster Tools + Google Search Console**: verify both and submit `/sitemap.xml`.
6. **Update startwith.carrd.co**: put the referral link in its main button, and link to `/pricing/`, `/carrd-tricks/` and `/alternatives/`. Keep whatever content caused the August jump.
7. **Filter the bots** in GA4 (Admin → Data filters, or exclude Singapore + datacenter cities in reports) so you can trust your numbers.

---

## 5. Roadmap

**Phase 1 (now → 4 weeks): money pages.** Ship the 41 pages. Watch Bing WMT for impressions. Add more `vs` pages (Carrd vs Linktree already has 140/mo. Try Wix Studio, Hostinger, Bio.link, Milkshake, Super.so, Typedream, Durable, Hostinger AI builder) and more `for/` audiences (tattoo artist, coach, therapist, real estate agent, podcast, restaurant, Discord server, streamer/VTuber).

**Phase 2 (month 2–3): template gallery.** This is the biggest buyer-adjacent opportunity (~8k/mo across templates/inspo/examples/aesthetic). Build 15–30 real Carrd templates (portfolio, commissions, link-in-bio, waitlist, aesthetic variants), screenshot each, and generate `/templates/{style}/` pages from a `templates.json`. The CTA on each is "create a free Carrd account to use this", which naturally leads to sign-ups through your link. **Don't publish template pages without real templates.** Empty, auto-generated pages get a site demoted.

**Phase 3 (month 3+): scale what converts.** Once `affiliate_click` data comes in, double down on the page types with the best click rate. Refresh `dateModified` + the year in titles each January. Add an "Update log" to pricing when Carrd changes plans (both Bing and Google reward freshness).

### Guardrails
- Every page must answer the query better than the current top result. More rows in the JSON only help if each row is genuinely useful. Thin pages hurt the entire domain.
- Keep competitor claims qualitative (no prices) unless you check and date them.
- Don't claim discounts that don't exist.
