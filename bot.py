from flask import Flask, request
import requests

import asyncio
from pathlib import Path
import sys
import json
sys.path.append(str(Path(".").resolve()))

from src.logic.worker import Worker
from src.state import ScoreBoard, FirstBloodBoard
from src import utils

N_TOP = 10
N_THRESHOLD = 10

app = Flask(__name__)

token = 'jnz_yulinsec_aJ5oS9bR'
base_url = 'http://127.0.0.1:3000'

admin_id = 1047505798 # 运维QQ
user_group = 392686341 # 招新群
admin_group = 953428132 # 管理群
groups = [708436450, 392686341, 953428132] 

welcome = '''
====YulinSec====
==🪐御梦而生，如鹿归林🦌==
🥳欢迎加入御林安全工作室
🤗招新已正式开始https://recruit.yulinsec.cn/
🪧群公告有招新相关要求
📄群文件有海量入门资料🎁
🥵群里更有热心❤️学长等你咨询
‍💻希望你能在这里从零开始成为一名大黑阔
🍃大风希音至，堪待后来人。
🍷儒门有斗酒，清浊问使君。'''

def send_group_msg(group_id, message):
    url = f"{base_url}/send_group_msg"
    params = {
        "group_id": group_id,
        "message": message,
        "access_token": token
    }
    response = requests.get(url=url, params=params)

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")
        print(response.status_code, response.text)

def send_private_msg(user_id, message):
    url = f"{base_url}/send_private_msg"
    params = {
        "group_id": user_id,
        "message": message,
        "access_token": token
    }
    response = requests.get(url=url, params=params)

    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print("Failed to send message")
        print(response.status_code, response.text)

def set_group_ban(group_id, user_id, duration):
    url = f'{base_url}/set_group_ban'
    params = {
        "group_id": group_id,
        "user_id": user_id,
        "duration": duration,
        "access_token": token
    }
    response = requests.get(url=url, params=params)

    if response.status_code == 200:
        print("User ban success!")
    else:
        print("User ban fail!")
        print(response.status_code, response.text)

def user_in_group(user_id, group_id):
    url = f"{base_url}/get_group_member_list"
    params = {
        "group_id": group_id,
        "access_token": token
    }
    res = requests.get(url=url, params=params)
    print(res.text)
    data = json.loads(res.text)['data']
    member = []
    for user in data:
        # print(user, type(user), user_id, type(user_id))
        if str(user['user_id']) == str(user_id):
            return True
        member.append(user['user_id'])
    print(member)
    return False

def get_rank():
    utils.fix_zmq_asyncio_windows()

    worker = Worker("worker-test")
    asyncio.run(worker._before_run())

    b = worker.game.boards["score_newbie"]

    msg = "当前新生排行如下："

    i = 1
    rk = ['', '🥇', '🥈', '🥉', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
    for item in b.board:
        if i >= 11:
            break
        msg = msg+"\n"+"{} {} : {}".format(rk[i] ,item[0]._store.profile.nickname_or_null, item[1])
        i = i + 1
    
    return msg

def get_rank_all():
    utils.fix_zmq_asyncio_windows()

    worker = Worker("worker-test")
    asyncio.run(worker._before_run())

    b = worker.game.boards["score_all"]

    msg = "当前所有人排行如下："

    i = 1
    rk = ['', '🥇', '🥈', '🥉', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
    for item in b.board:
        if i >= 11:
            break
        msg = msg+"\n"+"{} {} : {}".format(rk[i] ,item[0]._store.profile.nickname_or_null, item[1])
        i = i + 1
    
    return msg

@app.route('/qqpost', methods=['POST'])
def receive_event():
    data = request.json
    print("Received event:", data)
    if 'message_type' in data and data['message_type'] == 'group' and data['group_id'] in groups:
        msg = data['raw_message']
        group_id = data['group_id']
        user_id = data['user_id']

        if msg[0] == '#':
            msg = msg[1:]
            if msg == "ping":
                send_group_msg(group_id, "pong!")
            if msg == "rank":
                send_group_msg(group_id, get_rank())
            if msg == "rank all":
                send_group_msg(group_id, get_rank_all())
        elif '通知：' in msg or '重要通知' in msg or '进群' in msg or '群号' in msg or '加群' in msg or '福利' in msg:
            set_group_ban(group_id=group_id, user_id=user_id, duration=86400)

    elif 'notice_type' in data and data['notice_type'] == 'group_increase' and data['group_id'] in groups:
        group_id = data['group_id']
        user_id = data['user_id']
        send_group_msg(group_id, f"[CQ:at,qq={user_id}]"+welcome)

    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received Webhook:", data)

    if 'token' in data and data['token'] == token:
        if data['type'] == 'PUSH':
            if user_in_group(user_id=data['qq'], group_id=user_group):
                name = data['nickname']
                data['text'] = data['text'].replace(f"【{name}】", f"【{name}】([CQ:at,qq={data['qq']}])")
            send_group_msg(user_group, data['text'])
        if data['type'] == 'NOTICE':
            send_group_msg(admin_group, data['text'])
        if data['type'] == 'ERROR':
            send_private_msg(admin_id, data['text'])
    else: 
        print("illegal token:", data['token'])

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
