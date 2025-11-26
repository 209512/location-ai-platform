# API Documentation  
  
## Overview  
  
AI Location Platform은 위치 기반 AI 추천, URL 단축, 실시간 통신 기능을 제공하는 REST API입니다.  
  
## Authentication  
  
현재 버전에서는 인증이 구현되어 있지 않습니다. 향후 JWT 기반 인증이 추가될 예정입니다.  
  
## Base URL  
  
- Development: `http://localhost:8000`  
- Production: `https://your-domain.com`  
  
## Endpoints  
  
### AI Chat API  
  
#### POST /api/chat/recommend  
  
위치 기반 AI 추천을 생성합니다.  
  
**Request Body:**  
```json  
{  
  "message": "근처 맛집 추천해줘",  
  "latitude": 37.5665,  
  "longitude": 126.9780,  
  "category": "restaurant"  
}
```

**Response:**
```jsojn
{  
  "response": "AI 추천 내용...",  
  "share_url": "http://localhost:8000/s/abc123"  
}
```

### Locations API

#### POST /api/locations/nearby

반경 내 위치를 검색합니다.

**Request Body:**
```json
{  
  "latitude": 37.5665,  
  "longitude": 126.9780,  
  "radius_km": 5.0,  
  "category": "restaurant"  
}
```

#### POST /api/locations/

새로운 위치를 생성합니다.

**Request Body:**
```json
{  
  "name": "새로운 장소",  
  "latitude": 37.5665,  
  "longitude": 126.9780,  
  "category": "restaurant",  
  "description": "장소 설명",  
  "address": "주소",  
  "phone": "전화번호"  
}
```
### URL Shortener API
#### POST /api/urls/create
단축 URL을 생성합니다.

**Request Body:**
```json
{  
  "url": "https://example.com/very/long/url",  
  "custom_code": "optional-custom-code",  
  "expires_in_days": 30  
}
```
#### GET /s/{short_code}
단축 URL을 원본 URL로 리다이렉션합니다.

#### GET /api/urls/stats/{short_code}
URL 클릭 통계를 조회합니다.

### WebSocket
#### /ws/chat/{user_id}
실시간 채팅을 위한 WebSocket 연결입니다.

**Message Format:**
```json
{  
  "type": "chat",  
  "message": "안녕하세요",  
  "timestamp": 1234567890  
}
```

### SSE (Server-Sent Events)
#### GET /api/stream/ai-chat
AI 응답을 스트리밍으로 전송합니다.

**Query Parameters:**
- query: 검색 쿼리
- lat: 위도
- lng: 경도
#### GET /api/stream/location/{user_id}
실시간 위치 업데이트를 스트리밍으로 전송합니다.

### Error Responses
에러 응답은 다음 형식을 따릅니다:
```json
{  
  "detail": "에러 메시지"  
}
```
### Status Codes
- 200 - 성공
- 201 - 생성됨
- 400 - 잘못된 요청
- 404 - 찾을 수 없음
- 422 - 검증 에러
- 500 - 서버 내부 에러