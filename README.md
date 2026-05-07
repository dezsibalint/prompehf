# Domain-specifikus League of Legends RAG coach ChatGPT API-val

Ez a projekt egy egyszerű, beadásra alkalmas proof-of-concept arra, hogyan lehet domain-specifikus League of Legends tudást hozzáadni a ChatGPT API-hoz YouTube oktatóvideók transcriptjeiből.

A megoldás Python alapú, RAG megközelítést használ, és az OpenAI Responses API-t kombinálja a `file_search` eszközzel. A cél nem production-grade rendszer, hanem egy gyorsan érthető, jól dokumentált és demózható egyetemi projekt.

## Problémafelvetés

A League of Legends játékosok gyakran nagyon konkrét kérdéseket tesznek fel:

- Hogyan játsszak jungle-ként, ha bot lane-nek nincs priority-je?
- Mikor érdemes recallolni mid lane-en?
- Hogyan kell értelmezni a wave managementet top lane-en?

Ezekre a kérdésekre egy általános chatbot sokszor túl általános választ ad. A cél az, hogy a modell oktató jellegű YouTube-videók transcriptjeiből származó külső tudást is fel tudjon használni a válaszadáshoz.

## Miért RAG és miért nem fine-tuning?

Ebben a projektben RAG-et, vagyis Retrieval-Augmented Generation megközelítést használunk fine-tuning helyett.

Ennek okai:

- A YouTube transcript tartalom könnyen cserélhető és bővíthető.
- Nem kell új modellt tanítani.
- Gyorsabban demózható és olcsóbb, mint a fine-tuning.
- A válaszok a feltöltött tudásbázisra támaszkodhatnak.
- Ha új videókat adunk hozzá, elég újra feltölteni a tudástárat.

A fine-tuning inkább akkor lenne indokolt, ha a modell stílusát, formátumát vagy viselkedési mintázatait szeretnénk tartósan megtanítani. Itt viszont a fő cél az aktuális külső tudástartalom visszakeresése és felhasználása.

## Architektúra

```text
YouTube oktatóvideók
→ transcript letöltés
→ szöveg tisztítása
→ tudásbázis feltöltése OpenAI Vector Store-ba
→ ChatGPT API válaszol League of Legends kérdésekre a tudásbázis alapján
```

## Működési lépések

1. A felhasználó YouTube URL-eket ír az `examples/video_urls.txt` fájlba.
2. A `download_transcripts.py` script letölti az angol transcriptet.
3. A nyers transcript fájlok a `data/raw/` mappába kerülnek.
4. A `preprocess_transcripts.py` script megtisztítja a szöveget.
5. A tisztított fájlok a `data/processed/` mappába kerülnek.
6. Az `upload_knowledge_base.py` script létrehoz egy OpenAI Vector Store-t és feltölti a fájlokat.
7. Az `ask_coach.py` script egy League of Legends coaching asszisztenst futtat, amely `file_search` segítségével keresi meg a releváns tudást.

## Telepítés

Python 3.10 vagy újabb verzió ajánlott.

```bash
python -m venv .venv
```

Windows PowerShell alatt:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux alatt:

```bash
source .venv/bin/activate
```

Függőségek telepítése:

```bash
pip install -r requirements.txt
```

## .env beállítás

Másold le a példafájlt:

```bash
cp .env.example .env
```

Windows PowerShell alatt:

```powershell
Copy-Item .env.example .env
```

Ezután töltsd ki az `.env` fájlt:

```env
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_STORE_NAME=league-of-legends-knowledge-base
YOUTUBE_API_KEY=your_youtube_data_api_key_here
```

Fontos: az `.env` fájl nem kerül GitHubra, mert a `.gitignore` tartalmazza.

## Futtatási parancsok

1. YouTube URL-ek megadása:

```text
examples/video_urls.txt
```

Egy sorba egy YouTube video URL kerüljön. Az üres sorokat és a `#` karakterrel kezdődő kommenteket a script figyelmen kívül hagyja.

