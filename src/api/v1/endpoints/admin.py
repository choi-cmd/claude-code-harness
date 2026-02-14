"""관리자 API"""

import csv
import io
import zipfile
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
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
async def admin_login(password: str = Form(...)) -> RedirectResponse:
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


@router.get("/orders/download")
async def admin_orders_download(
    service: OrderServiceDep,
    admin_token: Optional[str] = Cookie(None),
    ids: Optional[str] = None,
) -> StreamingResponse:
    """주문 목록 CSV + 첨부파일 ZIP 다운로드"""
    if not verify_admin(admin_token):
        return RedirectResponse(url="/admin/login", status_code=303)

    orders = service.get_all_orders()
    if ids:
        id_list = ids.split(",")
        orders = [o for o in orders if o.order_id in id_list]

    # CSV 생성
    csv_output = io.StringIO()
    csv_output.write('\ufeff')  # BOM for Excel 한글 호환
    writer = csv.writer(csv_output)
    writer.writerow([
        "주문번호", "고객명", "연락처", "이메일",
        "가로(mm)", "세로(mm)", "수량", "최소수량",
        "개당단가", "총금액(VAT별도)", "총금액(VAT포함)",
        "샘플여부", "첨부파일", "요청사항", "주문일시", "상태",
    ])
    for order in orders:
        writer.writerow([
            order.order_id,
            order.customer_name,
            order.customer_phone,
            order.customer_email,
            order.width,
            order.height,
            order.quantity,
            order.min_quantity,
            order.unit_price,
            order.total_price,
            int(order.total_price * 1.1),
            "예" if order.is_sample else "아니오",
            order.file_path or "",
            order.notes or "",
            order.created_at,
            order.status,
        ])

    # 첨부파일 있는지 확인
    has_files = any(o.file_path for o in orders)

    if not has_files:
        # 첨부파일 없으면 CSV만 다운로드
        csv_output.seek(0)
        return StreamingResponse(
            iter([csv_output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=orders.csv"},
        )

    # 첨부파일 있으면 ZIP으로 묶어서 다운로드
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # CSV 추가
        zf.writestr("orders.csv", csv_output.getvalue().encode("utf-8-sig"))

        # 첨부파일 추가
        for order in orders:
            if order.file_path:
                file_path = Path("src" + order.file_path)
                if file_path.exists():
                    # 파일명: 주문번호_원본파일명
                    ext = file_path.suffix
                    archive_name = f"files/{order.order_id}_{order.customer_name}{ext}"
                    zf.write(file_path, archive_name)

    zip_buffer.seek(0)
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=orders.zip"},
    )


@router.post("/orders/bulk-status")
async def admin_bulk_status(
    request: Request,
    service: OrderServiceDep,
    admin_token: Optional[str] = Cookie(None),
) -> dict:
    """주문 상태 일괄 변경"""
    if not verify_admin(admin_token):
        raise HTTPException(status_code=401, detail="인증 필요")

    body = await request.json()
    order_ids = body.get("order_ids", [])
    status = body.get("status", "completed")

    for order_id in order_ids:
        service.repository.update_status(order_id, status)

    return {"ok": True, "updated": len(order_ids)}


@router.get("/orders/{order_id}/file")
async def admin_order_file_download(
    order_id: str,
    service: OrderServiceDep,
    admin_token: Optional[str] = Cookie(None),
) -> FileResponse:
    """첨부파일 다운로드"""
    if not verify_admin(admin_token):
        raise HTTPException(status_code=401, detail="인증 필요")

    order = service.get_order_by_id(order_id)
    if not order or not order.file_path:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

    # /static/uploads/filename -> src/static/uploads/filename
    file_path = Path("src" + order.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일이 존재하지 않습니다")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
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
