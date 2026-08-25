---
name: dinero-bogfoering
description: >
  Automatisér bogføring i Dinero fra ende til anden — læs bankkontoudtog, find manglende bilag i
  mail/lokalt/betalingsgateways, undersøg gældende lovgivning, klassificér posteringer, opret kladder via
  Dineros API, og bogfør først når brugeren har godkendt. Brug denne skill når brugeren nævner Dinero,
  bogføring, regnskab, bilag, kvitteringer, moms, kontoudtog, afstemning, "jeg mangler at bogføre",
  "der er rod i mit regnskab", "kan du bogføre for mig", "find mine bilag", "afstem banken", eller
  beder om hjælp til et dansk virksomhedsregnskab. Virker for alle danske virksomheder med Dinero Pro/Total.
---

# Dinero-bogføring — fuld automatisering

Denne skill fører et rodet Dinero-regnskab tilbage til nul afvigelse mod banken.

## ⚠️ Vigtigst af alt: denne skill indeholder INGEN lovgivning

Skillen beskriver **udelukkende det tekniske workflow** — hvordan man læser data, finder bilag, taler
med Dineros API og strukturerer processen. Den påstår **intet** om moms, skat, fradrag, bogføringsregler,
selskabsret eller frister. Regler ændrer sig, og et statisk dokument bliver forkert.

**Derfor SKAL du som AI, hver gang skillen bruges:**

1. **Undersøge gældende dansk lovgivning på brugstidspunktet** — før du klassificerer så meget som
   én transaktion. Se `references/lovgivnings-research.md` for hvilke spørgsmål du skal have besvaret
   og hvilke kilder der er autoritative.
2. **Aldrig gengive en regel fra hukommelsen uden at verificere den** mod en aktuel, autoritativ kilde.
   Din træningsdata kan citere ophævede paragraffer.
3. **Aldrig præsentere en momskode, kontering eller fradragsvurdering som fakta** uden at kunne pege på
   den aktuelle kilde, den bygger på.
4. **Sige det højt, når noget er en vurdering** frem for et faktum — og anbefale revisor/skatterådgiver
   ved væsentlige eller tvivlsomme forhold. Du er et bogføringsværktøj, ikke en rådgiver.

## Kerneprincipper — brydes aldrig

1. **Intet bogføres uden brugerens eksplicitte godkendelse.** Alt lander som kladde. Brugeren siger
   "bogfør", derefter bogføres.
2. **Er du i tvivl, så spørg.** Bogfør aldrig noget du ikke forstår. En ubogført kladde er uendeligt
   bedre end en forkert postering.
3. **Læs altid tilbage efter skrivning.** Stol aldrig på hvad dit script *sendte* — hent posteringen
   fra API'et og verificér hvad der faktisk står. Dinero udfylder tomme felter med standardværdier.
4. **Al regelanvendelse bygger på dagsaktuel research** — aldrig på denne skill, aldrig på hukommelse.
5. **Den endelige test er afstemning på øren.** Bankkontoen i Dinero skal ramme den faktiske banksaldo
   med 0,00 kr afvigelse. Gør den ikke det, er noget forkert — find det.

## Faser

Kør faserne i rækkefølge. Spring aldrig godkendelses- eller research-fasen over.

### Fase 0 — Adgang

Verificér at API-adgangen virker, før du lover noget. Se `references/dinero-api.md` for hvordan brugeren
skaffer credentials (kræver Dinero Pro eller Total). Test forbindelsen og bekræft organisationens navn
og regnskabsår over for brugeren.

### Fase 1 — Plan og spørgsmål

**Byg en plan, før du rører noget.** Præsentér den, og stil alle de spørgsmål du er i tvivl om, i én
omgang — ikke drypvis.

Ting du typisk skal have afklaret med brugeren:

- **Hvilke bankkonti har virksomheden?** Separat moms-opsparing, skattekonto, valutakonto? Interne
  overførsler mellem egne konti må aldrig blive til indtægt eller udgift.
- **Betalingsgateways?** Stripe, MobilePay, PayPal m.fl. skaber en mellemstation mellem salg og
  bankindsættelse (se `references/gateway-model.md`).
- **Privat vs. firma.** Hvad er brugerens holdning til gråzoner? Få en regel, ikke bare enkeltsvar.
- **Lønsystem?** Lønkørsler kræver særskilt behandling.
- **Momsregistrering og -periode** — det afgør frister og om rettelser rammer indberettede perioder.
- **Periode** der skal ryddes op.
- **Hvem er ansat/ejer?** Afgør hvordan udbetalinger til personer skal forstås.

Gå ikke videre før du har svarene.

### Fase 2 — Lovgivningsresearch

**Obligatorisk, hver gang.** Gennemgå spørgsmålslisten i `references/lovgivnings-research.md` og besvar
hvert punkt med en aktuel, autoritativ kilde. Skriv dine konklusioner ned med kildehenvisning og dato —
de bliver grundlaget for alle klassificeringer i fase 5, og brugeren skal kunne se dem.

### Fase 3 — Hent data

**Bankkontoudtoget** — bed brugeren eksportere hele perioden fra netbanken (PDF eller CSV). Parse det
til en struktureret tabel.

