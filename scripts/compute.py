#!/usr/bin/env python3
"""AI Citation PR Planner: turn raw probe answers into the two PR sheets.

Standard library only. Two commands:

  python3 scripts/compute.py cited   run.json
      Lists every domain the engines cited (after dropping app stores, social
      networks, the product's own site and competitors' sites). This is the
      list to check on Collaborator.pro.

  python3 scripts/compute.py compute run.json --out OUT_DIR
      Writes OUT_DIR/plan.json and OUT_DIR/data.js (window.PLAN = {...}) for
      artifact/index.html: trust averages, citation proof, priority scores,
      flags, sheet 1 (PR articles), sheet 2 (link insertions) and the cited
      domains that Collaborator.pro does not sell.

run.json is assembled by the lead agent from the probe answers, the
Collaborator.pro lookups and the trust answers. See README.md for its shape.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from urllib.parse import urlsplit

# Second-level suffixes where the registrable domain has three labels.
TWO_LEVEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "org.au",
    "co.nz", "org.nz", "com.br", "com.mx", "co.jp", "co.kr", "co.in",
    "com.sg", "com.tr", "com.cn", "com.hk", "co.za", "com.ar", "com.co",
}

# Domains that are never PR targets: app stores, search engines, video,
# forums, encyclopedias, code hosting and social networks.
DEFAULT_DROP = {
    "apple.com", "google.com", "search.google", "youtube.com", "reddit.com",
    "wikipedia.org", "github.com", "github.io", "facebook.com", "instagram.com",
    "x.com", "twitter.com", "tiktok.com", "linkedin.com", "pinterest.com",
    "vertexaisearch.cloud.google.com",
}

REDIRECT_HOSTS = ("vertexaisearch.cloud.google.com",)


def registrable_domain(url):
    """'https://www.travel.example.co.uk/a?b' -> 'example.co.uk'."""
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    if ".".join(labels[-2:]) in TWO_LEVEL_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def clean_url(url):
    """Canonical form of a cited URL, so the same page counts once.

    Drops tracking parameters such as ?utm_source=openai and lowercases the
    host without its 'www.' prefix ('https://www.A.com/x' -> 'https://a.com/x').
    """
    url = re.sub(r"[?&]utm_[a-z]+=[^&#]*", "", url or "")
    url = url.replace("?&", "?").rstrip("?")
    match = re.match(r"^(https?://)([^/?#]+)(.*)$", url, re.I)
    if match:
        host = match.group(2).lower()
        if host.startswith("www."):
            host = host[4:]
        url = match.group(1).lower() + host + match.group(3)
    return url


def parse_count(value):
    """'12.31K' -> 12310, '1.6M' -> 1600000, 'N/A' -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace(" ", "")
    match = re.fullmatch(r"([0-9]*\.?[0-9]+)([KkMm]?)", text)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2).lower()
    return number * (1000 if unit == "k" else 1000000 if unit == "m" else 1)


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def drop_set(run):
    product = run.get("product", {})
    drops = set(DEFAULT_DROP)
    for domain in [product.get("website", "")] + product.get("exclude_domains", []):
        if domain:
            drops.add(registrable_domain(domain))
    return drops


def is_dropped(domain, drops):
    return not domain or domain in drops or any(domain.endswith("." + d) for d in drops)


