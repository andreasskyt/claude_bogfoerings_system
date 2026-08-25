# Dinero-bogføring — opsætningsinstruktioner til AI'en

Denne mappe er en Claude Code-skill til automatiseret bogføring i Dinero. Når brugeren siger
**"sæt det op"**, "installér", "kom i gang" eller lignende, så kør opsætningen nedenfor — trin for
trin, i rækkefølge, og fortæl undervejs hvad du gør.

## Opsætning

### 1. Forudsætninger

- Spørg om brugeren har **Dinero Pro eller Total**. Uden det findes API'et ikke — stop her og sig det ærligt.
- Tjek at `pdftotext` findes (`which pdftotext`). Mangler det: tilbyd at køre `brew install poppler`
  (macOS) eller pakkemanagerens tilsvarende på Linux.

### 2. Installér skillen

Kopiér hele denne mappe til brugerens skills-mappe, hvis den ikke allerede ligger der:

```bash
mkdir -p ~/.claude/skills && cp -R . ~/.claude/skills/dinero-bogfoering
```

### 3. Skaf API-adgang

Guid brugeren igennem i Dinero (detaljer i `references/dinero-api.md`):

1. Log ind på Dinero → vælg virksomheden
2. Indstillinger → Udvidelser/Integrationer → **API-nøgler**
3. Vælg **personlig integration** og anmod om credentials
4. **Client ID + Client Secret** kommer på mail (typisk inden for få timer) — opsætningen kan
   holde pause her; brugeren siger bare til, når mailen er landet
5. **API-nøglen** kopieres fra samme side i Dinero

### 4. Gem credentials — aldrig i denne mappe

Bed brugeren selv tilføje dette til sin shell-profil (`~/.zshrc` eller `~/.bashrc`) med de rigtige
værdier, og genstarte terminalen:

```bash
export DINERO_CLIENT_ID="..."
export DINERO_CLIENT_SECRET="..."
export DINERO_API_KEY="..."
```

Regler: skriv aldrig nøglerne ind i filer i denne mappe, commit dem aldrig til git, og opfordr ikke
brugeren til at indsætte dem i chatten hvis det kan undgås.

### 5. Test forbindelsen og find organisations-ID

`DINERO_ORGANIZATION_ID` kendes ikke endnu — den hentes fra API'et:

```bash
DINERO_ORGANIZATION_ID=0 python3 scripts/dinero_api.py
```

Svaret indeholder organisationens navn og `Id`. Vis navnet til brugeren og bekræft at det er den
rigtige virksomhed. Bed dem derefter tilføje den fjerde linje til shell-profilen:

```bash
export DINERO_ORGANIZATION_ID="<id fra svaret>"
```

Kør testen igen uden override og verificér at alt svarer.

### 6. Færdig — start arbejdet

Sig til brugeren at opsætningen er færdig, og at de kan gå i gang sådan her:

> Eksportér virksomhedens kontoudtog fra netbanken (PDF eller CSV) for den periode der skal ryddes
> op, vedhæft det, og skriv: **"ryd op i min bogføring"**

Derfra tager skillen over: læs `SKILL.md` og følg faserne — plan, spørgsmål, lovgivningsresearch,
audit, klassificering, bilagsjagt, kladder, brugerens godkendelse, bogføring, afstemning.

## Ufravigelige regler (gælder også under opsætning)

- Intet bogføres i Dinero uden brugerens eksplicitte godkendelse — alt oprettes som kladder først
- Ingen påstande om moms-, skatte- eller bogføringsregler uden dagsaktuel research med kilder
  (se `references/lovgivnings-research.md`)
- Credentials rører aldrig denne mappe, git eller chatten
