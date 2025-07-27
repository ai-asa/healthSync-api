"""HealthSync API メインアプリケーション"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging import configure_logging, get_logger

# 構造化ロギングを設定
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("HealthSync API starting up", version="0.1.0")
    yield
    # 終了時
    logger.info("HealthSync API shutting down")


app = FastAPI(
    title="HealthSync API",
    description="iOS HealthKitと連携するヘルスケアデータ収集・分析API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    response = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
        "service": "healthsync-api"
    }
    logger.debug("Health check requested", response=response)
    return response