Efter parsning: **verificér at summen af alle transaktioner rammer slutsaldoen præcist.** Gør den ikke
det, er parseren forkert — typisk fordi linjer i fremmed valuta har et ekstra beløbsfelt. Ret parseren,
indtil antal transaktioner og slutsaldo begge stemmer. Alt herefter bygger på disse data.

**Dinero-posteringerne** — hent alle posteringer for regnskabsåret via API'et. Bemærk at datointervallet
skal ligge inden for ét regnskabsår.

Se `scripts/dinero_api.py` og `scripts/parse_bank_statement.py`.

### Fase 4 — Audit: match bank mod bogholderi

Match hver banklinje mod posteringerne på bankkontoen i Dinero — samme beløb, dato inden for få dage.
Grådigt match, hvor hver postering kun bruges én gang.

Resultatet er tre lister:

1. **Banklinjer uden postering** → mangler at blive bogført
2. **Posteringer uden banklinje** → fejlposteringer, eller betalinger fra en anden konto
3. **Bogførte bilag uden vedhæftet fil** → manglende dokumentation

**Advarsel om falske match:** grådigt beløbsmatch parrer af og til to urelaterede posteringer med samme
beløb. Den endelige afstemning i fase 10 fanger dem — tag den alvorligt.

Præsentér auditten for brugeren som en rapport med tal og omfang, før du foreslår rettelser.

### Fase 5 — Klassificering

Foreslå konto og momskode for hver ikke-bogført transaktion — **baseret på din lovgivningsresearch fra
fase 2**, ikke på antagelser. Kontoplan og momskoder hentes fra API'et (se `references/dinero-api.md`);
hvilken kode der er korrekt hvornår, afgør din research.

Byg regler ud fra leverandørnavnet i banktekten, men **gennemgå de tvivlsomme enkeltvis med brugeren.**
Typiske tvivlstilfælde: ukendte modtagere, personoverførsler, engangskøb, alt der kan være privat, og
alt hvor din research viser skærpede dokumentationskrav.

Præsentér klassificeringen som en tabel grupperet efter konto. Bed om svar på tvivlslisten. Vis hvilke
research-konklusioner klassificeringen bygger på.

### Fase 6 — Bilagsjagt

For hver transaktion skal der findes dokumentation. Se `references/bilagsjagt.md` for metoderne
(lokale filer, mail, gateways, portaler — og rekonstruktion som sidste udvej).

Hvilken dokumentation der er *tilstrækkelig* til hvad, er et lovgivningsspørgsmål — afklar det i fase 2
og vær ærlig over for brugeren om kvalitetsforskellen på original, rekonstruktion og internt bilag.

### Fase 7 — Opret kladder

Opret alle posteringer som kladder via API'et med dokumentationen vedhæftet.

**Kør altid en pilot først:** opret 2-3 kladder, læs dem tilbage fra API'et, og verificér konto,
momskode, beløb og at bilaget sidder på. Først derefter masseoprettelse.

Respektér rate limit (60 kald/min) — pause mellem kald, håndter HTTP 429 med genforsøg, og gem løbende
hvad der er oprettet, så en afbrudt kørsel kan genoptages uden dubletter.

### Fase 8 — Brugerens godkendelse

**Stop her.** Præsentér:

- Antal kladder og samlet beløb
- Fordeling pr. konto
- Dokumentationsdækning: originaler, rekonstruktioner, interne bilag
- Dine research-konklusioner med kilder
- Alt du er usikker på
- En konkret stikprøve brugeren kan åbne i Dinero og tjekke

Bemærk at Dinero i UI'et viser forslag fra andre brugere ("Andre Dinero-brugere har bogført lignende
bilag som…") — det er ikke bogføringen. Kontoen står i konto-feltet. Forklar det, hvis brugeren studser.

Vent på et klart "bogfør".

### Fase 9 — Bogfør

Bogfør hver kladde. Log fejl frem for at stoppe — og rapportér dem ærligt bagefter. Gem løbende hvilke
der er bogført, så en afbrudt kørsel kan genoptages.

### Fase 10 — Afstem

Hent posteringerne igen og sammenlign bankkontoen i Dinero med den faktiske banksaldo.

**Afvigelsen skal være 0,00 kr.** Er den ikke det, så opdel restbeløbet i navngivne poster, indtil hver
krone er forklaret. Uforklarede afvigelser er altid en fejl.

Rapportér til sidst: afstemning, åbne punkter, og hvad brugeren bør tage med til sin revisor.

## Efter oprydningen

Foreslå en fast månedsrutine: nye banklinjer → match → bilagsjagt → kladder → godkendelse → bogføring.
Bilag er langt lettere at skaffe i samme måned end et halvt år senere. Nævn også Dineros
bilags-mailadresse og app-fotografering af papirbonner — det fjerner rekonstruktionsbehovet fremadrettet.

## Referencer

- `references/dinero-api.md` — API-adgang, autentificering, endpoints, tekniske faldgruber
- `references/lovgivnings-research.md` — HVAD der skal undersøges og HVOR (indeholder ingen svar)
- `references/bilagsjagt.md` — find dokumentation i mail, lokalt, portaler
- `references/gateway-model.md` — teknisk model for betalingsgateways (mellemkonto, valuta)
- `scripts/dinero_api.py` — API-klient med autentificering, upload, kladder, bogføring
- `scripts/parse_bank_statement.py` — skabelon til parsning af kontoudtog med validering
