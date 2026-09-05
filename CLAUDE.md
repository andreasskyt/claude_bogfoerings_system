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

### 3. Forbind til Dinero — MCP (anbefalet)

Tilføj Dineros officielle MCP-server:

```bash
claude mcp add --transport http --scope user dinero https://mcp.dinero.dk
```

Bed derefter brugeren køre `/mcp` i en interaktiv session og logge ind via **Visma Connect** (deres
almindelige Dinero-login). Ingen API-nøgler nødvendige. Genstart sessionen, så værktøjerne indlæses.

### 4. Test forbindelsen

Slå organisationen op via MCP-værktøjerne og bekræft virksomhedsnavn og regnskabsår med brugeren.

### 5. (Valgfrit) REST-API som fallback

Til masseudtræk, sletninger og batch-kørsler kan REST-API'et sættes op som supplement — se
`references/dinero-api.md` (kræver Dinero Pro/Total og personlige API-credentials i miljøvariabler;
aldrig i denne mappe, aldrig i git, aldrig i chatten).

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
