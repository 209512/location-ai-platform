from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.logging
from app.routers import ai_chat, locations, streaming, urls
from app.websocket import chat_handler

app = FastAPI(
    title="AI Location Platform",
    description="AI 기반 위치 인지형 콘텐츠 추천 및 공유 플랫폼",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(ai_chat.router, prefix="/api/chat", tags=["AI Chat"])
app.include_router(locations.router, prefix="/api/locations", tags=["Locations"])
app.include_router(urls.router, prefix="/api/urls", tags=["URL Shortener"])
app.include_router(streaming.router, prefix="/api/stream", tags=["Streaming"])

# WebSocket
app.include_router(chat_handler.router, prefix="/ws")


@app.get("/")
async def root():
    return {"message": "AI Location Platform API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
