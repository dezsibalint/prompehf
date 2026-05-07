# Beadási dokumentáció

## Feladat azonosítója és címe

**Feladat azonosítója:** PE-HF-LOL-RAG-01

**Feladat címe:** ChatGPT API domain-specifikus tudás tanítása YouTube videók által

A projekt témája egy League of Legends témájú, domain-specifikus tudásbázissal támogatott ChatGPT API alapú coaching asszisztens készítése. A rendszer YouTube oktatóvideók transcriptjeiből épít tudásbázist, majd az OpenAI API segítségével válaszol játékbeli kérdésekre.

## Beadó

**Név:** Dezsi Bálint

A projekt egyéni beadandóként készült. A megvalósítás során a kódolási és repo-építési részhez Codex asszisztens is használva volt. A projektötlet, a fő követelmények, a működési irány, a tesztelési szempontok és a fejlesztési promptok a beadótól származtak; a Codex a kódgenerálásban, strukturálásban, hibakezelés finomításában és dokumentációs részek megfogalmazásában segített.

## Rövid leírás

A feladat célja az volt, hogy egy általános nyelvi modell ne csak saját belső tudása alapján válaszoljon League of Legends kérdésekre, hanem külső, domain-specifikus forrásokra is támaszkodjon. Ehhez YouTube oktatóvideók transcriptjeit használja a projekt. A transcript letöltése, tisztítása, feldolgozása és OpenAI Vector Store-ba feltöltése külön Python scriptekkel történik.

A megoldás RAG, vagyis Retrieval-Augmented Generation megközelítést használ. Ez azt jelenti, hogy a modell válaszadás előtt a feltöltött tudásbázisban keres releváns tartalmat, majd ezt használja a válasz összeállításához. A projekt nem fine-tuningot alkalmaz, mert a cél nem a modell újratanítása, hanem gyorsan cserélhető és bővíthető külső tudás hozzáadása.

A fejlesztés során sikerült egy működő, jól elkülönített modulokból álló proof-of-concept rendszert létrehozni. A kézi videólista mellett készült egy külön automatikus YouTube kereső modul is, amely friss és népszerű League of Legends guide videókat tud keresni YouTube Data API segítségével. A rendszer továbbra is egyszerű maradt: minden fő lépés külön scriptből futtatható, így jól demózható egyetemi beadandóként.

## A megoldás röviden

A projekt fő architektúrája:

```text
YouTube oktatóvideók
→ transcript letöltés
→ szöveg tisztítása
→ tudásbázis feltöltése OpenAI Vector Store-ba
→ ChatGPT API válaszol League of Legends kérdésekre a tudásbázis alapján
```

A rendszer fő komponensei:

- `src/download_transcripts.py`: YouTube URL-ek alapján transcriptet tölt le.
- `src/preprocess_transcripts.py`: megtisztítja a transcript szövegeket.
- `src/upload_knowledge_base.py`: feltölti a feldolgozott dokumentumokat OpenAI Vector Store-ba.
- `src/ask_coach.py`: kérdés-válasz demót futtat Responses API és `file_search` használatával.
- `src/discover_youtube_guides.py`: opcionálisan automatikusan keres YouTube guide videókat.
- `examples/video_urls.txt`: kézzel vagy automatikusan megadott YouTube URL-ek.
- `examples/example_questions.txt`: tesztkérdések a demóhoz.

## GitHub repó

A projekt GitHub repója:

```text
git@github.com:dezsibalint/prompehf.git
```

GitHub URL:

```text
https://github.com/dezsibalint/prompehf
```

## Használt technológiák

- Python
- OpenAI API
- OpenAI Responses API
- OpenAI Vector Store
- `file_search` eszköz
- `youtube-transcript-api`
- `python-dotenv`
- YouTube Data API
- Git és GitHub

## Miért RAG?

A projektben RAG megközelítést választottam fine-tuning helyett, mert a feladat célja külső tudás használata volt. A YouTube transcript tartalom gyakran változhat, bővíthető, törölhető vagy újra feldolgozható. Fine-tuning esetén a modell újratanítása lassabb, drágább és kevésbé rugalmas lenne.

RAG esetén elég új dokumentumokat feltölteni a tudásbázisba, majd a modell a válaszadáskor ezekből keres. Ez egyszerűbb, jobban illeszkedik egy proof-of-concept egyetemi beadandóhoz, és jobban szemlélteti a prompt engineering gyakorlati szerepét is.

## Futtatási workflow

Telepítés:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Környezeti változók beállítása:

```powershell
Copy-Item .env.example .env
```

Az `.env` fájlban szükséges:

```env
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_STORE_NAME=league-of-legends-knowledge-base
YOUTUBE_API_KEY=your_youtube_data_api_key_here
```

Kézi videólista esetén:

```powershell
python src/download_transcripts.py
python src/preprocess_transcripts.py
python src/upload_knowledge_base.py
python src/ask_coach.py
```

Automatikus videókeresés esetén:

```powershell
python src/discover_youtube_guides.py --limit 100 --months 12 --min-views 1000 --caption any --max-pages-per-query 1 --output examples/video_urls.txt --append
```

Ezután ugyanúgy futtatható a transcript letöltés, feldolgozás, feltöltés és kérdés-válasz demó.

## Tesztkérdések

A rendszer tesztelésére használható kérdések:

```text
How should I play jungle when my bot lane is losing and I have no dragon control?
How should I play jungle when my bot lane has no priority?
Explain wave management for top lane in simple terms.
When should I recall as mid laner?
How do I avoid dying to the enemy jungler?
What should an ADC do in mid game?
```

