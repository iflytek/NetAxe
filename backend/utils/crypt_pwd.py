# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      crypt_pwd
   Description:
   Author:          lijiamin
   date：           2019/5/24
-------------------------------------------------
   Change Activity:
                    2019/5/24:
-------------------------------------------------
"""
import base64, re
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5


class CryptPwd:
    """
    用于加密和解密密码,
    """

    def __init__(self):
        self.key = "1daff23r32sfa#$%"
        self.mode = AES.MODE_ECB

    @staticmethod
    def add_to_16(value):
        """
        要加密的数据和使用的key的字节数必须是16位，这里不足16位的用'\n'填充，方便后面解密使用rstrip
        :param value: 要加长的内容
        :return: bytes类型的数据
        :type value: str
        :rtype: bytes
        """
        while len(value) % 16 != 0:
            value += '\n'
        return value.encode('utf-8')

    def encrypt_pwd(self, pwd):
        """
        对密码进行加密
        :param pwd: 密码
        :return: 加密后的密码
        :type pwd: str
        :rtype: str
        """
        aes = AES.new(self.add_to_16(self.key), self.mode)
        encrypt_aes = aes.encrypt(self.add_to_16(pwd))
        encrypted_pwd = str(base64.b64encode(encrypt_aes), encoding='utf-8')
        return encrypted_pwd

    def decrypt_pwd(self, encrypted_pwd):
        """
        对密码进行解密
        :param encrypted_pwd: 加密后的密码，必须是使用同一种方式加密的密码
        :return: 解密后的密码，字符串类型
        :type encrypted_pwd: str
        :rtype: str
        """
        aes = AES.new(self.add_to_16(self.key), self.mode)
        decrypt_base64 = base64.b64decode(encrypted_pwd.encode('utf-8'))
        decrypt_pwd = str(aes.decrypt(decrypt_base64), encoding='utf-8')
        return decrypt_pwd.rstrip()

    @staticmethod
    def de_js_encrypt(en_pwd):
        """
        解密通过jsencrypt.js文件加密的密码
        :param en_pwd:
        :return:
        """

        key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCpWjOC7g8/3U2X
4qAbs/TRkfAYO+R+PHiG0xNUHAziyjPqgL5TFE48hjuwiAQL1Y7qeO7q8sl0d6nC
bqkFYx8z7DUIWN83o7Kmo0PgvilN1NZ2WGTAwwEvZraAPFx6vILU+OzAKOKpa7Wy
pe5g6QMOgeCiuT1BmQe1UvSke+6lhDRUXKelAV05zyCev+E9RRWTVyn1ZJ5EVAZe
Gp8j/EFppnnIEws0roQBl6n7VeyPa7/c0ja2XCWOVlkAB6oS7aE57IYoFoHlJr12
68xNHzeUT6SiDNlt2L89d4YCm46iwhNedl4u8UqukiItvOr5POEsAcLs5ut7ZPOa
V2KcFCdBAgMBAAECggEAU6AxE5ROf3DeYgQMn+FrIRl5f94DZLqjoaAVSVFYo5zJ
qiDM2uWKBKUcUH250cYw/mOdRvOAuzxj3ZkbaYea3t7jCS4pe6YgD91LJW2Bo+dX
x7S6e91PdoK31/b2i70Ote/9qJ4H3zVK0d7SKZSmZ8GGlZP3Ra81eTpvh9GS9LPX
23lLRG7ozY6e94yFR8hCRYyUES6l/hPjhb22bOcQEd51tCUskXlCcpzNCV31nLOD
eE8VnzLq1Yn9/2tUkE18yBdHU9VGNBA9grK0L1lzflMtfP1HQ4O1vnRHWoKGA0ql
zeJ7VlNNexmT/kNRpaDs2a+8yW07qxNfcF4N8mSlKQKBgQDbxidhjh9NG5EmmMJs
Lqms2olkPmEUh7fDrSQs9b/Dn0ZgdNXDyvKFFYFvTcXju9Ol1gI25Tg0Y0eA9922
Jz31ZoOj6jSHafxO5+R6y1Q7wZmvzCfOSOgcp1Rd4tTrdjIh2FHFjG37C5pjoZSn
4GYp8p4V/2yROzYDqSqQjrJXxwKBgQDFRGTXfJxgnJ//5EOBlbzy/8k4Ch2yXAIW
eXPnygu5KNKdaPyAhZSqVAVl/p8m0WblnOsBnkmQb1G1Clo9HJKhi6Uig4Wpl+zD
z4+T8GaLjxIRYBXVZN1zN48e9R+YSmlMwndcttZ/4zVj5O86X0T3+Yv/4kbIfTp7
iHWwjj1YtwKBgQCN+JO4EXdm+EfsBwKRoBM79nCKsUFFYeb0IQUdhiM628k6xj7R
HGlOT3Yt0K/lTZCLsJP9olWMghXO2k//O5pqzK59VO5aC71Ru7t9F5xyfb4qMlgE
ilRnLjDx9XZWJSR9eKBaXT0uz3AMrHS7fdqBfplg3H/l0boy4zT77TKIQQKBgQC0
Kg3rnLx5pDKhFAnvfSGP0bsl+l86+btSaWRJSwe/+R+6chtDCj1H/urbR1x1qIRQ
qysbVESdrH20Whsme0UUU6TjS7m0tbOg9p2MIOCXD3kR826dcbyrMQ/+1yMfBL79
QxKe08I+FPY7IOi4qDAmRnztm+zHyU+zaWMLeC1hKwJ/dwc6UxKKTQwKbClduZTZ
bpEsyS7xvAWuaQjTfD4r0dcudE90h/gx+s1coAVxeguaIEIsGFCRsF1Y2q/Uvyrm
ndpQtGa+vWEiqQh9DgQ260LPvVjVRpGf8fp54q06wUf9i5cpK6SK/mUOno674cXE
ufzZkfqqEAEdPkvaN3k3gg==
-----END PRIVATE KEY-----
"""
        rsakey = RSA.importKey(key)  # 导入私钥
        cipher = PKCS1_v1_5.new(rsakey)  # 生成对象
        missing_padding = len(en_pwd) % 4
        if missing_padding:
            en_pwd += '=' * (4 - missing_padding)
        text = cipher.decrypt(base64.b64decode(en_pwd.encode('utf-8')), "ERROR")  # 将密文解密成明文，返回的是一个bytes类型数据，需要自己转换成str

        return text.decode('utf-8')

def checkio(passwd):
    """ 密码必须同时包含大写字母、小写字母、数字并且长度大于10位"""
    return True if re.search("^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).*$", passwd) and len(passwd) >= 10 else False