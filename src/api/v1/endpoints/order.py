"""주문 API"""

import logging
from pathlib import Path
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Form,
    UploadFile,
    File,
    Request,
    Depends,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from src.domain.order.service import OrderService
from src.domain.order.schemas import OrderCreate

logger = logging.getLogger(__name__)

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
    proof_requested: Optional[str] = Form(None),
    template_file: Optional[str] = Form(None),
    order_type: str = Form("order"),
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
            proof_requested=bool(proof_requested),
            template_file_requested=bool(template_file),
            order_type=order_type,
        )

        order = service.create_order(order_data)

        # 성공 메시지 반환
        return templates.TemplateResponse(
            "partials/order_success.html",
            {"request": request, "order": order},
        )

    except ValidationError as e:
        # Pydantic 유효성 검사 에러 → 사용자 친화적 메시지
        field_messages = {
            "customer_name": "이름을 입력해 주세요.",
            "customer_phone": "연락처를 정확히 입력해 주세요 (10자리 이상).",
            "customer_email": "올바른 이메일 주소를 입력해 주세요.",
            "width": "가로 크기를 확인해 주세요.",
            "height": "세로 크기를 확인해 주세요.",
            "quantity": "수량을 확인해 주세요.",
        }
        messages = []
        for err in e.errors():
            field = err["loc"][0] if err["loc"] else ""
            messages.append(field_messages.get(field, str(err["msg"])))
        error_msg = " / ".join(messages) if messages else "입력 정보를 확인해 주세요."
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": error_msg},
            status_code=200,
        )
    except Exception as e:
        logger.exception("주문 처리 오류")
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "error": "주문 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."},
            status_code=200,
        )
