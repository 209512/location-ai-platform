import asyncio
import json
import logging
from typing import dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 수락 및 관리"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")
        await self.broadcast(f"User {user_id} joined the chat")

    def disconnect(self, user_id: str):
        """WebSocket 연결 해제"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: str, user_id: str):
        """특정 사용자에게 메시지 전송"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(message)
                logger.debug(f"Sent personal message to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {str(e)}")
                self.disconnect(user_id)

    async def broadcast(self, message: str):
        """모든 연결된 사용자에게 메시지 브로드캐스트"""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
                logger.debug(f"Broadcasted message to user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to broadcast to user {user_id}: {str(e)}")
                disconnected_users.append(user_id)

        # 연결이 끊어진 사용자 정리
        for user_id in disconnected_users:
            self.disconnect(user_id)

        if disconnected_users:
            logger.info(
                f"Cleaned up {len(disconnected_users)} disconnected connections"
            )


manager = ConnectionManager()


@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket 채팅 엔드포인트"""
    logger.info(f"WebSocket connection request from user: {user_id}")

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id}: {data}")

            try:
                message_data = json.loads(data)

                # 메시지 타입에 따른 처리
                if message_data.get("type") == "chat":
                    # 일반 채팅 메시지
                    response = {
                        "type": "chat_response",
                        "user_id": user_id,
                        "message": message_data.get("message", ""),
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                    await manager.send_personal_message(json.dumps(response), user_id)
                    await manager.broadcast(
                        json.dumps(
                            {
                                "type": "broadcast",
                                "user_id": user_id,
                                "message": message_data.get("message", ""),
                            }
                        )
                    )

                elif message_data.get("type") == "location_request":
                    # 위치 기반 AI 추천 요청
                    lat = message_data.get("lat")
                    lng = message_data.get("lng")
                    query = message_data.get("query", "근처 맛집")

                    logger.info(
                        f"Processing location request from user {user_id}: {query} at ({lat}, {lng})"
                    )

                    try:
                        # AI 서비스 호출
                        ai_response = await ai_service.get_location_recommendations(
                            lat, lng, query
                        )

                        response = {
                            "type": "ai_recommendation",
                            "user_id": user_id,
                            "recommendations": ai_response,
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                        await manager.send_personal_message(
                            json.dumps(response), websocket
                        )
                        logger.info(f"Sent AI recommendations to user {user_id}")

                    except Exception as e:
                        logger.error(
                            f"Error processing AI recommendation for user {user_id}: {str(e)}"
                        )
                        error_response = {
                            "type": "error",
                            "message": "추천 생성 중 오류가 발생했습니다",
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                        await manager.send_personal_message(
                            json.dumps(error_response), websocket
                        )

                elif message_data.get("type") == "ping":
                    # 핑/퐥 연결 확인
                    pong_response = {
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                    await manager.send_personal_message(
                        json.dumps(pong_response), websocket
                    )
                    logger.debug(f"Sent pong to user {user_id}")

                else:
                    # 알 수 없는 메시지 타입
                    logger.warning(
                        f"Unknown message type from user {user_id}: {message_data.get('type')}"
                    )
                    error_response = {
                        "type": "error",
                        "message": "알 수 없는 메시지 타입입니다",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                    await manager.send_personal_message(
                        json.dumps(error_response), websocket
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}: {data}")
                error_response = {
                    "type": "error",
                    "message": "유효하지 않은 JSON 형식입니다",
                    "timestamp": asyncio.get_event_loop().time(),
                }
                await manager.send_personal_message(
                    json.dumps(error_response), websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f"User {user_id} left the chat")
        logger.info(f"User {user_id} WebSocket disconnected")

    except Exception as e:
        logger.error(f"Unexpected error in WebSocket for user {user_id}: {str(e)}")
        manager.disconnect(user_id)


@router.get("/health")
async def health_check():
    """WebSocket 서비스 상태 확인"""
    logger.debug("WebSocket service health check requested")
    return {
        "status": "healthy",
        "service": "websocket_chat",
        "active_connections": len(manager.active_connections),
    }
