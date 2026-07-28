# Competitor Scorecard & Positioning Instrument — Ocean Enterprise (OEC)

**Prepared:** 28 July 2026 · **v2 (decision-ready)** · **Benchmark subject:** Ocean Enterprise (OE)
**Scope:** 46 distinct competitors today (47 source rows; Fivetran + dbt Labs merged Jun 2026), grouped into **7 macro-categories**, **scored** on a 6-criterion weighted model and **segmented** by strategic relevance.

| File | What's in it |
|---|---|
| **`competitor_scorecard.xlsx`** | The instrument. Tabs: **Scorecard** (scored + segmented + evidence), **OE Benchmark & Gaps**, **Tactic Backlog** (ranked), **Scoring Model** (rubric + weights), **Categories** (macro→sub), **Corrections & Method** |
| **`README.md`** (this file) | Executive summary, scoring model, OE gap analysis, synthesis, the OEC conclusion, and the corrections log |
| **`per_company_teardowns.md`** | Full qualitative teardown of every competitor (positioning, CTAs, keywords, clients, blog, LinkedIn, tactic) |
| `competitor_scorecard.csv` | Flat export of the Scorecard tab |

---

## 0 · What changed in v2 (from inventory → decision instrument)

This version responds to a review that (correctly) found v1 was a strong research inventory but not yet decision-ready. Added:

- **Weighted 6-criterion scoring model** (Relevance, Positioning, Traction, Trust, Community, Tactic-transferability) → a **Composite** and a **Strategic-priority** score per competitor. See the *Scoring Model* tab.
- **Segment weights** (Direct 1.0 / Technical 0.7 / Messaging 0.5 / Ecosystem 0.3) so **hyperscaler visibility no longer overwhelms strategic relevance** to OEC.
- **Ocean Enterprise scored on the same criteria**, with a **gap analysis** vs. the direct-competitor average (*OE Benchmark & Gaps* tab).
- **Metric-level separation** — own (company/product) followers & headcount vs. **parent/owner** followers for context — so a hyperscaler's sub-product isn't compared to a 20-person startup on the same line.
- **Evidence columns** — primary source (homepage, the canonical audit target), access date, and a **Confidence** rating per row.
- **Ranked Tactic Backlog** — each borrowable tactic carries **Expected impact / Effort / Fit-for-OEC / Supporting evidence** and a computed priority.
- **7 macro-categories** replacing the 19 granular labels.

### Factual corrections in this version (three were already stale on the compile date)

1. **Fivetran + dbt Labs — MERGED.** All-stock, announced 13 Oct 2025, **completed 1 Jun 2026**; combined entity positioned as *"Data Infrastructure for Trusted AI Agents"* (Fraser CEO, Handy President). Now **one** competitor row. *(v1 error: listed as two standalones — and misread their CEO-to-CEO merger content as a competitive exchange.)*
2. **Salesforce + Informatica — COMPLETED 18 Nov 2025** (~$8B, $25/share). Informatica is **no longer an independent public company**; row flags Salesforce as owner.
3. **IBM + Confluent — COMPLETED 17 Mar 2026** (~$11B, announced Dec 2025). Row now says "completed," consistent with the notes.
4. **Ocean Protocol ↔ ASI Alliance** — withdrawal 9 Oct 2025 (with litigation) **confirmed correct**.
5. **Count corrected** — 47 competitor rows in the source (the 48th is the title banner); after the Fivetran+dbt merger, **46 distinct competitors today**.

### Honesty box (unchanged, still important)
- **Site fetches were blocked** (HTTP 403 egress policy on every domain), so on-page CTA text and blog indexes come from indexed search snippets/press/trackers, not live pages. The *Primary source* column is the audit target.
- **LinkedIn numbers are approximate & point-in-time** (±~10–15% between trackers). Trust the **bands**, not the digits. `n/v` = not verifiable this pass.
- **Scores are structured analyst judgement on a published rubric**, not measured data. The weights are exposed in the workbook — change them and the ranking recomputes.

---

## 1 · Executive summary — the 8 things that matter

1. **OE's gap is marketing discipline, not headcount.** The competitors that punch above their weight (Phala, Sovity, Lifebit, Apheris, Streamr) are teams OE's size or smaller. The gap is content + proof discipline — copyable this quarter.

