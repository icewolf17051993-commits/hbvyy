import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time

START_URL = "https://wikipedia.org"
MAKS_SIDER = 10
BOT_NAVN = "MinSoegemaskineBot"

# Tjek hjemmesidens robots.txt før vi går i gang
domaene = f"{urlparse(START_URL).scheme}://{urlparse(START_URL).netloc}"
rp = RobotFileParser()
rp.set_url(f"{domaene}/robots.txt")
try:
    rp.read()
except:
    pass # Hvis siden ikke har en robots.txt, er det tilladt at crawle

besoegte = set()
koe = [START_URL]

print(f"Starter offentlig crawler på {START_URL}...")

while koe and len(besoegte) < MAKS_SIDER:
    url = koe.pop(0)
    if url in besoegte:
        continue

    # 1. Respekter robots.txt
    if not rp.can_fetch(BOT_NAVN, url):
        print(f"Springer over (blokeret i robots.txt): {url}")
        continue

    try:
        svar = requests.get(url, timeout=10, headers={"User-Agent": f"{BOT_NAVN}/1.0"})
        if svar.status_code != 200:
            continue

        besoegte.add(url)
        soup = BeautifulSoup(svar.text, "html.parser")

        # 2. Respekter 'noindex' meta-tags
        robots_meta = soup.find("meta", attrs={"name": "robots"})
        if robots_meta and "noindex" in robots_meta.get("content", "").lower():
            print(f"Springer over (noindex): {url}")
            continue

        # 3. Hent titel og et kort resumé (snippet) til visning
        titel = soup.title.string.strip() if soup.title else "Ingen titel"
        meta_beskrivelse = soup.find("meta", attrs={"name": "description"})
        
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        ren_tekst = " ".join(soup.get_text().split())

        # Brug sidens egen meta-beskrivelse hvis den findes, ellers maks. 160 tegn
        if meta_beskrivelse and meta_beskrivelse.get("content"):
            snippet = meta_beskrivelse["content"].strip()[:200]
        else:
            snippet = ren_tekst[:160] + "..."

        # Gem maks. 1000 tegn til internt søgeindeks (vises IKKE offentligt)
        soege_indeks_tekst = ren_tekst[:1000]

        print(f"[{len(besoegte)}/{MAKS_SIDER}] Indekseret: {titel}")
        print(f"   Link: {url}")
        print(f"   Offentligt uddrag: {snippet}\n")

        # Find nye links på samme domæne
        for link in soup.find_all("a", href=True):
            fuldt_link = urljoin(url, link["href"]).split("#")
            if urlparse(fuldt_link).netloc == urlparse(START_URL).netloc:
                if fuldt_link not in besoegte:
                    koe.append(fuldt_link)

        time.sleep(1.5) # Høflig pause på 1,5 sekund mellem hver side

    except Exception as e:
        print(f"Fejl ved {url}: {e}")

print("Færdig!")
