"""Minimal Dinero API-klient.

Credentials læses fra miljøvariabler — læg dem ALDRIG i koden:
    DINERO_CLIENT_ID, DINERO_CLIENT_SECRET, DINERO_API_KEY, DINERO_ORGANIZATION_ID

Se references/dinero-api.md for hvordan de skaffes.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = "https://api.dinero.dk"
AUTH = "https://authz.dinero.dk/dineroapi/oauth/token"


class Dinero:
    def __init__(self):
        self.client_id = os.environ["DINERO_CLIENT_ID"]
        self.client_secret = os.environ["DINERO_CLIENT_SECRET"]
        self.api_key = os.environ["DINERO_API_KEY"]
        self.org = os.environ["DINERO_ORGANIZATION_ID"]
        self.token = None
        self.token_time = 0

    def auth(self):
        """Token'et lever ca. en time; fornyes automatisk."""
        if self.token and time.time() - self.token_time < 3000:
            return self.token
        basic = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        data = urllib.parse.urlencode({
            "grant_type": "password",
            "scope": "read write",
            "username": self.api_key,
            "password": self.api_key,
        }).encode()
        req = urllib.request.Request(AUTH, data=data, method="POST")
        req.add_header("Authorization", f"Basic {basic}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req) as r:
            self.token = json.load(r)["access_token"]
            self.token_time = time.time()
        return self.token

    def call(self, method, path, body=None, retries=3):
        """Kald API'et. {org} i path erstattes automatisk. Håndterer 429."""
        path = path.replace("{org}", self.org)
        for attempt in range(retries):
            req = urllib.request.Request(BASE + path, method=method)
            req.add_header("Authorization", "Bearer " + self.auth())
            data = None
            if body is not None:
                data = json.dumps(body).encode()
                req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, data) as r:
                    text = r.read().decode()
                    return r.status, (json.loads(text) if text else {})
            except urllib.error.HTTPError as e:
                payload = e.read().decode() or "{}"
                if e.code == 429 and attempt < retries - 1:
                    time.sleep(20)
                    continue
                try:
                    return e.code, json.loads(payload)
                except ValueError:
                    return e.code, {"raw": payload[:400]}
        return 0, {}

    def upload_file(self, path):
        """Upload et bilag. Returnerer (status, {"FileGuid": ...})."""
        boundary = uuid.uuid4().hex
        name = os.path.basename(path)
        with open(path, "rb") as fh:
            content = fh.read()
        head = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode()
        body = head + content + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{BASE}/v1/{self.org}/files", data=body, method="POST"
        )
        req.add_header("Authorization", "Bearer " + self.auth())
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, {"raw": e.read().decode()[:400]}

    # --- læsning ---

    def entries(self, from_date, to_date):
        """Posteringer. Intervallet skal ligge inden for ét regnskabsår."""
        return self.call(
            "GET", f"/v1/{{org}}/entries?fromDate={from_date}&toDate={to_date}"
        )

    def accounting_years(self):
        return self.call("GET", "/v1/{org}/accountingyears")

    def purchase_accounts(self):
        """Kontoplan med hver kontos standardmomskode."""
        return self.call("GET", "/v1/{org}/accounts/purchase")

    def deposit_accounts(self):
        return self.call("GET", "/v1/{org}/accounts/deposit")

    # --- skrivning: alt oprettes som KLADDE ---

    def create_purchase(self, date, account, amount, description,
                        vat_code="NONE", file_guid=None, region="DK",
                        deposit_account=55000, external_ref=None):
        """Kontantkøb bogført mod en bankkonto.

        vat_code="NONE" undertrykker moms. Sender du None eller "", indsætter
        Dinero kontoens standardmoms — se references/dinero-api.md.
        """
        body = {
            "PurchaseType": "cash",
            "DepositAccountNumber": deposit_account,
            "RegionKey": region,
            "VoucherDate": date,
            "FileGuid": file_guid,
            "ExternalReference": external_ref,
            "Lines": [{
                "AccountNumber": account,
                "Description": description[:120],
                "Amount": amount,
                "VatCode": vat_code,
            }],
        }
        return self.call("POST", "/v1.2/{org}/vouchers/purchase", body)

    def create_manual(self, date, lines, file_guid=None, external_ref=None):
        """Manuelt bilag. Hver linje: AccountNumber, BalancingAccountNumber,
        Amount, Description og evt. AccountVatCode."""
        body = {
            "VoucherDate": date,
            "FileGuid": file_guid,
            "ExternalReference": external_ref,
            "Lines": lines,
        }
        return self.call("POST", "/v1/{org}/vouchers/manuel", body)

    def verify(self, kind, guid):
        """Læs et bilag tilbage. Gør ALTID dette efter skrivning."""
        return self.call("GET", f"/v1/{{org}}/vouchers/{kind}/{guid}")

    def book(self, kind, guid):
        """Bogfør — kun efter brugerens eksplicitte godkendelse."""
        status, voucher = self.verify(kind, guid)
        if status != 200:
            return status, voucher
        stamp = voucher.get("Timestamp") or voucher.get("TimeStamp")
        return self.call(
            "POST", f"/v1/{{org}}/vouchers/{kind}/{guid}/book", {"Timestamp": stamp}
        )

    def delete(self, kind, guid):
        """Sletning kræver Timestamp i request-body."""
        status, voucher = self.verify(kind, guid)
        if status != 200:
            return status, voucher
        stamp = voucher.get("Timestamp") or voucher.get("TimeStamp")
        return self.call("DELETE", f"/v1/{{org}}/vouchers/{kind}/{guid}",
                         {"Timestamp": stamp})


if __name__ == "__main__":
    d = Dinero()
    print(d.call("GET", "/v1/organizations"))
