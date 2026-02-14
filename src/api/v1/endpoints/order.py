"""주문 API"""

import os
import shutil
from pathlib import Path
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Form,
    UploadFile,
    File,
    HTTPException,
    Request,
    Depends,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.domain.order.service import OrderService
from src.domain.order.schemas import OrderCreate

router = APIRouter(prefix="/api/order", tags=["order"])
templates = Jinja2Templates(directory="src/templates")

UPLOAD_DIR = Path("src/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_order_service() -> OrderService:
    """Order 서비스 의존성"""
    return OrderService()


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post("/submit", response_class=HTMLResponse)
async def submit_order(
    request: Request,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    customer_email: str = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    quantity: int = Form(...),
    notes: Optional[str] = Form(None),
    ratio_file_path: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    service: OrderServiceDep = None,
) -> HTMLResponse:
    """
    주문 신청

    Args:
        customer_name: 고객 이름
        customer_phone: 연락처
        customer_email: 이메일
        width: 가로 (mm)
        height: 세로 (mm)
        quantity: 주문 수량
        notes: 요청사항
        file: 디자인 파일
        service: 주문 서비스

    Returns:
        주문 완료 HTML
    """
    try:
        file_path = None

        # 파일 업로드 처리
        if file and file.filename:
            # 파일명 안전하게 처리
            safe_filename = f"{customer_phone}_{file.filename}"
            file_path_obj = UPLOAD_DIR / safe_filename

            # 파일 저장
            with file_path_obj.open("wb") as f:
                content = await file.read()
                f.write(content)

            file_path = f"/static/uploads/{safe_filename}"

        # 비율 계산에서 업로드한 파일 경로 사용 (새 파일이 없을 때)
        if not file_path and ratio_file_path and ratio_file_path.strip():
            file_path = ratio_file_path.strip()

        # 주문 생성
        order_data = OrderCreate(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            width=width,
            height=height,
            quantity=quantity,
            file_path=file_path,
            notes=notes,
        )

        order = service.create_order(order_data)

        # 성공 메시지 반환
        return templates.TemplateResponse(
            "partials/order_success.html",
            {"request": request, "order": order},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 처리 오류: {str(e)}")
