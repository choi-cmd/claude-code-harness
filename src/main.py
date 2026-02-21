"""FastAPI 아크릴 단가 계산기 앱"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.v1.router import router as main_router
from src.api.v1.endpoints.image import router as image_router
from src.api.v1.endpoints.order import router as order_router
from src.api.v1.endpoints.admin import router as admin_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 이벤트"""
    # 시작: rembg 모델 사전 로딩
    try:
        from src.domain.calculator.rembg_service import preload_model
        logger.info("rembg 모델 사전 로딩 시작...")
        preload_model()
        logger.info("rembg 모델 사전 로딩 완료")
    except Exception as e:
        logger.warning("rembg 모델 사전 로딩 실패 (첫 요청 시 로딩됨): %s", e)
    yield
    # 종료: 정리 작업


# FastAPI 앱 생성
app = FastAPI(
    title="서블리원 아크릴 주문제작 프로그램",
    description="아크릴 주문제작 단가 계산 및 주문 신청 시스템",
    version="3.0.0",
    lifespan=lifespan,
)

# 정적 파일 설정
BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# API 라우터 등록
app.include_router(main_router)
app.include_router(image_router)
app.include_router(order_router)
app.include_router(admin_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
