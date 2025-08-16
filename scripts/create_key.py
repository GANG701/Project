from Crypto.PublicKey import RSA
import os

private_key_path = "#.pem" # 키 파일 경로
public_key_path = "#.pem" # 키 파일 경로

# 키 파일 여부 확인
if os.path.exists(private_key_path) or os.path.exists(public_key_path):
    print("[경고] RSA 키 파일이 이미 존재합니다. 새로운 키를 생성하지 않고 종료합니다.")
    print("기존 키를 덮어쓰려면 파일을 수동으로 삭제 후 다시 실행하세요.")
else:
    # 새로운 RSA 키 쌍 생성
    print("[INFO] 새로운 RSA 키 쌍을 생성하는 중...")
    rsa_key = RSA.generate(2048)
    private_key = rsa_key.export_key()
    public_key = rsa_key.publickey().export_key()

    # 키 파일을 로컬에 저장
    try:
        with open(private_key_path, "wb") as f:
            f.write(private_key)
        with open(public_key_path, "wb") as f:
            f.write(public_key)
        print(f"[성공] RSA 개인키가 '{private_key_path}'에, 공개키가 '{public_key_path}'에 저장되었습니다.")
        print("개인 키는 안전하게 보관하세요. 절대 외부에 노출해서는 안 됩니다.")
    except IOError as e:
        print(f"[오류] 키 파일을 저장하는 데 실패했습니다: {e}")
