import json
import time

class AccountsController():
    def __init__(self):
        self.db_name = "tokens.json"

    def get_data(self):
        with open(self.db_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data["data"]

    def get_active_token(self):
        self.check_accounts()
        data = self.get_data()
        for acc in data:
            if acc["is_active"]:
                return acc["token"]
        return None

    def check_accounts(self):
        # тут проходимся и проверяем локет а потом активность если неактив то чекаем время, если время меньше чем щас то ставим его активным
        data = self.get_data()
        new_data = []
        for acc in data:
            if acc["is_active"] != True and acc["is_locked"] != True and acc["recovery_time"] < int(time.time()):
                acc["is_active"] = True
            new_data.append(acc)
        with open(self.db_name, 'w', encoding='utf-8') as f:
            json.dump({"data": new_data}, f, ensure_ascii=False, indent=4)
        return None
    
    def update_account(self, token, recovery_time, is_active, is_locked):
        data = self.get_data()
        new_data = []
        for acc in data:
            if acc["token"] == token:
                acc["recovery_time"] = recovery_time
                acc["is_active"] = is_active
                acc["is_locked"] = is_locked
            new_data.append(acc)
        with open(self.db_name, 'w', encoding='utf-8') as f:
            json.dump({"data": new_data}, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    AccountsController().check_accounts()
    # chatbot = ChatBot()
    # asyncio.run(chatbot.run_chat())