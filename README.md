# AI Location Platform  
  
AI 기반 위치 인지형 콘텐츠 추천 및 공유 플랫폼  
  
## 기능  
  
- 🤖 위치 기반 AI 추천 시스템  
- 🗺️ PostGIS를 활용한 지리 정보 검색  
- 🔗 Redis 기반 고속 URL 단축기  
- 💬 WebSocket 실시간 채팅  
- 📡 SSE 스트리밍 응답  
- 📊 사용자 행동 분석 및 통계  
  
## 기술 스택  
  
- **Backend**: FastAPI, Uvicorn  
- **Database**: PostgreSQL + PostGIS  
- **Cache**: Redis  
- **AI**: OpenAI API  
- **Real-time**: WebSocket, SSE  
  
## 설치 및 실행  
  
### 1. 환경 설정  
  
```bash  
# 가상환경 생성
python -m venv venv  
source venv/bin/activate  # Windows: venv\Scripts\activate  
  
# 의존성 설치
uv pip install -e ".[dev]"  
  
# 환경 변수 설정
cp .env.example .env  
# .env 파일에 실제 값 입력
```
### 2. 인프라 시작
```bash
docker compose up -d
```
### 3. 데이터베이스 초기화
python -m app.db_init
### 4. 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
## API 문서
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
## 테스트
```bash
pytest
```
## 프로젝트 구조
```text
location-ai-platform/  
├── app/  
│   ├── models/          # 데이터 모델  
│   ├── routers/         # API 라우터  
│   ├── services/        # 비즈니스 로직  
│   └── websocket/       # WebSocket 핸들러  
├── tests/               # 테스트 코드  
├── docs/                # 문서  
└── docker-compose.yml   # 인프라 설정  
```