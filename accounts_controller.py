import json

class AccountsController():
    def __init__(self):
        self.db_name = "tokens.json"

    def get_data(self):
        with open(self.db_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data["data"]

    def get_active_token(self):
        data = self.get_data()
        for acc in data:
            if acc["is_active"]:
                return acc["token"]
        return None
    
    def update_account(self, token, recovery_time, is_active, is_locked):
        data = self.get_data()
        for acc in data:
            if acc["token"] == token:
                acc["recovery_time"] = recovery_time
                acc["is_active"] = is_active
                acc["is_locked"] = is_locked
                break