A RAG-alapú válasz akkor tekinthető jobbnak egy alap ChatGPT válasznál, ha konkrétabb, gyakorlatiasabb, jobban kapcsolódik a feltöltött oktatóvideók tartalmához, és nem talál ki patch-specifikus adatokat.

## A coaching prompt

Az `ask_coach.py` scriptben szereplő instrukció:

```text
Te egy League of Legends coaching asszisztens vagy.
A válaszaidhoz az oktató YouTube-videókból készült tudásbázist használd.
Gyakorlati, játék közben alkalmazható tanácsokat adj.
Ha a tudásbázis nem tartalmaz elég információt, mondd meg, hogy erre nincs elég forrás.
Ne találj ki patch-specifikus adatokat.
```

Ez a prompt határozza meg a modell szerepét, a válaszadás stílusát és a korlátokat. A prompt engineering itt nem önmagában jelenik meg, hanem a RAG rendszerrel együtt: a modell instrukciót kap arra, hogyan használja a külső tudásbázist.

## Fejlesztési promptok

A fejlesztéshez használt első, fő prompt lényege:

```text
Készíts egy teljes, beadásra alkalmas GitHub repót egy egyetemi prompt engineering házihoz.

A projekt témája:
Domain-specifikus League of Legends tudás hozzáadása ChatGPT API-hoz YouTube oktatóvideók transcriptjeiből.

Fő technológiai irány:
- Python alapú projekt
- OpenAI API használata
- RAG megközelítés, ne fine-tuning
- YouTube transcript letöltés
- transcript tisztítás
- dokumentumok mentése
- kérdés-válasz demó League of Legends témában
- GitHub README, ami elmagyarázza a projektet

Fontos:
A cél nem production-grade rendszer, hanem beadandó minőségű, jól dokumentált, működőképes proof-of-concept.

A projekt struktúrája tartalmazza:
- README.md
- requirements.txt
- .env.example
- .gitignore
- data/raw
- data/processed
- src/download_transcripts.py
- src/preprocess_transcripts.py
- src/upload_knowledge_base.py
- src/ask_coach.py
- src/config.py
- examples/video_urls.txt
- examples/example_questions.txt

OpenAI API-nál használj modern megközelítést.
Használj Responses API-t és file_search eszközt a kérdés-válasz demóhoz.
```

Későbbi fontosabb promptok:

```text
How can I test it and see if it gives back better answer than basic ChatGPT?
```

```text
Can we add a module that scans automatically for YouTube League of Legends guides that are max 3 months old and popular and automatically gets them in a configurable way?
```

```text
Van --append is hogyha csak hozzá akarok adni?
```

Ezek alapján készült el az összehasonlítható tesztelési workflow, az automatikus YouTube guide kereső modul, az append/overwrite működés, valamint a YouTube API quota hibák kezelése.

## Alátámasztó anyagok

A megoldást alátámasztó elemek:

- GitHub repó: `https://github.com/dezsibalint/prompehf`
- Futtatható Python scriptek a `src/` mappában.
- Példakérdések az `examples/example_questions.txt` fájlban.
- YouTube videó URL-ek az `examples/video_urls.txt` fájlban.
- OpenAI Vector Store azonosító lokálisan a `vector_store_id.txt` fájlban.
- README dokumentáció magyar nyelven.
- Ez a beadási dokumentáció.

Képernyőképnek javasolt beadási bizonyítékok:

- GitHub repó főoldala.
- Sikeres `python src/download_transcripts.py` futás.
- Sikeres `python src/preprocess_transcripts.py` futás.
- Sikeres `python src/upload_knowledge_base.py` futás.
- `python src/ask_coach.py` kérdés-válasz eredménye.
- Összehasonlítás egy alap ChatGPT válasszal ugyanarra a kérdésre.

## Érdekes tanulságok

Az egyik legfontosabb tanulság az volt, hogy domain-specifikus tudás hozzáadásához nem mindig fine-tuning a legjobb megoldás. Egy jól felépített RAG rendszer gyorsabban elkészíthető, könnyebben módosítható, és jobban illik olyan tartalmakhoz, amelyek gyakran változnak vagy külső forrásból származnak.

Érdekes gyakorlati tapasztalat volt a YouTube Data API quota limitje. A népszerű, friss videók automatikus keresése technikailag megoldható, de a YouTube keresési végpontja gyorsan fogyasztja a napi kvótát. Emiatt a scriptbe bekerült quota-barátabb működés, részleges mentés és érthetőbb hibaüzenet.

Prompt engineering szempontból az is tanulságos volt, hogy nem elég azt mondani a modellnek, hogy "válaszolj League of Legends coachként". A jobb válaszokhoz szerepet, forráshasználati szabályt, gyakorlati válaszstílust és korlátokat is meg kell adni. A `file_search` eszköz és a Vector Store pedig azt biztosítja, hogy a modell ne csak általános tudásból válaszoljon, hanem a feltöltött oktatóanyagok alapján is.

## Összefoglalás

A projekt egy működőképes, egyszerűen demózható League of Legends coaching asszisztens proof-of-concept. A rendszer YouTube transcript alapú tudásbázist épít, azt OpenAI Vector Store-ba tölti, majd Responses API és `file_search` segítségével válaszol kérdésekre.

A beadandó jól szemlélteti, hogyan lehet egy általános ChatGPT API alapú rendszert domain-specifikusabbá tenni prompt engineering és RAG kombinációjával, fine-tuning nélkül.
