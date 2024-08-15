#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Time    : 2023/7/18 1:35
# @Author  : Suzuran
# @FileName: AES_module.py
# @Software: PyCharm
# AES-demo

import base58
from Crypto.Cipher import AES

from .. import secret


def add_to_16(raw_text: str) -> bytes:
    """
    将字符串补足为16的倍数
    :param raw_text: 原始文本
    :return: 补足后的字节
    """
    while len(raw_text) % 16 != 0:
        raw_text += '\0'
    return str.encode(raw_text)  # 返回bytes


def encrypt_oracle(text: str) -> str:
    """
    AES加密
    :param text: 待加密文本
    :return: 加密后文本
    """
    key = secret.AES_KEY
    aes = AES.new(add_to_16(key), AES.MODE_ECB)  # 初始化加密器
    encrypt_aes = aes.encrypt(add_to_16(text))
    encrypted_text = str(
        base58.b58encode(encrypt_aes), encoding='utf-8'
    )  # 执行加密并转码返回bytes
    return encrypted_text


def decrypt_oracle(enc_text: str) -> str:
    """
    AES解密
    :param enc_text: 加密文本
    :return: 解密后文本
    """
    key = secret.AES_KEY
    aes = AES.new(add_to_16(key), AES.MODE_ECB)  # 初始化加密器
    base58_decrypted = base58.b58decode(enc_text.encode(encoding='utf-8'))
    decrypted_text = str(aes.decrypt(base58_decrypted), encoding='utf-8').replace(
        '\0', ''
    )
    return decrypted_text
