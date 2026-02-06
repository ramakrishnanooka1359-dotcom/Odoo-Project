import requests

class OdooRPC:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = self.authenticate()

    def authenticate(self):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [self.db, self.username, self.password, {}]
            },
            "id": 1
        }

        response = requests.post(
            f"{self.url}/jsonrpc",
            json=payload
        ).json()

        print("🔍 AUTH RESPONSE FROM ODOO:")
        print(response)

        if not response.get("result"):
            raise Exception("❌ Odoo login failed")

        return response["result"]

    def call(self, model, method, args, kwargs=None):
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    method,
                    args,
                    kwargs or {}
                ]
            },
            "id": 2
        }
        response = requests.post(f"{self.url}/jsonrpc", json=payload).json()
        if "error" in response:
            raise Exception(response["error"])
        return response["result"]
