# pip install fastapi uvicorn "mysql-connector-python" "python-dotenv"
# pip install "python-multipart" # if you need to handle file uploads
import uvicorn
import mysql.connector
from fastapi import FastAPI, HTTPException
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64
import json
import os
import sys

# RSA 개인 키 파일 경로 (KMS 역할을 시뮬레이션하기 위해 사용)
PRIVATE_KEY_PATH = "rsa_private.pem"

# ------------------------------
# 1. RSA 개인 키 로드 (KMS 역할 시뮬레이션)
# ------------------------------
# 실제 운영 환경에서는 개인 키가 서버에 직접 보관되지 않고,
# 별도의 KMS 서비스에 안전하게 저장
# 로컬 파일에서 키를 읽어오는 것으로 KMS의 역할을 함.
if not os.path.exists(PRIVATE_KEY_PATH):
    print("[오류] RSA 개인 키 파일이 존재하지 않습니다. 복호화는 불가능합니다.")
    print(f"개인 키 파일('{PRIVATE_KEY_PATH}')을 안전한 경로에 보관했는지 확인하세요.")
    sys.exit()

try:
    with open(PRIVATE_KEY_PATH, "rb") as f:
        PRIVATE_KEY_IN_KMS = f.read() # 키를 마치 KMS에 저장된 것처럼 변수에 할당
    print("[INFO] RSA 개인 키를 성공적으로 불러왔습니다.")
except IOError as e:
    print(f"오류: 개인 키 파일을 불러오는 데 실패했습니다: {e}")
    sys.exit()

# ------------------------------
# 2. FastAPI 애플리케이션 초기화
# ------------------------------
app = FastAPI()

# ------------------------------
# 3. 데이터베이스 연결 함수
# ------------------------------
def get_db_connection():
    """MySQL 데이터베이스 연결을 생성하고 반환합니다."""
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='password',
            database='sea_system'
        )
    except mysql.connector.Error as err:
        print(f"MySQL 연결 오류: {err}")
        return None

# ------------------------------
# 4. 복호화 유틸리티 함수
# ------------------------------
def decrypt_aes(enc_data, aes_key):
    """
    AES-256 (EAX Mode)로 암호화된 데이터를 복호화
    """
    cipher = AES.new(aes_key, AES.MODE_EAX, nonce=enc_data['nonce'])
    data_bytes = cipher.decrypt_and_verify(enc_data['ciphertext'], enc_data['tag'])
    return json.loads(data_bytes.decode('utf-8'))

def decrypt_aes_key_with_kms(enc_aes_key):
    """
    (KMS API 호출을 시뮬레이션)
    암호화된 AES 키를 KMS에 저장된 개인 키로 복호화
    """
    # 이 함수는 실제로는 네트워크를 통해 KMS에 복호화를 요청
    # 여기서는 로컬 변수에 저장된 키를 사용해 시뮬레이션
    rsa_cipher = PKCS1_OAEP.new(RSA.import_key(PRIVATE_KEY_IN_KMS))
    aes_key = rsa_cipher.decrypt(enc_aes_key)
    return aes_key

# ------------------------------
# 5. API 엔드포인트: 승객 정보 조회
# ------------------------------
@app.get("/passenger/{passenger_id}")
async def get_passenger_data(passenger_id: int):
    """
    DB에서 특정 승객의 정보를 조회하고 복호화하여 반환
    """
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="데이터베이스 연결 실패")

    cur = conn.cursor()
    
    # DB에서 암호화된 데이터 및 평문 데이터를 조회
    query = """
    SELECT name, gender, job, encrypted_data, encrypted_aes_key
    FROM passengers
    WHERE id = %s
    """
    cur.execute(query, (passenger_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="승객을 찾을 수 없습니다.")

    # 튜플에서 데이터 추출
    db_name, db_gender, db_job, enc_data_json, enc_aes_key_b64 = row
    
    try:
        # 암호화된 데이터 디코딩
        enc_data_json_str = enc_data_json.decode('utf-8')
        enc_aes_key_b64_str = enc_aes_key_b64.decode('utf-8')
        enc_data_decoded = json.loads(enc_data_json_str)
        enc_data = {k: base64.b64decode(v) for k, v in enc_data_decoded.items()}
        enc_aes_key = base64.b64decode(enc_aes_key_b64_str)
        
        # AES 키 복호화 (KMS 함수 사용)
        aes_key = decrypt_aes_key_with_kms(enc_aes_key)
        
        # 민감 데이터 복호화
        decrypted_sensitive_data = decrypt_aes(enc_data, aes_key)
        
        # 평문 데이터와 복호화된 민감 데이터를 결합
        full_data = {
            'id': passenger_id,
            'name': db_name,
            'gender': db_gender,
            'job': db_job,
            **decrypted_sensitive_data
        }
        return full_data
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"복호화 오류: {e}")
        raise HTTPException(status_code=500, detail="데이터 복호화 중 오류가 발생했습니다.")

if __name__ == "__main__":
    # uvicorn을 사용하여 서버 실행
    uvicorn.run(app, host="127.0.0.1", port=8000)
