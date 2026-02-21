"""API v1 라우터"""

from pathlib import Path

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.api.deps import CalculatorServiceDep
from src.domain.calculator.schemas import CalculateRequest
from src.domain.calculator.shape_analyzer import analyze_image, analyze_with_custom_mask, convert_to_mm
from src.domain.calculator.shape_pricing import ShapePricingService

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")

# 프로젝트 루트 기준 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "src" / "static" / "uploads"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """메인 페이지"""
    response = templates.TemplateResponse("calculator.html", {"request": request})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    return response


@router.post("/api/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    width: float = Form(...),
    height: float = Form(...),
    quantity: int = Form(...),
    service: CalculatorServiceDep = None,
) -> HTMLResponse:
    """
    단가 계산 API (HTMX 호출) - 직접 입력 모드 (기존 수식)

    Args:
        width: 가로 (mm)
        height: 세로 (mm)
        quantity: 주문 수량
        service: Calculator 서비스

    Returns:
        계산 결과 HTML 조각
    """
    try:
        calc_request = CalculateRequest(width=width, height=height, quantity=quantity)
        result = service.calculate(calc_request)

        return templates.TemplateResponse(
            "partials/result.html", {"request": request, "result": result}
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )


@router.post("/api/calculate-shape", response_class=HTMLResponse)
async def calculate_shape(
    request: Request,
    file_path: str = Form(...),
    width: float = Form(...),
    height: float = Form(...),
    quantity: int = Form(...),
    polygon: str = Form(""),
    product_type: str = Form("objet"),
    hole_type: str = Form("ring"),
) -> HTMLResponse:
    """
    형상 기반 견적 API (HTMX 호출) - 이미지 분석 모드

    Args:
        file_path: 업로드된 이미지 경로
        width: 바운딩 박스 가로 (mm) - 키링이면 고리 포함 전체 크기
        height: 바운딩 박스 세로 (mm) - 키링이면 고리 포함 전체 크기
        quantity: 주문 수량
        polygon: 수동 선택 폴리곤 JSON
        product_type: 제품 타입 (objet/keyring)
    """
    try:
        from urllib.parse import unquote
        decoded_path = unquote(file_path)
        filename = Path(decoded_path).name
        actual_path = UPLOAD_DIR / filename
        if not actual_path.exists():
            raise HTTPException(status_code=400, detail="이미지 파일을 찾을 수 없습니다")

        import json
        if polygon and polygon.strip():
            polygon_points = json.loads(polygon)
            metrics = analyze_with_custom_mask(actual_path, polygon_points)
        else:
            metrics = analyze_image(actual_path)
        if metrics is None:
            raise HTTPException(status_code=400, detail="이미지 분석에 실패했습니다")

        metrics = convert_to_mm(metrics, width, height)

        # 키링이면 타공비 100원 추가
        drilling_fee = 0
        if product_type == "keyring":
            from src.domain.calculator.cutting_line_generator import get_drilling_fee
            drilling_fee = get_drilling_fee()

        pricing = ShapePricingService()
        quote = pricing.full_quote(metrics, quantity, drilling_fee=drilling_fee)

        return templates.TemplateResponse(
            "partials/shape_result.html",
            {
                "request": request,
                "quote": quote,
                "width": width,
                "height": height,
                "quantity": quantity,
                "product_type": product_type,
                "hole_type": hole_type,
            },
        )
    except ValueError as e:
        return templates.TemplateResponse(
            "partials/error.html", {"request": request, "error": str(e)}
        )
