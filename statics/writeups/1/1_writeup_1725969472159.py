import requests
import json
from playsound import playsound
import time

while True:
    res = requests.post('https://wx.uestc.edu.cn/power/oneCartoon/list', data={'roomCode': '3rad4hZtOezi70kt3crg0g=='})
    r = json.loads(res.text)
    print(r)
    sydl = float(r['data']['sydl'])
    syje = float(r['data']['syje'])
    print(f"{time.strftime('%H:%M:%S',time.localtime(time.time()))} 剩余{sydl}度")
    print(f"{time.strftime('%H:%M:%S',time.localtime(time.time()))} 剩余{syje}元")
    # if syje < 0.5:
    #     while True:
    #         playsound('xm2715.mp3')
    time.sleep(120)