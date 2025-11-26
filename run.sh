#!/bin/bash

echo "🚀 AI Location Platform 시작 중..."

# Docker 컨테이너 시작
docker-compose up -d

# 데이터베이스 초기화 대기
echo "⏳ 데이터베이스 초기화 대기 중..."
sleep 5

# 데이터베이스 초기화
echo "🗄️ 데이터베이스 초기화..."
python -m app.db_init

# FastAPI 서버 시작
echo "🌐 FastAPI 서버 시작..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

echo "✅ 서비스가 시작되었습니다!"
echo "📖 API 문서: http://localhost:8000/docs"
echo "🔍 ReDoc 문서: http://localhost:8000/redoc"