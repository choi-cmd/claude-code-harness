"""API v1 라우터"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.api.deps import CalculatorServiceDep
from src.domain.calculator.schemas import CalculateRequest, CalculateResponse

router = APIRouter()
templates = Jinja2Templates(directory="src/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """메인 페이지"""
    return templates.TemplateResponse("calculator.html", {"request": request})


@router.post("/api/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    width: float = Form(...),
    height: float = Form(...),
    quantity: int = Form(...),
    service: CalculatorServiceDep = None,
) -> HTMLResponse:
    """
    단가 계산 API (HTMX 호출)

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
