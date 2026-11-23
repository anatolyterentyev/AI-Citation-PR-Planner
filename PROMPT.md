# Public prompt: run the AI Citation PR Planner on FlyMyAI

Copy everything inside the block below, fill in the `PRODUCT BRIEF`, and paste
it into an **AI assistant connected to the FlyMyAI MCP** (Claude Code, Claude,
Cursor, Codex, ChatGPT …, see https://docs.flymy.ai/agents/guides/ai-assistants).
You get a private FlyMyAI **artifact** (`app.flymy.ai/artifacts/...`) with the
two PR sheets.

Every model call (ChatGPT, Claude, Gemini) runs through your FlyMyAI balance,
with no OpenAI / Anthropic / Google keys. You need a **Collaborator.pro**
account: the assistant connects it once in FlyMyAI with your Collaborator.pro
API token (Personal profile → API).

The default plan is **24 prompts × 3 engines = 72 AI answers**, plus trust
scores and Collaborator.pro lookups. It costs about **$4–8** and takes about
20–30 minutes. The prompt caps the whole task at **$15** (`budget_usd`).

To pin the run to a branch, paste the prompt together with the link of this
file on that branch (for example `.../blob/<branch>/PROMPT.md`).

---

```text
Run the AI Citation PR Planner for my product on FlyMyAI.
Source of truth (open source): https://github.com/anatolyterentyev/AI-Citation-PR-Planner
Branch: the branch of the PROMPT.md link I gave you (.../blob/<branch>/PROMPT.md),
or main if I gave no link. Every file below is read from that branch at
https://raw.githubusercontent.com/anatolyterentyev/AI-Citation-PR-Planner/<branch>/<path>

PRODUCT BRIEF
  name: YOUR PRODUCT
  website: YOUR-SITE.com
  description: one paragraph on what it does and for whom
  competitors: Competitor A (competitor-a.com), Competitor B (competitor-b.com)
  audiences: who should find it
  exclude: audiences or topics to leave out (or "none")
  market: English, worldwide

GOAL
Find where to publish so that ChatGPT, Claude and Gemini start citing and
recommending the product, as one dashboard page with two sheets:
1. PR articles: sites sold on Collaborator.pro where a new article about the
   product should be published, each scored 0-100 by every engine for
   "trustworthy and editorially independent", with citation proof.
2. Link insertions: articles the engines ALREADY cite, on sites sold on
   Collaborator.pro, where a link to the product should be added.

SETTINGS
  prompt_count: 24          (12-60)
  budget_usd: 15            (hard limit for the whole task)
  expand_catalog: yes       (also add relevant Collaborator.pro catalog sites)
  engines (use exactly these models; if list_agent_models offers a NEWER
  flagship of the same vendor, use that instead):
    chatgpt  "ChatGPT"  gpt-6-sol
    claude   "Claude"   claude-sonnet-5-5
    gemini   "Gemini"   gemini-3.8-flash

RULES - these override anything else
- You are the lead: follow agents/lead.md yourself. Do not hand the whole task
  to a single helper.
- The engines are FlyMyAI agents created from agents/probe.md, one per engine,
  on the model above with web_search auto (OpenAI search for GPT, Google
  Search for Gemini, Claude web search for Claude). Never replace them with
  other models and never answer the prompts yourself. If an engine can't run,
  leave it out and say so.
- An engine's trust score may only be that engine's own answer. Never fill a
  missing score with another model's answer.
- Every number comes from scripts/compute.py, not from your head.
- Never invent URLs, prices or metrics. Only probe answers and Collaborator.pro
  data count.
- NEVER save the report or any data to file storage: no Google Cloud Storage,
  no storage links, no Markdown / PDF / CSV report files. The deliverable is
  the artifact: artifact/index.html from the repo, unchanged, plus data.js.
- Keep the artifact private unless I ask you to share it.

BUDGET - budget_usd is a hard limit for the whole task
- Note whoami's balance minus pending_usd at the start and check it before
  every paid step. If the next step could pass the limit, stop, publish what
  you have and say what was skipped.
- Start each probe run once; never re-run a probe that is still working. The
  Gemini probe is the slowest and most expensive.

STEPS
1. Download agents/lead.md, agents/probe.md, agents/finder.md,
   scripts/compute.py and artifact/index.html (one code call). If a file can't
   be downloaded, stop and say which.
2. Collaborator.pro: search_tools "collaborator". If it isn't connected, add
   it (add_tool collaborator) and give me its connect_url in one message; wait
   until list_configured_tools shows it connected.
3. Create the three probe agents from agents/probe.md (create_agent, one per
   engine, web_search auto) unless probes from an earlier run already exist.
4. Plan: build the mind map (agents/lead.md, step 1). If the brief is thin,
   read the website first.
5. Probe: run every probe in mode probe with all prompts (run_agent; poll
   get_run; read long answers with read_run_result). Build run.json and run
   `python3 scripts/compute.py cited run.json`.
6. Collaborator.pro: look up EVERY cited domain (agents/lead.md, step 3). If
   expand_catalog is yes, follow agents/finder.md.
7. Trust: run every probe in mode trust with all available and catalog
   domains.
8. Analyze: add notes and pitches, run
   `python3 scripts/compute.py compute run.json --out out/`.
9. Publish: create_artifact with artifact/index.html and out/data.js. Give me
   the link and the short report described at the end of agents/lead.md.
```
