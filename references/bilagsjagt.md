# Bilagsjagt — sådan findes den manglende dokumentation

Rent teknisk workflow. **Hvilken dokumentation der er tilstrækkelig til moms- og skattefradrag, er et
lovgivningsspørgsmål** — det afklares i research-fasen, ikke her. Denne fil handler om at *finde* filerne.

Rækkefølgen er vigtig: gå fra det billigste og mest komplette til det dyreste. De fleste bilag findes i mailen.

## 1. Lokale filer

Start her — det er gratis og hurtigt.

```bash
# find kvitteringer efter filnavn
find ~/Downloads ~/Documents ~/Desktop -type f \( -iname "*.pdf" -o -iname "*.png" -o -iname "*.jpg" \) \
  \( -iname "*faktura*" -o -iname "*invoice*" -o -iname "*receipt*" -o -iname "*kvittering*" \) 2>/dev/null

# find efter indhold i PDF'er (kræver poppler: brew install poppler)
for f in ~/Downloads/*.pdf; do
  pdftotext -layout "$f" - 2>/dev/null | grep -qi "leverandørnavn" && echo "$f"
done

# macOS: søg i Spotlight-indekset, også inde i dokumenter
mdfind -onlyin ~ "faktura leverandørnavn"

# find filer i en periode
find ~/Downloads -type f -newermt "2024-01-01" ! -newermt "2024-12-31"
```

Læs altid PDF'en for at bekræfte leverandør, dato og beløb, før du parrer den med en transaktion — filnavne lyver.

## 2. Mailen

De fleste leverandører sender kvittering på mail. Søg pr. leverandør, ikke bredt.

Nyttige søgemønstre (Gmail-syntaks):

```
from:leverandør.dk (faktura OR kvittering OR invoice OR receipt) after:2024/01/01
subject:(faktura OR invoice) has:attachment after:2024/01/01
"ordrebekræftelse" after:2024/01/01 before:2024/12/31
```

Tre typer resultater:

**a) PDF vedhæftet** — det bedste. Hent filen og gem den.

**b) Link til PDF** — mange betalingsudbydere linker til en faktura-PDF, der kan hentes uden login.
Test linket; virker det, så hent den rigtige faktura. Bemærk at sådanne links ofte **udløber efter
ca. 30 dage**, så gamle mails giver kun en HTML-fejlside.

**c) Kun HTML i mailen** — leverandøren har sendt kvitteringen som formateret mail uden vedhæftning.
Så rekonstruér: udtræk beløb, dato, fakturanummer, referencenummer, moms og leverandørens oplysninger
fra mailteksten, skriv det til en struktureret tekstfil og konvertér til PDF. Markér tydeligt i
dokumentet, at det er rekonstrueret fra leverandørens mail, og gem reference til kildemailen. Al data
kommer fra leverandørens egen mail — men afklar i research-fasen, hvad en rekonstruktion kan bruges til.

```bash
# tekst -> PDF (macOS, indbygget)
cupsfilter kvittering.txt > kvittering.pdf

# alternativt på Linux
pandoc kvittering.txt -o kvittering.pdf
```

**Bemærk om mail-integrationer:** mange mail-værktøjer kan læse mails, men ikke hente vedhæftninger.
Kan du se at en PDF findes, men ikke hente den, så noter mailens ID og filnavn og hent den via
browseren i stedet.

## 3. Betalingsgateways og API'er

Har virksomheden en betalingsgateway, kan gebyrer og udbetalinger ofte hentes direkte via API med en
læse-nøgle. Det giver præcise tal frem for gæt. Se `gateway-model.md`.

## 4. Leverandørportaler

Det der ikke findes i mailen, ligger i leverandørens eget dashboard: annonceplatforme, cloud-udbydere,
abonnementstjenester, rejsebureauer.

Dette kræver login og dermed brugerens medvirken. To muligheder:

- Brugeren henter selv filerne (giv en præcis liste med links og hvad der skal hentes)
- Browserautomatisering med brugerens eksplicitte tilladelse

Bruger du browseren til at downloade flere filer, skal browseren typisk have lov til automatiske
downloads for det pågældende domæne.

**Bed aldrig om adgangskoder i chatten.** Brug brugerens egen password manager eller lad brugeren
logge ind selv.

## 5. Internt udgiftsbilag — sidste udvej

For fysiske køb hvor der aldrig har eksisteret en digital kvittering (restauranter, dagligvarer, taxa,
parkering) kan der udarbejdes et internt udgiftsbilag med reference til banktransaktionen.

Bilaget bør indeholde: dato, leverandør, beløb, betalingsmiddel, kontering, formål, og en tydelig note
om at originalkvitteringen ikke foreligger.

**Hvad et internt bilag er værd — og hvilke fradrag der i givet fald må tages på det — er et
lovgivningsspørgsmål.** Afklar det i research-fasen, sørg for at posteringen stemmer overens med det
bilaget påstår, og vær ærlig over for brugeren om kvalitetsforskellen. Jagt altid originalen først,
især for store beløb. Findes der notekrav for bestemte udgiftstyper (fx deltagere/anledning), så
indhent oplysningerne fra brugeren og skriv dem på bilaget, inden der bogføres.

Generér interne bilag programmatisk ud fra transaktionslisten, og gem både tekst og PDF.

## Navngivning og arkiv

Saml alle bilag i én mappe med ensartet navngivning:

```
YYYY-MM-DD leverandør beløbvaluta.pdf
```

Det gør automatisk match mod banktransaktioner muligt (dato + beløb), og det gør arkivet brugbart for
revisor. Kopiér altid filer ind i arkivet frem for at flytte dem.

## Match bilag til transaktion

Match på beløb først, dato dernæst. Vær opmærksom på:

- **Valutakøb:** kvitteringen er i fremmed valuta, banken i lokal valuta. Match på dato og leverandør,
  ikke beløb.
- **Dato forskydes:** kortkøb bogføres i banken 1-3 dage efter kvitteringens dato.
- **Samlefakturaer:** én faktura kan dække flere banktræk, og ét træk kan dække flere fakturaer.
- **Abonnementer med samme beløb** hver måned kræver dato-nærhed for at ramme rigtigt.

Fejlmatch fanges i den endelige afstemning. Tag den alvorligt.
