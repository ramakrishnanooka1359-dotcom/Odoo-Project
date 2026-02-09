import requests

class OdooRPC:
    def __init__(self, url, db, username, api_key):
        self.url = url
        self.db = db
        self.username = username
        self.api_key = api_key
        self.uid = self.authenticate()

    def authenticate(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [
                    self.db,
                    self.username,
                    self.api_key,
                    {}
                ]
            },
            "id": 1
        }

        response = requests.post(f"{self.url}/jsonrpc", json=payload).json()

        if not response.get("result"):
            raise Exception("❌ Authentication failed")

        print("✅ Authenticated. UID:", response["result"])
        return response["result"]

    def call(self, model, method, args=None, kwargs=None):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    self.uid,
                    self.api_key,
                    model,
                    method,
                    args or [],
                    kwargs or {}
                ]
            },
            "id": 2
        }

        response = requests.post(f"{self.url}/jsonrpc", json=payload).json()

        if "error" in response:
            raise Exception(response["error"])

        return response["result"]
