# AI Citation PR Planner

**Free, open-source planner that tells you where to publish so ChatGPT, Claude
and Gemini start citing your product.**

AI assistants answer buyer questions from a small set of web pages. This tool
asks the assistants your buyers' questions, records every page they cite, keeps
the sites you can actually buy a placement on (through
[Collaborator.pro](https://collaborator.pro)), has every assistant rate each
site's trustworthiness, and gives you two sheets:

| Sheet | Question it answers |
|---|---|
| **1 · PR articles** | Where should I publish a **new** article about my product? Every site is sold on Collaborator.pro and scored 0–100 by each engine for *"is this site trustworthy and editorially independent?"* |
| **2 · Link insertions** | Which articles do the assistants **already cite**, on sites I can buy, so I should get my link added there? |

Every row carries **citation proof**: which engine cited it, for which prompt,
and the exact page. Sites nobody cited say so.

All models are reached through **[FlyMyAI](https://flymy.ai)**: one account,
one balance, no OpenAI / Anthropic / Google keys. The report is a dashboard
page hosted on FlyMyAI as a private artifact.

Sister project of the
[AI Visibility Checker](https://github.com/anatolyterentyev/AI-Visibility-Checker),
which measures *whether* AI assistants mention you. This one tells you *where
to publish* so they start to.

---

## Quick start

Open [`PROMPT.md`](PROMPT.md), copy the prompt, fill in the product brief
(name, website, description, competitors, audiences), and paste it into an
**AI assistant connected to the FlyMyAI MCP** (Claude Code, Claude, Cursor,
Codex, ChatGPT …: https://docs.flymy.ai/agents/guides/ai-assistants).

You need:

- a **FlyMyAI** account with balance. The default plan is 24 prompts × 3
  engines plus trust scoring: about **$4–8**, 20–30 minutes, capped at $15 by
  the prompt.
- a **Collaborator.pro** account. The assistant connects it once in FlyMyAI
  with your Collaborator.pro API token.

---

## How it works

```
 your assistant (FlyMyAI MCP) = the lead
   │
   ├─ 1. Plan ────────────▶ prompt mind map: 6 branches × 4 prompts,
   │                        2–10 words, never containing your brand
   │
   ├─ 2. Probe, in parallel, every prompt × every engine
   │        ChatGPT probe (GPT-6 Sol + OpenAI web search)
   │        Claude probe  (Claude Sonnet 5.5 + Claude web search)
   │        Gemini probe  (Gemini 3.8 Flash + Google Search,
   │                       redirect links resolved to real pages)
   │      → every URL each engine cited
   │
   ├─ 3. compute.py cited ─▶ cited domains, minus app stores, social
   │                         networks, your site and competitors' sites
   │
   ├─ 4. Collaborator.pro ─▶ which cited domains are for sale: price, DR,
   │                         organic traffic, link type
   │      (+ optional catalog search for more relevant sites)
   │
   ├─ 5. Trust, every engine scores every site 0–100 with a reason
   │
   ├─ 6. compute.py compute ▶ priorities, flags, proof → plan.json + data.js
   │
   └─ 7. FlyMyAI artifact: artifact/index.html + data.js
```

### Scoring

- **Trust avg** = mean of the engines' 0–100 scores. A missing score stays
  missing: no engine's answer ever stands in for another's.
- **Priority** = 0.6 × trust avg + 15 × engines citing the site + 2 ×
  citations (max 5), capped at 100. Catalog sites (not cited yet) score
  0.6 × trust avg.
- **Flags** (red notes): inflated traffic (organic under 1,000 a month or under
  1% of listed traffic), sponsored or nofollow links, and warnings taken from
  the engines' trust reasons (vendor's own site, sells paid posts …).

## Repository

| Path | What it is |
|---|---|
| [`PROMPT.md`](PROMPT.md) | The public prompt: paste into any assistant connected to FlyMyAI |
| [`agents/lead.md`](agents/lead.md) | The lead's method: brief → mind map → probes → Collaborator.pro → trust → report |
| [`agents/probe.md`](agents/probe.md) | Instructions of the per-engine probe agent (`probe` and `trust` modes) |
| [`agents/finder.md`](agents/finder.md) | Optional: find more relevant sites in the Collaborator.pro catalog |
| [`scripts/compute.py`](scripts/compute.py) | `cited` lists the domains to check; `compute` builds `plan.json` + `data.js` (standard library only) |
| [`artifact/index.html`](artifact/index.html) | The dashboard page; reads `window.PLAN` from `data.js` |
| [`tests/`](tests/) | `python3 -m unittest discover tests` |

Preview a plan locally: run `compute.py compute` on `tests/fixtures/run.json`,
copy the resulting `data.js` next to `artifact/index.html` and open the HTML
file in a browser.

### `run.json`

The lead assembles one file from the agents' answers and runs
`compute.py` on it ([`tests/fixtures/run.json`](tests/fixtures/run.json) is a
complete small example):

```json
{
  "product": {"name": "", "website": "", "exclude_domains": ["competitor.com"]},
  "mind_map": {"<branch>": ["prompt"]},
  "probes": [{"engine": "claude", "label": "Claude", "run": "<run id>", "round": "Run 1",
              "date": "2026-11-17", "results": [{"prompt": "", "cited_urls": [], "product_mentioned": false}]}],
  "collaborator": {"<domain>": {"price": "250.00 USD", "dr": 48, "listed_traffic": "45.5K",
                   "organic_traffic": 21670, "link_type": "dofollow", "url": "", "added": null}},
  "catalog": ["<domain found in the catalog, not cited>"],
  "trust": [{"engine": "claude", "label": "Claude", "scores": [{"domain": "", "score": 60, "reason": ""}]}],
  "notes": {"<domain>": "warning"},
  "pitches": {"<article url>": {"anchor": "", "pitch": ""}}
}
```

## Customising

- **Models:** the probes use each vendor's flagship on FlyMyAI. The prompt tells
  the assistant to check `list_agent_models` and move to newer models.
- **More engines:** add another probe agent (e.g. Grok) and list it in the
  prompt's `engines`.
- **More prompts:** `prompt_count` from 12 to 60. Cost grows with prompts, and
  the Gemini probe costs the most.
- **Track progress:** re-run the same prompts every week or two. New citations
  of your own articles show up in the proof column.

## Limitations

This is an honest approximation, not a panel of real users. API models with
web search answer differently from the consumer apps, and each prompt is asked
once per engine, so citations change from run to run. Trust scores are each
model's opinion and can be stale: a model may still praise a domain that
has changed owners. Check a site yourself
before you pay for a placement.

## Privacy of results

Plans contain which sites sell placements and at what price. Keep them in
your private FlyMyAI artifact; this repository deliberately ships no real
plans or site lists, and the test fixture uses made-up domains.

## License

MIT, free for anyone. Model access via [FlyMyAI](https://flymy.ai); site
listings via [Collaborator.pro](https://collaborator.pro).