2. **The whole field repositioned around "trusted data for AI agents" in the last 12 months** — and it's now consolidating hard around that phrase: **IBM** (Confluent + StreamSets + DataStage), **Salesforce** (Informatica), **Qlik** (Talend), **LiveRamp** (Habu), and the **Fivetran + dbt** merger all pitch the same "data infrastructure for trusted AI." OE's **Compute-to-Data** is *natively* that story and should lead with it.

3. **That consolidation is OE's opening.** As the independents get absorbed into suites and walled gardens, an **open, collectively-governed, vendor-neutral** network is the differentiated alternative — the way Databricks weaponizes "open, no lock-in."

4. **OE's measured edge is TRUST; its gap is POSITIONING + COMMUNITY.** Scored against the direct-competitor average (§4): OE **leads on Trust (+0.8)** and is slightly ahead on Traction (+0.4), but **trails on Positioning (−1.7)** and **Community (−0.9)**. The recommendations target exactly those two gaps.

5. **Proof has moved from logo walls to quantified outcomes and named consortia** (Phala's "300% sales / 60% faster"; Apheris's co-branded AISB/ADMET networks). OE has arguably the **best raw proof in the set** — Mercedes/Acentrik, EuProGigant, Staatsbibliothek Berlin — presented as a governance roster, not as marketed outcomes.

6. **The direct set wins on standards authority, not spend** — Dawex turned its framework into a **CEN/CENELEC standard**; Fraunhofer/Advaneo are cited as **"use case #1"** inside IDSA/Gaia-X; OVHcloud badges **"Gaia-X label level 3."** OE's Gaia-X/IDS lineage should be *quantified and badged* the same way.

7. **Naming is a moat** — "context layer" (Atlan), "Secret Computing®" (Inpher), "CLAIRE" (Informatica), "Data Shops" (Narrative). **Compute-to-Data** is an unbranded, ownable asset — brand it and repeat it relentlessly.

8. **Signature content formats are cheap and recurring** — the annual "State of X" report, the public quarterly transparency/roadmap post, the "success stories" page with numbers, release-synced blogging. OE runs none systematically today.

---

## 2 · Ocean Enterprise — baseline

| Dimension | OE today |
|---|---|
| **Positioning** | Free, open-source, collectively-governed **data & AI ecosystem software** to **securely manage & monetize** proprietary AI/data products. Domain-agnostic. |
| **Core / named asset** | **Compute-to-Data (C2D)** — compute runs where the data lives; only results leave. Roots in Ocean Protocol (web3). |
| **Governance** | **Ocean Enterprise Collective (OEC)** — independent non-profit; consortium model (à la Gaia-X/IDS), not a classic SaaS vendor. |
| **Proof (members)** | FELT Labs, Transport Genie, **Acentrik / Mercedes-Benz**, sunDAO, Brainstem, Rocketstar, **EuProGigant**, **Staatsbibliothek Berlin**, deltaDAO, Ocean Protocol Foundation, **Triumvirate Labs / TVL Tech**. |
| **Channels** | `oceanenterprise.io`, `docs.oceanenterprise.io`, **Medium** blog, **X** @ocnenterprise, **LinkedIn** "Ocean Enterprise Collective". |
| **Funnel** | "Learn / read docs / contact" only. No prominent self-serve or live-demo path. |
| **LinkedIn** | Small / early-stage; count not publicly indexed. Member-spotlight posts ~monthly. No paid campaigns evident. |

---

## 3 · Scoring model, segmentation & the ranked field

**Criteria & weights** (1–5 each; full rubric in the workbook): Relevance **25%**, Positioning **20%**, Traction **15%**, Trust **15%**, Community **10%**, Tactic-transferability **15%** → **Composite (1–5)**.
**Strategic priority (0–100)** = Composite ÷ 5 × 100 × **segment weight**.

