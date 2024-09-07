import json
from .. import secret

import os

class MsgHistory:
    def __init__(self):
        self.flag_path = secret.SYBIL_LOG_PATH / f"flag.txt"
        self.first_blood_path = secret.SYBIL_LOG_PATH / f"first_blood.txt"
        self.newbie_first_blood_path = secret.SYBIL_LOG_PATH / f"newbie_first_blood.txt"

        if not os.path.exists(self.flag_path):
            with open(self.flag_path, "w") as file:
                file.write('')
        if not os.path.exists(self.first_blood_path):
            with open(self.newbie_first_blood_path, "w") as file:
                file.write('')
        if not os.path.exists(self.newbie_first_blood_path):
            with open(self.newbie_first_blood_path, "w") as file:
                file.write('')

    async def set_msg_history(self, msg):
        if "first_blood" in msg:
            if "新生" in msg:
                with open(self.newbie_first_blood_path, "w") as file:
                    file.write(msg)
            else:
                with open(self.first_blood_path, "w") as file:
                    file.write(msg)
        else:
            with open(self.flag_path, "w") as file:
                file.write(msg)

    async def is_msg_in_cache(self, msg):
        if "first_blood" in msg:
            if "新生" in msg:
                with open(self.newbie_first_blood_path, "r") as file:
                    if file.read() == msg:
                        return True
            else:
                with open(self.first_blood_path, "r") as file:
                    if file.read() == msg:
                        return True
        else:
            with open(self.flag_path, "r") as file:
                if file.read() == msg:
                    return True

        return False


def parse_msg(msg):
    json_str = msg.replace("[PUSH]", "")
    data = json.loads(json_str)
    if data["type"] == "flag_first_blood":
        result = (
            f'🎋Flag一血更新！恭喜【{data["nickname"]}】🎋\n在“{data["board_name"]}”中\n“{data["challenge"]}”的'
            f'【{data["flag"]}】取得一血！'
        )
    elif data["type"] == "passed_flag":
        result = (
            f'🔥Flag更新！恭喜【{data["nickname"]}】🔥\n在“{data["challenge"]}”的'
            f'【{data["flag"]}】解出了Flag！'
        )
    elif data["type"] == "passed_challenge":
        result = f'🎉Challenge更新！恭喜【{data["nickname"]}】🎉\n解出了【{data["challenge"]}】！'
    elif data["type"] == "challenge_first_blood":
        result = f'❤️‍🔥Challenge一血更新！恭喜【{data["nickname"]}】❤️‍🔥\n在“{data["board_name"]}”中\n【{data["challenge"]}】取得一血！'
    return result
