#### docs/deployment.md  
  
# Deployment Guide  
  
## Production Deployment  

---
### Docker Deployment  
  
1. **Docker 이미지 빌드**  
  
```bash  
docker build -t location-platform:latest . 
``` 
2. **Production 환경 설정**
```bash
cp .env.example .env.production  
# .env.production에 실제 프로덕션 값 입력
```
3. **Docker Compose 실행**
```bash
docker-compose -f docker-compose.prod.yml up -d
```
---
### Environment Variables
프로덕션 환경에서는 다음 환경 변수가 필요합니다:

- DATABASE_URL: PostgreSQL 연결 문자열
- REDIS_URL: Redis 연결 문자열
- OPENAI_API_KEY: OpenAI API 키
- SECRET_KEY: JWT 서명을 위한 시크릿 키
- BASE_URL: 서비스 기본 URL
- ENVIRONMENT: production
---
### Database Setup

1. PostgreSQL + PostGIS 설치
```sql
CREATE DATABASE locationdb;  
CREATE USER location_user WITH PASSWORD 'secure_password';  
GRANT ALL PRIVILEGES ON DATABASE locationdb TO location_user;
```
2. PostGIS 확장 활성화
```sql
\c locationdb  
CREATE EXTENSION IF NOT EXISTS postgis;
```

3. 데이터베이스 마이그레이션
```bash
python -m app.db_init
```
---
### Redis Setup
Redis 서버를 설치하고 실행합니다:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server  
  
# CentOS/RHEL
sudo yum install redis  
  
# macOS
brew install redis
```
---

### SSL/HTTPS 설정
프로덕션 환경에서는 HTTPS가 필수입니다. Nginx를 리버스 프록시로 사용하는 것을 권장합니다:

```
server {  
    listen 443 ssl;  
    server_name your-domain.com;  
      
    ssl_certificate /path/to/certificate.crt;  
    ssl_certificate_key /path/to/private.key;  
      
    location / {  
        proxy_pass http://127.0.0.1:8000;  
        proxy_set_header Host $host;  
        proxy_set_header X-Real-IP $remote_addr;  
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  
        proxy_set_header X-Forwarded-Proto $scheme;  
    }  
      
    location /ws/ {  
        proxy_pass http://127.0.0.1:8000;  
        proxy_http_version 1.1;  
        proxy_set_header Upgrade $http_upgrade;  
        proxy_set_header Connection "upgrade";  
        proxy_set_header Host $host;  
    }  
}
```
### Monitoring
1. Health Check
```bash
curl https://your-domain.com/health
```
2. Log Monitoring
```bash
docker-compose logs -f app
```

3. Performance Monitoring
- APM 도구 (New Relic, DataDog 등) 연동
- Prometheus + Grafana 모니터링
---

### Scaling

1. **Horizontal Scaling**

```bash
docker-compose up -d --scale app=3
```

2. **Load Balancing**

Nginx나 AWS ALB를 사용한 로드 밸런싱

3. **Database Scaling**
- Read Replica 구성
- Connection Pooling 최적화

---

### Security
1. **Firewall 설정**
```bash
# 8000 포트만 허용
sudo ufw allow 8000  
sudo ufw enable
```
2. **Environment Variables 보호**
- .env 파일을 버전 관리에서 제외
- 시크릿 관리 도구 사용 (Vault, AWS Secrets Manager)

3. **Dependency Updates**
```bash
# 정기적인 의존성 업데이트
uv pip install --upgrade -e ".[dev]"
```

4. **API 보안**
- Rate limiting 구현
- CORS 설정 최적화
- HTTPS 강제 사용

---

### Troubleshooting
일반적인 문제들
1. 데이터베이스 연결 실패
```bash
# PostgreSQL 상태 확인
docker-compose ps postgres  
# 로그 확인
docker-compose logs postgres
```
2. Redis 연결 문제
```bash
# Redis 테스트
redis-cli ping
```
3. 포트 충돌
```bash
# 포트 사용 확인
lsof -i :8000  
# 다른 포트로 실행
uvicorn app.main:app --port 8001
```

---

### Performance Tuning
1. 데이터베이스 최적화
```sql
    -- 인덱스 최적화  
ANALYZE locations;  
REINDEX INDEX idx_locations_geom;
```
2. Redis 설정
```bash
# redis.conf 최적화
maxmemory 256mb  
maxmemory-policy allkeys-lru
```
3. Uvicorn 설정
```
# 워커 수 조정
uvicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```
---

## Backup and Recovery
### 데이터베이스 백업
```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U user locationdb > backup.sql  
  
# 복원
docker-compose exec -T postgres psql -U user locationdb < backup.sql
```
### Redis 백업
```bash
# Redis 백업
docker-compose exec redis redis-cli BGSAVE
```
---