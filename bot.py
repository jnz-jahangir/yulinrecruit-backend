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

groups = [708436450, 392686341, 953428132]
welcome = '''
====YulinSec====
==🪐御梦而生，如鹿归林🦌==
🥳欢迎加入御林安全工作室
🤗我们将在九月初开放为期两个月的招新训练营
🪧群公告有招新相关要求
📄群文件有海量入门资料🎁
🥵群里更有热心❤️学长等你咨询
‍💻希望你能在这里从零开始成为一名大黑阔
💭群主空间有转发抽奖说说
🏫夏令营目前开放，欢迎零基础同学参与学习https://summer.yulinsec.cn/
🍃大风希音至，堪待后来人。
🍷儒门有斗酒，清浊问使君。
'''

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

def user_in_member(user_id, group_id):
    url = f"{base_url}/get_group_member_list"
    params = {
        "group_id": group_id
    }
    res = requests.get(url=url, params=params)
    data = json.loads(res.text)['data']
    member = []
    for user in data:
        if user == user_id:
            return True
        member.append(user['user_id'])
    print(member)
    return False

def get_rank():
    utils.fix_zmq_asyncio_windows()

    worker = Worker("worker-test")
    asyncio.run(worker._before_run())

    b = worker.game.boards["score_all"]

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
        print(user_in_member(user_id=data['qq'], group_id=708436450))
        send_group_msg(708436450, data['text'])
    else: 
        print("illegal token:", data['token'])

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)