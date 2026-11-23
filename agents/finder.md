# Catalog finder: more options from Collaborator.pro

AI answers cite only a few sites that Collaborator.pro sells. This step adds
relevant sites from the catalog so the plan has more options. Catalog rows
are marked `catalog` in the report: no engine has cited them yet.

Run it in a code sandbox (call `collaborator_search_sites` from code and read
the results from memory), so large result sets never pass through the chat.

## Search

For 8–16 keywords taken from the mind map and the brief (the category,
topics, places and audiences), call `collaborator_search_sites` with:

```json
{"keywords": ["<keyword>"], "language": "en", "per_page": 100, "page": 1,
 "ahrefs_dr_min": 30, "placement_format": "article"}
```

and the next pages while there are more. Run each search once more with
`"added_to_catalog": "last_month"` and tag those sites as new. Use the
`language` and country filters that match the brief's market.

## Filter

Keep a site only if all of these hold:

- Its Collaborator.pro **categories** (not just the keyword match) fit the
  product's topic.
- Its audience matches the brief's market and language.
- Ahrefs organic traffic is at least 1,000 a month **and** at least 1% of the
  listed traffic. Sites that list far more traffic than they get from search
  are usually link farms.
- It has an Article price.
- It isn't a casino, betting, adult, crypto, loans, CBD or forex site, and its
  first category isn't finance, real estate, auto or sport (unless that is the
  product's topic).
- It isn't an excluded audience from the brief.

Rank by fit to the product, then by organic traffic, and keep the best 15–40.
Drop every domain already in the plan.

## Output

Add the chosen domains to `catalog` in `run.json` and their listings to
`collaborator` (`price`, `dr`, `listed_traffic`, `organic_traffic`,
`link_type`, `url`, `categories`, and `added` for sites new in the last
month). They go through the trust step like every other site.
