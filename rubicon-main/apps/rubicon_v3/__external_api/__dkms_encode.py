from dkmsclient.dkms_client import DKMSClient
from dkmsclient.dkms_client_configuration import DKMSClientConfigurationBuilder, ServiceRunningOn
from dkmsclient import dkms_constants
import sys
import base64
import json
import tempfile
sys.path.append("/www/alpha")
from alpha.settings import VITE_COUNTRY
from apps.rubicon_v3.__external_api.__apiRequest import apiHandler
import os

class DKMS_Encoder:
    def __init__(self, channel=None):
        self.country = VITE_COUNTRY
        self.apiRequester = apiHandler(self.country, channel)
        self.opType = self.apiRequester.opType
        #self.current_path = '/www/alpha/apps/rubicon_v3/__external_api'
        self.current_path = os.path.dirname(__file__)
        self.encoded_private_key = ""
        self.credential_path = ""
        self.encoded_private_key = ""
        self.server_url = ""
        if self.opType.upper() in ["DEV", "STG"]:
            self.server_url = "https://stg.bdcdkms.com/v1"
            if self.country == "KR":
                self.credential_path = f"{self.current_path}/rubicon-kr-stg@2I5-dkms.com.json"
                self.encoded_private_key = os.getenv("DKMS_PRIVATE_KEY_KR_STG") ## base64 encoded private key
            elif self.country == "UK": ## UK Only for VITE_COUNTRY. ELSE, GB
                self.credential_path = f"{self.current_path}/rubicon-uk-stg@2I5-dkms.com.json"
                self.encoded_private_key = os.getenv("DKMS_PRIVATE_KEY_GB_STG") ## base64 encoded private key
        elif self.opType.upper() in ["PROD", "PRD"]:
            self.server_url = "https://global.sec-dkms.com/v1"
            if self.country == "KR":
                self.credential_path = f"{self.current_path}/rubicon-kr-prd@2I5-dkms.com.json"
                self.encoded_private_key = os.getenv("DKMS_PRIVATE_KEY_KR_PRD") ## base64 encoded private key
            elif self.country == "UK": ## UK Only for VITE_COUNTRY. ELSE, GB
                self.credential_path = f"{self.current_path}/rubicon-uk-prd@2I5-dkms.com.json"
                self.encoded_private_key = os.getenv("DKMS_PRIVATE_KEY_GB_PRD") ## base64 encoded private key
        try:
            private_key_64 = base64.b64decode(self.encoded_private_key).decode("utf-8").replace("\\n","\n")
            with open(self.credential_path, 'r') as f:
                credential = json.load(f)
            credential['privateKey'] = private_key_64
            temp_cred_path = ""
            with tempfile.NamedTemporaryFile('w', delete=False, suffix=".json") as temp_file:
                json.dump(credential, temp_file)
                temp_cred_path = temp_file.name
            self.conf = (DKMSClientConfigurationBuilder().server_url([f"{self.server_url}"]).service_running_on(ServiceRunningOn.AZURE).cred_path(temp_cred_path).build())
            self.client = DKMSClient(self.conf)
        except Exception as e:
            self.client = None
    
    def isEncrypted(self, encrypted_value):
        return self.client.is_encrypted(encrypted_value)

    def getEncryptedValue(self, value):
        encrypted_value = self.client.encrypt(value, '2I5:rubicon_chat_history_dkms', dkms_constants.PII_TAG_SAMSUNG_ACCOUNT_GUID)
        if self.client.is_encrypted(encrypted_value):
            return encrypted_value
        else:
            raise ValueError("DKMS encryption failed. The value is not encrypted.")
        
    def getDecryptedValue(self, value):
        decrypted_value = self.client.decrypt(value)
        if decrypted_value is None:
            raise ValueError("DKMS decryption failed. The value is None.")
        return decrypted_value

if __name__ == '__main__':
    client = DKMS_Encoder()
    encrypted_value = client.getEncryptedValue("wqptk45plj") #wqptk45plj
    print(encrypted_value)
    decrypted_value = client.getDecryptedValue(encrypted_value)
    print(decrypted_value)