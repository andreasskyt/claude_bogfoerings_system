# Dinero REST-API — fallback og masseoperationer

**Foretræk MCP-serveren til dagligt arbejde** (se `dinero-adgang.md`). REST-API'et bruges hvor MCP ikke
rækker: posterings-udtræk til afstemning, sletninger, kontooprettelse og batch-kørsler.

## Sådan får brugeren API-adgang

Kræver **Dinero Pro eller Total**. Gratis- og Starter-abonnementer kan ikke bruge API'et.

1. Log ind på Dinero → vælg virksomheden
2. **Indstillinger → Udvidelser/Integrationer → API-nøgler**
3. Vælg **personlig integration** og anmod om credentials
4. Dinero sender **Client ID** og **Client Secret** på mail (typisk inden for få timer)
5. **API-nøglen** (en lang streng) findes samme sted i UI'et
6. **Organisations-ID** hentes fra `/v1/organizations` efter første login

Brugeren skal altså bruge fire ting: `CLIENT_ID`, `CLIENT_SECRET`, `API_KEY`, `ORGANIZATION_ID`.

**Gem dem som miljøvariabler — aldrig i kode, aldrig i git.** Fx i `.env.local` eller shell-profilen.

## Autentificering

OAuth2 password grant mod `https://authz.dinero.dk/dineroapi/oauth/token`.

- `Authorization: Basic <base64(CLIENT_ID:CLIENT_SECRET)>`
- Body: `grant_type=password&scope=read write&username=<API_KEY>&password=<API_KEY>`

Bemærk at API-nøglen bruges som **både** brugernavn og adgangskode. Token'et lever ca. en time — hent et nyt ved lange kørsler.

## Base-URL og versioner

`https://api.dinero.dk` — endpoints er versionerede pr. sti (`/v1/`, `/v1.1/`, `/v1.2/`). Nyere versioner findes kun for nogle endpoints. Den fulde OpenAPI-specifikation ligger på:

```
https://api.dinero.dk/openapi/v1/swagger.json
```

**Hent den og læs det aktuelle schema** i stedet for at gætte felter — den er autoritativ og ændrer sig.

## Vigtigste endpoints

| Formål | Metode og sti |
|---|---|
| Organisationer | `GET /v1/organizations` |
| Regnskabsår | `GET /v1/{org}/accountingyears` |
| Alle posteringer | `GET /v1/{org}/entries?fromDate=&toDate=` |
| Kontoplan (udgift) | `GET /v1/{org}/accounts/purchase` |
| Kontoplan (indtægt) | `GET /v1/{org}/accounts/entry` |
| Bankkonti | `GET /v1/{org}/accounts/deposit` · `POST` opretter ny |
| Momskoder | `GET /v1/{org}/vatTypes` |
| Kontakter | `GET/POST /v1/{org}/contacts` |
| Upload fil | `POST /v1/{org}/files` (multipart) |
| Købsbilag | `POST /v1.2/{org}/vouchers/purchase` · `PUT /v1.1/...{guid}` |
| Bogfør købsbilag | `POST /v1/{org}/vouchers/purchase/{guid}/book` |
| Manuelt bilag | `POST /v1/{org}/vouchers/manuel` |
| Bogfør manuelt bilag | `POST /v1/{org}/vouchers/manuel/{guid}/book` |
| Faktura | `POST /v1/{org}/invoices` |
| Bogfør faktura | `POST /v1/{org}/invoices/{guid}/book` |
| Registrér betaling | `POST /v1/{org}/invoices/{guid}/payments` |


## Momskoder og kontoplan — hent dem, fortolk dem ikke

`GET /v1/{org}/vatTypes` returnerer organisationens momskoder (fx dansk købs-/salgsmoms, koder for
EU- og tredjelandskøb med omvendt betalingspligt, repræsentation, m.fl.) med navn og sats.
`GET /v1/{org}/accounts/purchase` returnerer kontoplanen, hvor hver konto har en standardmomskode.

**Hent altid de aktuelle lister fra API'et frem for at antage koder eller kontonumre** — kontoplaner
tilpasses pr. virksomhed. Og husk: API'et fortæller hvilke koder der FINDES; hvilken kode der er
korrekt for en given transaktion, afgøres af din lovgivningsresearch (se `lovgivnings-research.md`).

Én kode er teknisk særlig: den bogstavelige streng `NONE`, som undertrykker moms helt — se faldgruberne nedenfor.

## Faldgruber — læs disse, de koster timer

### Tom momskode giver kontoens standardmoms

Sender du `VatCode: null` eller `""` på en bilagslinje, indsætter Dinero **kontoens standardmomskode**. Det betyder at der bliver taget momsfradrag, du ikke bad om.

For at undertrykke moms helt skal du sende den bogstavelige streng:

```json
"VatCode": "NONE"
```

Tom streng afvises med en valideringsfejl. `null` gør noget andet, end du tror.

### Læs altid tilbage efter skrivning

Efter oprettelse eller opdatering: hent bilaget og verificér `VatCode`, `VatAmountValue`, `AccountNumber` og `FileGuid`. Dette er den eneste pålidelige kontrol.

### Timestamp-feltet staves forskelligt

Bilag returnerer `Timestamp`. **Fakturaer returnerer `TimeStamp`** med stort S. Feltet skal med ved opdatering, sletning og bogføring for at undgå konflikter.

### DELETE kræver en body

Sletning af bilag kræver `Timestamp` i request-body som JSON — ikke som query-parameter:

```
DELETE /v1/{org}/vouchers/manuel/{guid}
Content-Type: application/json
{"Timestamp": "<timestamp>"}
```

### Rate limit

60 kald i minuttet. Indsæt pause mellem kald ved masseoperationer, og håndter HTTP 429 med genforsøg efter ventetid. Ved store kørsler: gem løbende hvad der er lykkedes, så en afbrudt kørsel kan genoptages.

### Datointerval skal ligge i ét regnskabsår

`GET /entries` afviser intervaller, der krydser regnskabsår. Hent regnskabsårene først og loop over dem.

### Kontantkøb vs. kreditkøb

`PurchaseType: "cash"` bogfører direkte mod en bankkonto — sæt `DepositAccountNumber`. Det passer til kortkøb og direkte hævninger.

`PurchaseType: "credit"` går via kreditorer og kræver `ContactGuid`. Brug det til fakturaer, der betales senere.

### RegionKey skal passe til momskoden

`RegionKey` er `DK`, `EU` eller `World`. Bogfører du med EU- eller verdens-momskode på et bilag markeret `DK`, afvises bogføringen med en fejl om at momskoden ikke passer til landet.

### Balancekonti kan ikke bruges på købsbilag

Konti som mellemregning, udlæg og skyldige poster er balancekonti. Forsøg på at oprette et købsbilag på dem fejler. Brug et **manuelt bilag** i stedet med `AccountNumber` og `BalancingAccountNumber`.

### Moms på manuelle bilag

Momsen beregnes af den konto, der bærer `AccountVatCode` — og fortegnet betyder noget. Skal en udgift *tilbageføres* (fx en refusion), så sæt udgiftskontoen som `AccountNumber` med et **negativt** beløb og momskoden på den konto. Lægger du i stedet det positive beløb på bankkontoen med momskode på modkontoen, bliver momsen nul.

### ExternalReference er din ven

Sæt et genkendeligt `ExternalReference` på alt du opretter (fx afledt af dato og beløb). Så kan du finde dine egne posteringer igen, undgå dubletter ved genkørsel, og verificere at du kun bogfører det, du selv har lavet.