Opcionális automatikus videókeresés YouTube Data API-val:

```bash
python src/discover_youtube_guides.py --limit 100 --output examples/video_urls.txt --overwrite
```

Nagyobb tudásbázishoz például:

```bash
python src/discover_youtube_guides.py --limit 1000 --months 3 --min-views 50000 --output examples/video_urls.txt --overwrite
```

Ez a külön modul az elmúlt 3 hónap népszerű, angol felirattal rendelkező League of Legends guide videóit keresi. A meglévő kézi workflow továbbra is működik, mert a `download_transcripts.py` továbbra is az `examples/video_urls.txt` fájlból dolgozik.

Fontos: a YouTube Data API keresési végpontja kvótát használ, és egy lekérés jelentős quota costtal jár. Emiatt a `--limit 1000` parancs technikailag támogatott, de a ténylegesen megtalált videók száma függhet az API kvótától, a keresési találatoktól, a feliratok elérhetőségétől és a szűrőktől.

2. Transcript letöltés:

```bash
python src/download_transcripts.py
```

3. Transcript tisztítás:

```bash
python src/preprocess_transcripts.py
```

4. Tudásbázis feltöltés OpenAI Vector Store-ba:

```bash
python src/upload_knowledge_base.py
```

5. Kérdés-válasz demó:

```bash
python src/ask_coach.py
```

## Példa kérdések

Az `examples/example_questions.txt` fájlban található néhány példa:

```text
How should I play jungle when my bot lane has no priority?
Explain wave management for top lane in simple terms.
When should I recall as mid laner?
How do I avoid dying to the enemy jungler?
What should an ADC do in mid game?
```

## Várható eredmény

Az `ask_coach.py` futtatásakor a felhasználó beír egy League of Legends kérdést. A program meghívja az OpenAI Responses API-t, amely a Vector Store-ban lévő transcript dokumentumok között keres, majd gyakorlati coaching jellegű választ ad.

A válaszoknak:

- gyakorlati tanácsokat kell adniuk,
- a feltöltött oktatóvideók tudására kell támaszkodniuk,
- jelezniük kell, ha nincs elég forrás,
- nem szabad kitalálniuk patch-specifikus adatokat.

## Projekt struktúra

```text
prompehf/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
├── src/
│   ├── download_transcripts.py
│   ├── discover_youtube_guides.py
│   ├── preprocess_transcripts.py
│   ├── upload_knowledge_base.py
│   ├── ask_coach.py
│   └── config.py
└── examples/
    ├── video_urls.txt
    └── example_questions.txt
```

## Korlátok

- Csak akkor működik, ha a YouTube videóhoz elérhető angol transcript.
- A projekt nem kezel nagy mennyiségű videót optimalizált módon.
- A válasz minősége erősen függ a feltöltött transcript minőségétől.
- A rendszer nem ellenőrzi automatikusan, hogy a videók tartalma aktuális-e az adott League of Legends patch szerint.
- A projekt oktatási célra készült, nem production-grade alkalmazás.

## Továbbfejlesztési lehetőségek

- Több nyelv támogatása transcript letöltésnél.
- Forrásmegjelölések megjelenítése a válaszok mellett.
- Egyszerű webes felület készítése.
- Automatikus video-lista kezelés csatorna vagy playlist alapján.
- Dokumentumok metaadatokkal való feltöltése, például role, lane vagy téma szerint.
- Patch-verzió szerinti szűrés.

## Kapcsolódás a prompt engineeringhez

A projekt prompt engineering szempontból azt mutatja be, hogy a modell viselkedése nem csak a prompt szövegén múlik, hanem azon is, milyen külső kontextust adunk neki. A coaching asszisztens instrukciója meghatározza a szerepet, a válaszstílust és a korlátokat, a RAG komponens pedig releváns domain-tudást ad a modellnek.

Ez a kombináció jól szemlélteti, hogyan lehet egy általános nyelvi modellt célzott, domain-specifikus asszisztenssé alakítani anélkül, hogy fine-tuningot alkalmaznánk.
