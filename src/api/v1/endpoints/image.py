"""이미지 처리 API"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from src.domain.order.service import OrderService
from src.domain.order.schemas import ImageRatioRequest
from src.domain.calculator.shape_analyzer import analyze_image, convert_to_mm
from src.domain.calculator.shape_pricing import ShapePricingService

router = APIRouter(prefix="/api/image", tags=["image"])
templates = Jinja2Templates(directory="src/templates")

UPLOAD_DIR = Path("src/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_class=HTMLResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    target_size: Optional[float] = Form(None),
    target_dimension: str = Form("auto"),
) -> HTMLResponse:
    """
    이미지 업로드 및 비율 계산 + OpenCV 형상 분석

    Args:
        file: 업로드 이미지
        target_size: 목표 크기 (mm)
        target_dimension: 기준 방향 (width/height)

    Returns:
        비율 계산 결과 HTML
    """
    try:
        # 파일 확장자 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다")

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ai", ".psd"]:
            raise HTTPException(
                status_code=400, detail="지원하지 않는 파일 형식입니다"
            )

        # 임시 파일로 저장
        temp_path = UPLOAD_DIR / f"temp_{file.filename}"
        with temp_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        # 이미지 크기 읽기
        with Image.open(temp_path) as img:
            # PNG 투명 배경인 경우 실제 객체만의 크기 계산
            if img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            ):
                # 알파 채널로 실제 객체 영역 찾기
                if img.mode == "P":
                    img = img.convert("RGBA")

                bbox = img.getbbox()  # 투명하지 않은 영역의 바운딩 박스
                if bbox:
                    original_width = bbox[2] - bbox[0]
                    original_height = bbox[3] - bbox[1]
                    is_transparent = True
                else:
                    original_width, original_height = img.size
                    is_transparent = False
            else:
                # JPG 등 투명도 없는 이미지는 전체 크기 사용
                original_width, original_height = img.size
                is_transparent = False

        # auto 모드: 이미지 픽셀 크기를 mm로 직접 사용
        if target_dimension == "auto":
            from src.domain.order.schemas import ImageRatioResponse

            ratio = original_width / original_height
            result = ImageRatioResponse(
                original_width=original_width,
                original_height=original_height,
                target_width=round(original_width),
                target_height=round(original_height),
                ratio=round(ratio, 4),
                target_dimension="auto",
            )
        else:
            # 비율 계산
            service = OrderService()
            ratio_request = ImageRatioRequest(
                original_width=original_width,
                original_height=original_height,
                target_size=target_size,
                target_dimension=target_dimension,
            )
            result = service.calculate_image_ratio(ratio_request)

        # OpenCV 형상 분석 (PNG/JPG만)
        shape_analysis = None
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            metrics = analyze_image(str(temp_path))
            if metrics is not None:
                metrics = convert_to_mm(
                    metrics,
                    float(result.target_width),
                    float(result.target_height),
                )
                pricing = ShapePricingService()
                price_info = pricing.calculate_shape_price(metrics)
                complexity_mult, complexity_label = pricing.complexity_multiplier(
                    metrics.complexity_score
                )
                shape_analysis = {
                    "area_mm2": metrics.area_mm2,
                    "perimeter_mm": metrics.perimeter_mm,
                    "fill_ratio": metrics.fill_ratio,
                    "fill_pct": round(metrics.fill_ratio * 100, 1),
                    "complexity_score": metrics.complexity_score,
                    "complexity_label": complexity_label,
                    "complexity_pct": round(metrics.complexity_score * 100, 1),
                    "vertex_count": metrics.vertex_count,
                    "circularity": metrics.circularity,
                    "unit_price": price_info["unit_price"],
                    "material_cost": price_info["material_cost"],
                    "processing_cost": price_info["processing_cost"],
                    "complexity_multiplier": price_info["complexity_multiplier"],
                    "efficiency_multiplier": price_info["efficiency_multiplier"],
                    "efficiency_label": price_info["efficiency_label"],
                    "margin": price_info["margin"],
                }

        # 템플릿 렌더링
        return templates.TemplateResponse(
            "partials/image_ratio.html",
            {
                "request": request,
                "result": result,
                "filename": file.filename,
                "is_transparent": is_transparent,
                "file_path": f"/static/uploads/temp_{file.filename}",
                "shape_analysis": shape_analysis,
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 처리 오류: {str(e)}")
