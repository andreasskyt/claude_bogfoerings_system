"""Skabelon til parsning af bankkontoudtog med indbygget validering.

Kontoudtog ser forskellige ud fra bank til bank. Tilpas TX_PATTERN til det
faktiske format — men BEHOLD valideringen. Den er hele pointen: parser du
kontoudtoget forkert, bliver alt hvad du bygger ovenpå også forkert.

Brug:
    pdftotext -layout kontoudtog.pdf statement.txt
    python parse_bank_statement.py statement.txt --expect-count 250 --expect-balance 12500.00
"""
import argparse
import csv
import re

# Tilpas denne. Eksemplet matcher: "01.02.2024 14.10  Leverandør  -1.234,56  12.345,67"
# Den valgfri valutagruppe fanger linjer som "... -101,54 USD -670,00  2.843,84"
# hvor beløbet i fremmed valuta står FØR beløbet i kontoens valuta.
TX_PATTERN = re.compile(
    r"^\s*(\d{2}\.\d{2}\.\d{4})\s+(\d{2}[.:]\d{2})\s+"     # dato, klokkeslæt
    r"(.+?)\s{2,}"                                          # tekst
    r"(-?[\d.]+,\d{2})(?:\s+[A-Z]{3})?"                     # beløb (+ evt. valutakode)
    r"(?:\s+[A-Z]{3}\s*(-?[\d.]+,\d{2}))?"                  # evt. beløb i kontovaluta
    r"\s+(-?[\d.]+,\d{2})\s*$"                              # saldo
)

# Fortsættelseslinjer (noter under en transaktion) — kraftigt indrykket.
NOTE_PATTERN = re.compile(r"^\s{15,}(\S.*\S|\S)\s*$")

# Linjer der ligner noter, men er sidehoved/-fod. Udvid efter behov.
NOISE = ("Dato", "Date", "Tekst", "Title", "Saldo", "Balance", "Side ", "Page ", "CVR")


def to_float(value):
    """Dansk talformat: 1.234,56 -> 1234.56"""
    return float(value.replace(".", "").replace(",", "."))


def parse(path):
    rows = []
    for line in open(path, encoding="utf-8", errors="replace").read().splitlines():
        match = TX_PATTERN.match(line)
        if match:
            date, clock, title, amount, alt_amount, balance = match.groups()
            rows.append({
                "date": f"{date[6:10]}-{date[3:5]}-{date[0:2]}",
                "time": clock.replace(".", ":"),
                "title": title.strip(),
                # Er der to beløb, er det ANDET i kontoens valuta.
                "amount": to_float(alt_amount or amount),
                "balance": to_float(balance),
                "note": "",
            })
        elif rows:
            note = NOTE_PATTERN.match(line)
            if note and not any(n in line for n in NOISE):
                rows[-1]["note"] = (rows[-1]["note"] + " " + note.group(1)).strip()
    rows.reverse()  # kronologisk rækkefølge
    return rows


def report_unparsed(path):
    """Linjer der starter med en dato, men ikke matchede — de afslører formatfejl."""
    bad = []
    for number, line in enumerate(
        open(path, encoding="utf-8", errors="replace").read().splitlines(), 1
    ):
        if re.match(r"^\s*\d{2}\.\d{2}\.\d{4}\s+\d{2}[.:]\d{2}", line):
            if not TX_PATTERN.match(line):
                bad.append((number, line))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("statement")
    ap.add_argument("--out", default="bank.csv")
    ap.add_argument("--expect-count", type=int,
                    help="Antal transaktioner ifølge kontoudtoget")
    ap.add_argument("--expect-balance", type=float,
                    help="Slutsaldo ifølge kontoudtoget")
    ap.add_argument("--opening-balance", type=float, default=0.0)
    args = ap.parse_args()

    rows = parse(args.statement)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["date", "time", "title", "amount", "balance", "note"]
        )
        writer.writeheader()
        writer.writerows(rows)

    total = sum(r["amount"] for r in rows)
    print(f"transaktioner : {len(rows)}")
    print(f"periode       : {rows[0]['date']} -> {rows[-1]['date']}" if rows else "tom")
    print(f"ind           : {sum(r['amount'] for r in rows if r['amount'] > 0):>14,.2f}")
    print(f"ud            : {sum(r['amount'] for r in rows if r['amount'] < 0):>14,.2f}")
    print(f"beregnet saldo: {args.opening_balance + total:>14,.2f}")

    unparsed = report_unparsed(args.statement)
    if unparsed:
        print(f"\nADVARSEL: {len(unparsed)} datolinjer matchede ikke mønsteret:")
        for number, line in unparsed[:10]:
            print(f"  linje {number}: {line.strip()[:100]}")

    ok = True
    if args.expect_count is not None and len(rows) != args.expect_count:
        print(f"\nFEJL: forventede {args.expect_count} transaktioner, fandt {len(rows)}")
        ok = False
    if args.expect_balance is not None:
        calculated = args.opening_balance + total
        if abs(calculated - args.expect_balance) > 0.005:
            print(f"\nFEJL: saldo {calculated:,.2f} != forventet {args.expect_balance:,.2f}")
            ok = False

    print("\nOK — kontoudtoget er parset korrekt." if ok
          else "\nRET PARSEREN FØR DU FORTSÆTTER.")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
