# 🚢 승객 데이터 암호화 시스템

RSA와 AES 암호화를 조합하여 승객 개인정보를 안전하게 관리하는 시스템입니다.

## ✨ 주요 기능

- **이중 암호화**: AES-256 + RSA-2048 하이브리드 암호화
- **민감 데이터 분리**: 일반 정보와 민감 정보 분리 저장
- **FastAPI 서버**: RESTful API를 통한 안전한 데이터 접근
- **MySQL 데이터베이스**: 암호화된 승객 데이터 저장

## 🚀 빠른 시작

### 1. 환경 설정
```bash

# 가상환경 생성
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# MySQL 설치 및 데이터베이스 생성
CREATE DATABASE sea_system;

# 키 디렉토리 생성
mkdir keys
```

### 2. 실행 순서
```bash
# 1. RSA 키 생성
cd scripts
python create_key.py

# 2. 데이터 암호화 및 저장
python encrypt_data.py

# 3. 데이터 복호화 테스트
python decrypt_data.py

# 4. FastAPI 서버 실행
cd ../server
python fastapi_decrypt_server.py
```

### 3. API 사용
- 서버: `http://127.0.0.1:8000`
- API 문서: `http://127.0.0.1:8000/docs`
- 승객 조회: `GET /passenger/{id}`

## 📁 프로젝트 구조

```
region_project/
├── data/                          # 승객 데이터 (CSV)
├── keys/                          # RSA 키 파일
├── scripts/                       # 암호화/복호화 스크립트
├── server/                        # FastAPI 서버
└── requirements.txt               # Python 패키지
```

## 🔌 API 예시

### 승객 정보 조회
```http
GET /passenger/1
```

**응답:**
```json
{
  "id": 1,
  "name": "Lee Minjun",
  "gender": "M",
  "job": "Doctor",
  "생년월일": "1989-03-25",
  "전화번호": "010-3928-4721",
  "지병여부": true
}
```

## 🔒 보안

- **AES-256**: 민감 데이터 암호화
- **RSA-2048**: 키 암호화
- **개별 키**: 각 레코드마다 고유한 AES 키
- **데이터 분리**: 일반 정보(이름, 성별, 직업)와 민감 정보(생년월일, 전화번호, 지병여부) 분리

## 🛠️ 기술 스택

- **Python 3.8+** + **FastAPI** + **MySQL**
- **PyCryptodome** + **Pandas**

## 🔧 문제 해결

### 자주 발생하는 오류

| 오류 | 해결 방법 |
|------|-----------|
| MySQL 연결 오류 | 비밀번호 확인, MySQL 서비스 실행 확인 |
| 키 파일 없음 | `cd scripts && python create_key.py` |
| CSV 파일 없음 | `data/passenger_data.csv` 파일 존재 확인 |
| 패키지 오류 | `pip install -r requirements.txt` |
| 포트 충돌 | 다른 포트 사용 또는 기존 프로세스 종료 |

---

**⚠️ 주의사항**: 교육 목적 프로젝트입니다. 실제 운영 전 보안 검토 필수. 