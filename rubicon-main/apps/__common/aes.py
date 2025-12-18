import base64 
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad,unpad
from alpha.settings import VITE_ENCRYPTION_KEY

import string
import random


def encrypt(raw):
    raw = pad(raw.encode(),16)
    cipher = AES.new(VITE_ENCRYPTION_KEY.encode('utf-8'), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(raw))

def decrypt(enc):
    enc = base64.b64decode(enc)
    cipher = AES.new(VITE_ENCRYPTION_KEY.encode('utf-8'), AES.MODE_ECB)
    return str(unpad(cipher.decrypt(enc),16), 'utf-8')

def salt_generator(size=24, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

