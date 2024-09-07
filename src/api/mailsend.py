import time
from datetime import datetime
import json
from re import match
from .. import secret
from .AES_module import encrypt_oracle, decrypt_oracle
import base64


class ip_user_mail_checker:
    def __init__(self) -> object:
        self.ip_list = []
        self.ip_time = []
        self.mail_list = []
        self.mail_time = []

    def check_ip(self, ip):
        if len(self.ip_list) > 100:
            self.ip_list.pop(0)
            self.ip_time.pop(0)
        if ip in self.ip_list:
            if time.time() - self.ip_time[self.ip_list.index(ip)] < 60:
                return False
            else:
                self.ip_time[self.ip_list.index(ip)] = time.time()
                return True
        else:
            self.ip_list.append(ip)
            self.ip_time.append(time.time())
            return True

    def check_mail(self, mail):
        if len(self.mail_list) > 100:
            self.mail_list.pop(0)
            self.mail_time.pop(0)

        if mail in self.mail_list:
            if time.time() - self.mail_time[self.mail_list.index(mail)] < 60:
                return False
            else:
                self.mail_time[self.mail_list.index(mail)] = time.time()
                return True
        else:
            self.mail_list.append(mail)
            self.mail_time.append(time.time())
            return True


ipChecker = ip_user_mail_checker()


def check_ip(ip: str) -> str:
    # 如果没有IP_Checker实例，则创建一个
    # 检查IP地址是否合法,使用正则表达式
    if not match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
        return "IP地址不合法"
    # 检查IP地址是否在黑名单中
    if ip in secret.IP_BLACK_LIST:
        return "IP地址在黑名单中"

    # 检查IP地址是否在IP_Checker实例中
    if ipChecker.check_ip(ip):
        return "IP地址认证成功"
    else:
        # 检查IP地址是否在白名单中
        if ip in secret.IP_WHITE_LIST:
            return "IP地址在白名单中"
        else:
            return "同IP访问过于频繁"


def check_mail(mail: str) -> str:
    # 检查邮箱是否合法,使用正则表达式
    if not match(secret.MAIL_PATTERN, mail):
        return "邮箱不合法"
    # 检查邮箱是否在黑名单中
    if mail in secret.MAIL_BLACK_LIST:
        return "邮箱在黑名单中"

    # 检查邮箱是否在IP_Checker实例中
    if ipChecker.check_mail(mail):
        return "邮箱认证成功"
    else:
        # 检查邮箱是否在白名单中
        if mail in secret.MAIL_WHITE_LIST:
            return "邮箱在白名单中"
        else:
            return "同邮箱访问过于频繁"


def gen_email_link(email: str) -> str:
    """
    生成加密的邮箱连接
    :param email: 邮箱
    :return: 加密后的链接
    """
    data = json.dumps({"email": email, "time": time.time()})
    authID = encrypt_oracle(data)

    return authID


def decode_mail_link(authID: str) -> dict:
    """
    对AuthID进行解码，得到邮箱和注册时间
    :param authID: 加密过的邮箱和时间戳
    :return: 字典格式数据
    {
        "email":str(邮箱)
        "time_sec":int(相差分钟数)
    }
    """
    data = json.loads(decrypt_oracle(authID))
    time1 = datetime.strptime(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data["time"])),
        "%Y-%m-%d %H:%M:%S",
    )
    time2 = datetime.strptime(
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S"
    )
    
    uestc_pattern = r'^\d{13}@std.uestc.edu.cn$'
    if match(uestc_pattern, data['email']):
        if data["email"].lower()[:4] in ("2023", "2024"):
            group = "newbie"
        else:
            group = "oldbie"
    else:
        group = "other"

    return {
        "email": data["email"],
        "time_sec": (time2 - time1).seconds / 60,
        "user_group": group,
    }
