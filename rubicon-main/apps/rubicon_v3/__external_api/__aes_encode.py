import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from datetime import datetime
import random
import string
import urllib.parse
import os

class AES_Encoder:

    def generate_random_id(self, length=8):
        """8자리 랜덤 문자열 생성 (알파벳 + 숫자)"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def get_current_datetime(self):
        """현재 날짜시간을 14자리 문자열로 반환 (YYYYMMDDHHmmss)"""
        return datetime.now().strftime('%Y%m%d%H%M%S')

    def encrypt_aes_cbc(self, text, secret_key, iv=None):
        # 키 사이즈가 16바이트(128비트)가 되도록 조정
        key_bytes = secret_key.encode('utf-8')
        if len(key_bytes) > 16:
            key_bytes = key_bytes[:16]
        elif len(key_bytes) < 16:
            key_bytes = key_bytes.ljust(16, b'\0')
        
        # IV가 없으면 0으로 채움 (웹사이트와 동일하게)
        if iv is None:
            iv = b'\x00' * 16
        else:
            # Hex 문자열에서 바이트로 변환
            iv = binascii.unhexlify(iv)
        
        # AES-CBC 암호화
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        padded_data = pad(text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        # 암호화된 데이터만 Base64 인코딩 (IV 제외)
        result_base64 = base64.b64encode(encrypted).decode('utf-8')
        result_hex = binascii.hexlify(encrypted).decode('utf-8').upper()
        
        return {
            'base64': result_base64,
            'hex': result_hex
        }

    def doEncoding(self, random_id):
        # 랜덤 ID + 날짜 방식 테스트
        secret_key = os.environ.get("AES_SECRET_KEY")
        random_id = random_id
        current_datetime = self.get_current_datetime()
        combined_text = random_id + current_datetime
        
        #print(f"\n새 랜덤 ID + 날짜 문자열: {combined_text}")
        result2 = self.encrypt_aes_cbc(combined_text, secret_key)
        #print(f"암호화 결과 (Base64): {result2['base64']}")
        
        # URL 인코딩
        url_encoded_base64_2 = urllib.parse.quote(result2['base64'])
        #print(f"암호화 결과 (URL 인코딩된 Base64): {url_encoded_base64_2}")
        return url_encoded_base64_2

if __name__ == "__main__":
    encoder = AES_Encoder()
    result = encoder.doEncoding('YGW9OH8H')
    print(result)