def collect_citations(run):
    """Every cited URL as a citation record, plus the unresolved redirect links."""
    drops = drop_set(run)
    citations, unresolved = [], 0
    for probe in run.get("probes", []):
        for result in probe.get("results", []):
            for raw in result.get("cited_urls", []):
                url = clean_url(raw)
                if not url or url == "UNRESOLVED" or any(h in url for h in REDIRECT_HOSTS):
                    unresolved += 1
                    continue
                domain = registrable_domain(url)
                if is_dropped(domain, drops):
                    continue
                citations.append(OrderedDict([
                    ("domain", domain),
                    ("engine", probe["engine"]),
                    ("label", probe.get("label", probe["engine"])),
                    ("prompt", result["prompt"]),
                    ("url", url),
                    ("run", probe.get("run", "")),
                    ("round", probe.get("round", "")),
                    ("date", probe.get("date", "")),
                ]))
    # One record per engine + prompt + URL.
    seen, unique = set(), []
    for c in citations:
        key = (c["engine"], c["round"], c["prompt"], c["url"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique, unresolved


def by_domain(citations):
    grouped = OrderedDict()
    for c in citations:
        grouped.setdefault(c["domain"], []).append(c)
    return grouped


def cmd_cited(run):
    citations, unresolved = collect_citations(run)
    rows = []
    for domain, items in by_domain(citations).items():
        rows.append({
            "domain": domain,
            "citations": len(items),
            "engines": sorted({c["label"] for c in items}),
        })
    rows.sort(key=lambda r: (-len(r["engines"]), -r["citations"], r["domain"]))
    return {"domains": rows, "unresolved_links": unresolved}


def flags_for(site, note):
    flags = []
    organic = parse_count(site.get("organic_traffic"))
    listed = parse_count(site.get("listed_traffic"))
    if organic is not None and (organic < 1000 or (listed and organic < 0.01 * listed)):
        flags.append("Inflated traffic: listed %s, organic %s" % (
            site.get("listed_traffic", "?"), site.get("organic_traffic", "?")))
    link = (site.get("link_type") or "").lower()
    if link == "sponsored":
        flags.append("Sponsored link")
    elif link == "nofollow":
        flags.append("Nofollow link")
    if note:
        flags.append(note)
    return flags


def priority(trust_avg, engines_citing, citation_count):
    score = 0.6 * (trust_avg or 0) + 15 * engines_citing + 2 * min(citation_count, 5)
    return min(100, int(round(score)))


def cmd_compute(run):
    citations, unresolved = collect_citations(run)
    grouped = by_domain(citations)
    collab = run.get("collaborator", {})
    notes = run.get("notes", {})
    pitches = run.get("pitches", {})
    engines = OrderedDict((p["engine"], p.get("label", p["engine"])) for p in run.get("probes", []))
    for t in run.get("trust", []):
        engines.setdefault(t["engine"], t.get("label", t["engine"]))

    trust = {}
    for answer in run.get("trust", []):
        for s in answer.get("scores", []):
            trust.setdefault(s["domain"], {})[answer["engine"]] = (s.get("score"), s.get("reason", ""))

    pr = []
    for domain in list(OrderedDict.fromkeys([d for d in grouped if d in collab] + run.get("catalog", []))):
        site = collab.get(domain)
        if not site:
            continue
        items = grouped.get(domain, [])
        scores = trust.get(domain, {})
        values = [v[0] for v in scores.values() if isinstance(v[0], (int, float))]
        avg = round(sum(values) / len(values), 1) if values else None
        citing = {c["engine"] for c in items}
        pr.append(OrderedDict([
            ("domain", domain),
            ("source", "cited" if items else "catalog"),
            ("trust", {e: scores.get(e, (None, ""))[0] for e in engines}),
            ("reasons", {e: scores.get(e, (None, ""))[1] for e in engines}),
            ("trust_avg", avg),
            ("citations", items),
            ("engines_citing", len(citing)),
            ("citation_count", len(items)),
            ("priority", priority(avg, len(citing), len(items))),
            ("price", site.get("price", "")),
            ("dr", site.get("dr")),
            ("listed_traffic", site.get("listed_traffic", "")),
            ("organic_traffic", site.get("organic_traffic")),
            ("link_type", site.get("link_type", "")),
            ("collaborator_url", site.get("url", "")),
            ("categories", site.get("categories", "")),
            ("added", site.get("added")),
            ("flags", flags_for(site, notes.get(domain))),
        ]))
    pr.sort(key=lambda r: (-r["priority"], -(r["trust_avg"] or 0), r["domain"]))

    li = []
    for row in pr:
        urls = OrderedDict()
        for c in row["citations"]:
            urls.setdefault(c["url"], []).append(c)
        for url, items in urls.items():
            pitch = pitches.get(url, {})
            li.append(OrderedDict([
                ("article_url", url),
                ("domain", row["domain"]),
                ("citations", items),
                ("engines_citing", len({c["engine"] for c in items})),
                ("price", row["price"]),
                ("dr", row["dr"]),
                ("link_type", row["link_type"]),
                ("collaborator_url", row["collaborator_url"]),
                ("trust_avg", row["trust_avg"]),
                ("flags", row["flags"]),
                ("suggested_anchor", pitch.get("anchor", "")),
                ("pitch", pitch.get("pitch", "")),
            ]))
    li.sort(key=lambda r: (-r["engines_citing"], -len(r["citations"]), r["article_url"]))

    na = []
    for domain, items in grouped.items():
        if domain not in collab:
            na.append({"domain": domain, "citations": len(items),
                       "engines": sorted({c["label"] for c in items})})
    na.sort(key=lambda r: (-len(r["engines"]), -r["citations"], r["domain"]))

    mentioned = OrderedDict((e, 0) for e in engines)
    answers = 0
    for probe in run.get("probes", []):
        for result in probe.get("results", []):
            answers += 1
            if result.get("product_mentioned"):
                mentioned[probe["engine"]] = mentioned.get(probe["engine"], 0) + 1

    runs = []
    for probe in run.get("probes", []):
        runs.append({"engine": probe["engine"], "label": probe.get("label", probe["engine"]),
                     "run": probe.get("run", ""), "round": probe.get("round", ""),
                     "date": probe.get("date", ""), "answers": len(probe.get("results", []))})

    return OrderedDict([
        ("product", run.get("product", {})),
        ("generated_at", run.get("generated_at", "")),
        ("engines", engines),
        ("mind_map", run.get("mind_map", {})),
        ("summary", OrderedDict([
            ("prompts", len({r["prompt"] for p in run.get("probes", []) for r in p.get("results", [])})),
            ("answers", answers),
            ("unique_cited_domains", len(grouped)),
            ("available_on_collaborator", sum(1 for r in pr if r["source"] == "cited")),
            ("catalog_candidates", sum(1 for r in pr if r["source"] == "catalog")),
            ("product_mentioned", mentioned),
            ("unresolved_links", unresolved),
        ])),
        ("pr", pr),
        ("li", li),
        ("na", na),
        ("runs", runs),
    ])


def write_outputs(plan, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "plan.json"), "w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "data.js"), "w", encoding="utf-8") as handle:
        handle.write("window.PLAN = " + json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + ";\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    cited = sub.add_parser("cited", help="list cited domains to check on Collaborator.pro")
    cited.add_argument("run")
    compute = sub.add_parser("compute", help="build plan.json and data.js")
    compute.add_argument("run")
    compute.add_argument("--out", default=".")
    args = parser.parse_args(argv)
    run = load(args.run)
    if args.command == "cited":
        json.dump(cmd_cited(run), sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
    else:
        plan = cmd_compute(run)
        write_outputs(plan, args.out)
        s = plan["summary"]
        print("%d answers, %d cited domains, %d on Collaborator.pro, %d catalog, %d link insertions -> %s"
              % (s["answers"], s["unique_cited_domains"], s["available_on_collaborator"],
                 s["catalog_candidates"], len(plan["li"]), args.out))


if __name__ == "__main__":
    main()
