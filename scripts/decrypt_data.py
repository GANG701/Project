import pandas as pd
import mysql.connector
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64
import json
import os

# ------------------------------
# 1. RSA 키 준비 (개인 키 사용)
# ------------------------------
private_key_path = "../keys/rsa_private.pem"

if not os.path.exists(private_key_path):
    print("[오류] RSA 개인 키 파일이 존재하지 않습니다. 복호화는 불가능합니다.")
    print("개인 키 파일('rsa_private.pem')을 안전한 경로에 보관했는지 확인하세요.")
    exit()

try:
    with open(private_key_path, "rb") as f:
        private_key = f.read()
    print("[INFO] RSA 개인 키를 불러왔습니다. 복호화를 시작합니다.")
except IOError as e:
    print(f"오류: 개인 키 파일을 불러오는 데 실패했습니다: {e}")
    exit()

# ------------------------------
# 2. AES 복호화 함수
# ------------------------------
def decrypt_aes(enc_data, aes_key):
    """
    AES-256 (EAX 모드)로 암호화된 데이터를 복호화
    """
    cipher = AES.new(aes_key, AES.MODE_EAX, nonce=enc_data['nonce'])
    data_bytes = cipher.decrypt_and_verify(enc_data['ciphertext'], enc_data['tag'])
    return json.loads(data_bytes.decode('utf-8'))

# ------------------------------
# 3. RSA로 AES 키 복호화
# ------------------------------
def decrypt_aes_key(enc_aes_key, rsa_priv_key):
    """
    암호화된 AES 키를 RSA 개인 키로 복호화
    """
    rsa_cipher = PKCS1_OAEP.new(RSA.import_key(rsa_priv_key))
    aes_key = rsa_cipher.decrypt(enc_aes_key)
    return aes_key

# ------------------------------
# 4. DB 연결 및 데이터 조회
# ------------------------------
print("\n[INFO] DB에서 데이터 조회 및 복호화 시작...")
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='password',
        database='sea_system'
    )
    cur = conn.cursor()
except mysql.connector.Error as err:
    print(f"MySQL 연결 오류: {err}")
    exit()

# 모든 컬럼을 조회
cur.execute('SELECT name, gender, job, encrypted_data, encrypted_aes_key FROM passengers')
rows = cur.fetchall()
conn.close()

# ------------------------------
# 5. 데이터 복호화 예제
# ------------------------------
for row in rows:
    db_name, db_gender, db_job, enc_data_json, enc_aes_key_b64 = row
    try:
        # DB에서 가져온 데이터 디코딩
        enc_data_json_str = enc_data_json.decode('utf-8')
        enc_aes_key_b64_str = enc_aes_key_b64.decode('utf-8')
        enc_data_decoded = json.loads(enc_data_json_str)
        enc_data = {k: base64.b64decode(v) for k, v in enc_data_decoded.items()}
        enc_aes_key = base64.b64decode(enc_aes_key_b64_str)
        
        # AES 키 복호화
        aes_key = decrypt_aes_key(enc_aes_key, private_key)
        
        # 민감 데이터 복호화
        decrypted_sensitive_data = decrypt_aes(enc_data, aes_key)
        
        # 평문 데이터와 복호화된 민감 데이터를 결합
        full_data = {
            'name': db_name,
            'gender': db_gender,
            'job': db_job,
            **decrypted_sensitive_data
        }
        print(f"DB 데이터 복호화 성공: {full_data}")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"오류: DB 복호화 실패. 데이터가 손상되었거나 키가 올바르지 않습니다. ({e})")