**Segments** (so hyperscaler reach doesn't distort strategic relevance):

| Segment | Weight | Members (examples) |
|---|---|---|
| **Direct competitor** — same job-to-be-done | 1.0 | Dawex, Sovity, Advaneo, Fraunhofer, iExec, Phala, Oasis, Secret, Streamr, Narrative.io, Fetch.ai |
| **Technical alternative** — similar outcome, different tech | 0.7 | Lifebit, Apheris, Duality, Sarus, Devron, Tune Insight, Oblivious, Inpher, NVIDIA FLARE |
| **Messaging reference** — learn positioning from | 0.5 | Atlan, IONOS, OVHcloud, OpenMined, Flower, Alation, Collibra, Precisely, Pega, FICO, Striim, Talend, Habu, Fivetran+dbt, Informatica |
| **Ecosystem platform** — hyperscaler/suite sub-product | 0.3 | AWS Data Exchange, Snowflake Marketplace/Clean Rooms, Databricks Marketplace, Azure Data Factory, IBM DataStage/ODM, SAP Data Services, Confluent, StreamSets |

**Top 10 competitors by strategic priority** (the ones to watch and learn from first — note they're all Direct):

| # | Company | Segment | Composite | Priority |
|---|---|---|---:|---:|
| 1 | Phala Network | Direct | 4.2 | 84 |
| 2 | Dawex | Direct | 4.1 | 83 |
| 3 | Fraunhofer ISST (IDS) | Direct | 4.1 | 83 |
| 4 | Sovity | Direct | 4.0 | 80 |
| 5 | iExec | Direct | 3.9 | 77 |
| 6 | Oasis Protocol | Direct | 3.6 | 72 |
| 7 | Narrative.io | Direct | 3.6 | 72 |
| 8 | Advaneo | Direct | 3.6 | 71 |
| 9 | Streamr | Direct | 3.4 | 68 |
| 10 | Fetch.ai (ASI) | Direct | 3.3 | 67 |

> Hyperscaler sub-products (AWS/Snowflake/Databricks/Azure) score high on Composite but fall down the priority list once segment-weighted — which is the point. Full scores for all 46 are in the *Scorecard* tab.

---

## 4 · OE benchmark & gap analysis

OE scored on the four criteria comparable across the benchmark (Relevance and Tactic-transfer are self-referential for the subject), against the **direct-competitor average**:

| Criterion | Ocean Enterprise | Direct-competitor avg | Gap | Reading |
|---|:--:|:--:|:--:|---|
| **Positioning** | 2 | 3.7 | **−1.7** | Strong substance, weak/unnamed surfaced message. Biggest, cheapest gap. |
| **Traction** | 3 | 2.6 | **+0.4** | Real blue-chip members but early; roughly at par with small direct peers. |
| **Trust** | 4 | 3.2 | **+0.8** | Gaia-X/IDS lineage + collective governance + national-institution members = genuine strength. |
| **Community** | 2 | 2.9 | **−0.9** | Small social footprint; OSS + collective under-activated. |

**Headline:** OE's edge is **Trust**; its gaps are **Positioning** and **Community**. Close the *message + proof + community* gap and OE leads its direct segment on trust-weighted relevance — because Trust is the one axis its consolidating, walled-garden rivals can't easily claim.

---

## 5 · LinkedIn & scale benchmark (realistic target band)

Approximate; own-entity pages only (hyperscaler sub-products excluded — they roll up to a parent). **Set OE's near-term target from the peer band, not the giants.**

| Peer band | Companies | Followers |
|---|---|---|
| **OE near-term target (~4–8k)** | iExec, Dawex, Apheris, Narrative, Streamr, Oasis | ~3.6k–8.4k |
| **Ceiling on a small team (~20k)** | Lifebit (~22k on ~124 people) | shows what disciplined SEO+cadence reaches |
| **Early-stage (<2k)** | Advaneo, Secret Network, Sarus, Sovity | ~1.2k–1.9k |
| **Aspirational (category authority)** | OVHcloud ~294k, dbt+Fivetran ~300k(combined), FICO ~546k | not near-term |

> Follower count tracks **content cadence** far more than headcount. Lifebit (~22k / ~124 staff) is the proof.

---

## 6 · Cross-cutting synthesis (what the field does)

- **CTAs — two-track is the norm:** enterprise *"Book a demo / Contact sales"* **plus** self-serve *"Start free / free credits / Star on GitHub / docs quickstart."* OE runs neither prominently. Databricks even tiers CTAs by trust level ("Get instant access" vs "Request access") — a pattern that maps onto C2D's data-sensitivity tiers.
- **Messaging clusters:** AI-readiness/agents · privacy/crypto (FHE, TEE, DP, C2D) · sovereignty (Gaia-X, IDS, "by architecture not policy") · monetization (data products, Data Shops). **OE is one of the few that can credibly stand in all four at once** — but must pick a lead ("trustworthy, governed data for AI, without moving it").
- **Proof:** quantified outcome stories + named multi-brand consortia > grey logo walls. Per-customer branded case-study pages (Streamr, Dawex, OVHcloud) win.
- **Content formats (all cheap, recurring):** annual "State of X" report · public quarterly transparency/roadmap · "success stories with numbers" · release-synced blog · SEO "2026 guide" hub · flagship event + recorded talks · free courses · policy/analyst editorial sub-brand.

---

## 7 · The strongest available position for OEC

> **An open, collectively-governed data & AI network where data stays under the provider's control and approved computation travels to the data.**

The website should make **five elements immediately visible**:

1. **One ownable category phrase** — brand **Compute-to-Data** as the name (à la "context layer" / "Secret Computing").
2. **Separate journeys** for **builders**, **data providers**, and **enterprise buyers** (distinct CTAs + landing pages).
3. **A live Compute-to-Data demonstration** on the homepage (the top self-serve conversion lever).
4. **Quantified deployments & consortium members** — Mercedes/Acentrik, EuProGigant, Staatsbibliothek Berlin, with a metric each.
5. **Public roadmap, governance report & transparency report** — turning governance-first into a recurring trust asset.

This position leans directly into OE's measured strength (Trust) and closes its measured gap (Positioning), while the consolidation of every rival into a suite makes "open + neutral + collectively governed" more differentiated by the quarter.

---

## 8 · Ranked tactic backlog (top of the list)

Full ranked list with Expected-impact / Effort / Fit / Evidence is in the **Tactic Backlog** tab. The highest-priority, lowest-effort moves:

| Priority | Tactic | Borrowed from |
|---:|---|---|
| ⭐⭐⭐ | Brand **Compute-to-Data** as a named, ownable category phrase | Atlan, Inpher, Informatica |
| ⭐⭐⭐ | **Two-track CTA** — enterprise demo **+** self-serve/OSS entry | dbt+Fivetran, Phala, iExec, Flower |
| ⭐⭐⭐ | **"Success stories" page with quantified member outcomes** | Phala, Fivetran |
| ⭐⭐⭐ | **Live Compute-to-Data demo** on the homepage | iExec, Phala |
| ⭐⭐⭐ | **Lean into neutrality** as consolidation accelerates | Databricks (vs IBM/Salesforce/Qlik roll-ups) |
| ⭐⭐ | **Name member cohorts as co-branded "data networks"** | Apheris (AISB/ADMET) |
| ⭐⭐ | **Public quarterly transparency + governance + roadmap** report | Streamr, iExec |
| ⭐⭐ | **Quantify + badge Gaia-X / IDS** credentials | OVHcloud |

---

## 9 · Competitive watch-list (status changes to track)

- **Ocean Protocol left the Fetch.ai/ASI Alliance (Oct 2025, with litigation)** — a former partner now operating adjacent territory. Highest relevance.
- **Consolidation wave:** **IBM** now owns Confluent (~$11B, Mar 2026), StreamSets, DataStage, ODM; **Salesforce** owns Informatica (Nov 2025); **Fivetran + dbt Labs** merged (Jun 2026); **Qlik** owns Talend; **LiveRamp** owns Habu; **Arcium** took Inpher's core tech/team. Independents are becoming suite features.
- **TripleBlind → uncertain** (possible divestiture/downsizing) — **verify before citing** client-facing.
- **Streamr** flagged resourcing pressure. **Phala, Oasis, Secret Network** all mid-pivot to "confidential AI" — the same wedge OE should claim first.

---

*Sources: each competitor's public web presence and press coverage, third-party trackers (Crunchbase, PitchBook, LeadIQ, Tracxn), LinkedIn public snippets, and the GitHub API for OSS stars, gathered 2026-07-28. Direct fetches were blocked by egress policy; figures approximate and flagged where unverifiable. Scores are analyst judgement on the rubric in the workbook. See `per_company_teardowns.md` for detail and `competitor_scorecard.xlsx` for the scored, filterable instrument.*
