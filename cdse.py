"""Copernicus Data Space (CDSE) login and endpoints, shared by the Sentinel-2 scripts.

Credentials: env vars CDSE_CLIENT_ID / CDSE_CLIENT_SECRET, or secret.txt next to this file
with the lines "client ID: ..." and "client secret: ...". Never print or publish them.
"""
import os
import time

import requests

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
STAC = "https://stac.dataspace.copernicus.eu/v1/search"
PROCESS = "https://sh.dataspace.copernicus.eu/api/v1/process"
CLOUD_CLASSES = [3, 8, 9, 10, 11]  # Sentinel-2 SCL: shadow, cloud med/high, cirrus, snow


class Auth:
    def __init__(self):
        self.cid = os.environ.get("CDSE_CLIENT_ID")
        self.secret = os.environ.get("CDSE_CLIENT_SECRET")
        if not (self.cid and self.secret):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret.txt")
            vals = {}
            for line in open(path):
                if ":" in line:
                    k, v = line.split(":", 1)
                    vals[k.strip().lower()] = v.strip()
            self.cid, self.secret = vals["client id"], vals["client secret"]
        self.tok, self.t = None, 0

    def header(self):
        if not self.tok or time.time() - self.t > 480:
            r = requests.post(TOKEN_URL, data=dict(
                grant_type="client_credentials", client_id=self.cid,
                client_secret=self.secret), timeout=60)
            r.raise_for_status()
            self.tok, self.t = r.json()["access_token"], time.time()
        return {"Authorization": f"Bearer {self.tok}"}
