"""관리자 API"""

from typing import Annotated, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.domain.order.service import OrderService

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="src/templates")

# 간단한 관리자 비밀번호 (실제로는 환경변수나 DB에 저장)
ADMIN_PASSWORD = "admin1234"


def get_order_service() -> OrderService:
    """Order 서비스 의존성"""
    return OrderService()


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


def verify_admin(admin_token: Optional[str] = Cookie(None)) -> bool:
    """관리자 인증 확인"""
    return admin_token == ADMIN_PASSWORD


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> HTMLResponse:
    """관리자 로그인 페이지"""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def admin_login(password: str) -> RedirectResponse:
    """관리자 로그인 처리"""
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin/orders", status_code=303)
        response.set_cookie(key="admin_token", value=ADMIN_PASSWORD, httponly=True)
        return response
    else:
        raise HTTPException(status_code=401, detail="비밀번호가 틀렸습니다")


@router.get("/logout")
async def admin_logout() -> RedirectResponse:
    """관리자 로그아웃"""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_token")
    return response


@router.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    service: OrderServiceDep,
    admin_token: Optional[str] = Cookie(None),
) -> HTMLResponse:
    """관리자 주문 목록 페이지"""
    if not verify_admin(admin_token):
        return RedirectResponse(url="/admin/login", status_code=303)

    orders = service.get_all_orders()
    return templates.TemplateResponse(
        "admin/orders.html", {"request": request, "orders": orders}
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(
    request: Request,
    order_id: str,
    service: OrderServiceDep,
    admin_token: Optional[str] = Cookie(None),
) -> HTMLResponse:
    """관리자 주문 상세 페이지"""
    if not verify_admin(admin_token):
        return RedirectResponse(url="/admin/login", status_code=303)

    order = service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")

    return templates.TemplateResponse(
        "admin/order_detail.html", {"request": request, "order": order}
    )
