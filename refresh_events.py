import json, datetime, requests, bs4

SITES = [
  "https://www.gre.ac.uk/careers/meet-employers-and-network",
  "https://www.gre.ac.uk/careers/get-help-with-job-applications-and-interviews",
  "https://www.gre.ac.uk/careers"
]

def parse_events(html):
    soup = bs4.BeautifulSoup(html, "html.parser")
    events = []
    # Adjust selector to real site markup:
    for h in soup.select("h3, h4")[:15]:          # grab first 15 headings
        title = h.get_text(strip=True)
        if not title or len(title) < 10:          # skip short rubbish
            continue
        a = h.find_parent("a") or h.find("a")
        url = a["href"] if a and a.get("href") else ""
        events.append({"title": title, "url": url})
    return events

all_events = []
for site in SITES:
    try:
        r = requests.get(site, timeout=10)
        r.raise_for_status()
        all_events.extend(parse_events(r.text))
    except Exception as e:
        print("Could not fetch", site, "→", e)

json.dump(
    {
      "last_updated": datetime.datetime.utcnow().isoformat(),
      "events": all_events[:30]              # keep at most 30
    },
    open("events.json", "w", encoding="utf-8"),
    ensure_ascii=False, indent=2
)
print("Saved", len(all_events), "events to events.json")

