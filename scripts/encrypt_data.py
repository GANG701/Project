import pandas as pd
import mysql.connector
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import base64
import json
import os

# ------------------------------
# 1. CSV 데이터 불러오기
# ------------------------------
csv_path = "../data/passenger_data.csv"
try:
    df = pd.read_csv(csv_path, encoding='utf-8')
    # 성별을 M/F로 변환
    df['gender'] = df['성별'].apply(lambda x: 'M' if x.strip().lower() == 'male' else 'F')
except FileNotFoundError:
    print(f"오류: '{csv_path}' 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    exit()

# ------------------------------
# 2. RSA 키 준비 (공개 키 사용)
# ------------------------------
public_key_path = "../keys/rsa_public.pem"

if not os.path.exists(public_key_path):
    print("[오류] RSA 공개 키 파일이 존재하지 않습니다.")
    print("데이터를 암호화하기 위해 'rsa_public.pem' 파일이 필요합니다.")
    exit()

try:
    with open(public_key_path, "rb") as f:
        public_key = f.read()
    print("[INFO] RSA 공개 키를 불러왔습니다. 암호화를 시작합니다.")
except IOError as e:
    print(f"오류: 공개 키 파일을 불러오는 데 실패했습니다: {e}")
    exit()

# ------------------------------
# 3. AES 암호화 함수
# ------------------------------
def encrypt_aes(data, aes_key):
    """
    주어진 데이터를 AES-256 (EAX Mode)로 암호화
    """
    data_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data_bytes)
    return {
        'ciphertext': ciphertext,
        'nonce': cipher.nonce,
        'tag': tag
    }

# ------------------------------
# 4. RSA로 AES 키 암호화
# ------------------------------
def encrypt_aes_key(aes_key, rsa_pub_key):
    """
    AES 키를 RSA 공개 키로 암호화
    """
    rsa_cipher = PKCS1_OAEP.new(RSA.import_key(rsa_pub_key))
    enc_key = rsa_cipher.encrypt(aes_key)
    return enc_key

# ------------------------------
# 5. DB 연결 및 테이블 생성
# ------------------------------
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='cjfdl2#mysql',
        database='sea_system'
    )
    cur = conn.cursor()
except mysql.connector.Error as err:
    print(f"MySQL 연결 오류: {err}")
    exit()

# 테이블 생성
cur.execute('''
CREATE TABLE passengers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    gender CHAR(1),
    job VARCHAR(255),
    encrypted_data BLOB NOT NULL,
    encrypted_aes_key BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
print("[INFO] DB 테이블 'passengers' 준비 완료.")

# ------------------------------
# 6. 데이터 암호화 및 DB 저장
# ------------------------------
print("[INFO] 데이터 암호화 및 DB 저장 시작...")

# Check for required columns
required_columns_csv = ['이름', '성별', '직업', '생년월일', '전화번호', '지병여부']
missing_required = [col for col in required_columns_csv if col not in df.columns]

if missing_required:
    print(f"오류: CSV 파일에 필수 컬럼이 누락되었습니다: {missing_required}")
    print(f"현재 CSV 컬럼: {list(df.columns)}")
    exit()

for index, row in df.iterrows():
    # 1) Generate a unique AES key for each row
    aes_key = get_random_bytes(32)  # 256-bit AES

    # 2) Encrypt the truly sensitive data with AES
    # 암호화 대상: '생년월일', '전화번호', '지병여부'
    data_to_encrypt = {
        '생년월일': row['생년월일'],
        '전화번호': row['전화번호'],
        '지병여부': bool(row['지병여부'])
    }
        
    aes_encrypted = encrypt_aes(data_to_encrypt, aes_key)

    # 3) Encrypt the AES key with the RSA public key
    enc_aes_key = encrypt_aes_key(aes_key, public_key)

    # 4) Prepare data for DB
    encrypted_data_dict_for_db = {
        'ciphertext': base64.b64encode(aes_encrypted['ciphertext']).decode('utf-8'),
        'nonce': base64.b64encode(aes_encrypted['nonce']).decode('utf-8'),
        'tag': base64.b64encode(aes_encrypted['tag']).decode('utf-8')
    }
    encrypted_data_bytes_for_db = json.dumps(encrypted_data_dict_for_db).encode('utf-8')
    encrypted_aes_key_bytes_for_db = base64.b64encode(enc_aes_key)
    
    # 5) Store in the database with separate plaintext and encrypted data
    cur.execute('''
        INSERT IGNORE INTO passengers (name, gender, job, encrypted_data, encrypted_aes_key)
        VALUES (%s, %s, %s, %s, %s)
    ''', (row['이름'], row['gender'], row['직업'], encrypted_data_bytes_for_db, encrypted_aes_key_bytes_for_db))

conn.commit()
conn.close()
print("[INFO] 데이터 저장 완료!")
