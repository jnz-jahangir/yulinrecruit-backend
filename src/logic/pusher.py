import httpx
from collections import deque
from typing import Dict, Deque, Optional
import time
import random
from .wbhparser import parse_msg, MsgHistory
import json

from .. import utils
from .. import secret

msg_history = MsgHistory()

class Pusher:
    THROTTLE_TIME_S = 20*60
    THROTTLE_N = 5

    def __init__(self) -> None:
        self.chan_history: Dict[str, Deque[float]] = {}

    async def push_message(self, msg: str, chan: Optional[str]) -> None:
        print('push message', chan)
        print(msg)
        if (not secret.FEISHU_WEBHOOK_ADDR) and (not secret.QQBOT_WEBHOOK_ADDR):
            return
        if chan:
            if 'ERROR' in msg:
                hist = self.chan_history.get(chan, None)
                if hist is None:
                    hist = deque()
                    self.chan_history[chan] = hist

                if len(hist) >= self.THROTTLE_N:
                    if time.time() - hist[0] < self.THROTTLE_TIME_S:
                        print(f'push throttled ({chan}), time bound = {time.time()-hist[0]}')
                        return
                    hist.popleft()

                hist.append(time.time())
        if "PUSH" in msg:
            time.sleep(random.random())
            if await msg_history.is_msg_in_cache(msg):
                print("Message in cache, skip")
                return
            else:
                await msg_history.set_msg_history(msg)
                msg = parse_msg(msg)

        if secret.FEISHU_WEBHOOK_ADDR:
            async with httpx.AsyncClient(http2=True) as client:
                try:
                    await client.post(secret.FEISHU_WEBHOOK_ADDR, json={
                        'msg_type': 'text',
                        'content': {
                            'text': str(msg),
                        },
                    })
                except Exception as e:
                    print('PUSH FEISHU MESSAGE FAILED', utils.get_traceback(e))
                    pass
        
        if secret.QQBOT_WEBHOOK_ADDR:
            async with httpx.AsyncClient(http2=True) as client:
                try:
                    json_str = msg.replace("[PUSH]", "")
                    data = json.loads(json_str)
                    if ("ERROR" not in msg) and ("WRITEUP" not in msg) and ("POLICE" not in msg) and ("FEEDBACK" not in msg):
                        await client.post(secret.QQBOT_WEBHOOK_ADDR, json={
                            'token': 'jnz_yulinsec_aJ5oS9bR',
                            'text': str(msg),
                            'qq': data['qq'],
                        })
                except Exception as e:
                    print('PUSH QQ MESSAGE FAILED', utils.get_traceback(e))
                    pass