# Adgang til Dinero — MCP først, REST som fallback

## Anbefalet: Dineros officielle MCP-server (beta)

Ingen API-nøgler, ingen ansøgning — brugeren logger ind med sit eget Dinero-login via Visma Connect,
og assistenten kan derefter kun det, brugeren selv kan.

Tilføj serveren i Claude Code:

```bash
claude mcp add --transport http --scope user dinero https://mcp.dinero.dk
```

(Virker forbindelsen ikke, så prøv adressen `https://mcp.dinero.dk/mcp` — samme server.)

Derefter skal brugeren autentificere: kør `/mcp` i en interaktiv Claude Code-session og gennemfør
Visma Connect-login. Genstart sessionen, hvis værktøjerne ikke dukker op.

**Hvad serveren kan** (ifølge Dineros dokumentation — beta, kan ændre sig):
opslag i fakturaer, kontakter, produkter og kontoplan · oprette og bogføre fakturaer, kreditnotaer,
køb og kassekladder · registrere betalinger · hente bilag som PDF · uploade dokumenter til
bilagsarkivet · rapporter som saldobalance og kontospecifikation.

**Arbejdsregler med MCP:**
- Tjek altid hvilke værktøjer serveren udstiller i den aktuelle session, før du planlægger — beta
  betyder at funktioner tilføjes og fjernes uden varsel
- Kerneprincipperne gælder uændret: kladder først, brugerens godkendelse før bogføring, læs tilbage
  efter skrivning, ingen momsfradrag uden originalbilag
- Feedback til Dinero-teamet kan sendes direkte gennem assistenten ("send feedback vedrørende … til
  Dinero")

## Fallback: REST-API'et

Brug REST når MCP-serveren mangler noget — typisk masseudtræk af posteringer til afstemning,
sletning af bilag, oprettelse af konti, eller store batch-kørsler med rate-styring. Kræver Dinero
Pro/Total og personlige API-credentials. Opsætning, endpoints og faldgruber: se `dinero-api.md`;
klar-til-brug klient: `scripts/dinero_api.py`.
