# Betalingsgateways — teknisk model (mellemkonto og valuta)

Gælder Stripe, PayPal, MobilePay, Shopify Payments og lignende, hvor pengene ikke går direkte fra
kunden til bankkontoen: gatewayen opkræver kunden, trækker sit gebyr, og udbetaler nettobeløbet til
banken — ofte dage senere og som sammenlægning af flere salg.

**Momsbehandling af salgene, gebyrerne og kravene til fakturaer er lovgivningsspørgsmål** — de afklares
i research-fasen. Denne fil beskriver den tekniske model, der bevarer al information.

## Problemet med at bogføre netto

Bogføres kun nettoudbetalingen fra banken, forsvinder information: det fulde salgsbeløb, gebyret og
sammenhængen til de enkelte fakturaer kan ikke rekonstrueres fra bankkontoen alene. Undersøg i
research-fasen, hvad gældende regler kræver om bruttoregistrering og modregning — og notér at
netto-bogføring også gør momsgrundlaget for salget usynligt.

Modellen nedenfor registrerer alt brutto og mister ingen information.

## Modellen

Opret gatewayen som en **konto af bank-typen i regnskabet** (`POST /v1/{org}/accounts/deposit`).
Den fungerer som mellemstation mellem salg og bankindsættelse.

Flowet pr. salg:

1. **Faktura** oprettes og bogføres med den momsbehandling, din research tilsiger for den konkrete
   kundetype (indland/EU/tredjeland, erhverv/privat)
2. **Betalingen registreres på gateway-kontoen** (ikke banken) med fakturaens fulde beløb
3. **Gebyret bogføres** som omkostning mod gateway-kontoen — momsbehandlingen afklares i researchen
4. **Udbetalingen bogføres** som overførsel fra gateway-kontoen til banken, med præcis det beløb der
   ramte bankkontoen

Til sidst skal gateway-kontoens saldo svare til det, der reelt står hos udbyderen — typisk penge
opkrævet men endnu ikke udbetalt. Det er korrekt og skal ikke nulstilles.

Hent tallene fra gatewayens API frem for at gætte: de fleste udbydere eksponerer balance-transaktioner,
hvor hvert salg, gebyr og udbetaling fremgår med præcise beløb — og hvilke salg hver udbetaling dækker.

## Fremmed valuta

Sælges der i fremmed valuta, opstår en kursdifference, fordi fakturaen omregnes på én dato og
udbetalingen på en anden.

Beregn gebyret i den fremmede valuta som `bruttobeløb − udbetalt beløb` og omregn til lokal valuta med
udbetalingens kurs. Restbeløbet, der får udbetalingen til at stemme mod fakturaen, er kursdifferencen
og bogføres på en valutakursdifference-konto.

Ét bilag pr. udbetaling med disse linjer:

| Linje | Debet | Kredit |
|---|---|---|
| Udbetaling | Bank | Gateway-konto |
| Gebyr | Gebyrkonto | Gateway-konto |
| Kursdifference | Gateway-konto *eller* kurstab | Kursgevinst *eller* gateway-konto |

Kontrollér at gateway-kontoens bevægelse præcis modsvarer fakturabeløbet. Gør den ikke det, er et af
tallene forkert.

## Salg via betalingslink uden faktura

Bruges betalingslinks frem for fakturaer, findes der ofte ingen faktura i regnskabssystemet — kun en
kvittering fra gatewayen. Undersøg i research-fasen, hvilke fakturakrav der gælder for de konkrete
salg, hvad der skal ske når fakturaen mangler, hvilken dato en efterudstedt faktura må bære, og
hvilken periode momsen skal henføres til.

Kontrollér også, om der findes annullerede fakturaer i regnskabssystemet, som dækker penge der reelt
er modtaget via links — omsætningen skal med, uanset hvilken kanal betalingen kom igennem.

## Kontrol til sidst

- Summen af udbetalinger fra gatewayen skal matche indbetalingerne på bankkontoudtoget, krone for krone
- Gateway-kontoens restsaldo skal svare til det, der står hos udbyderen
- Hver udbetaling skal kunne spores tilbage til de fakturaer, den dækker
