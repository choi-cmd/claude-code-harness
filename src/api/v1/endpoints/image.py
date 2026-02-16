"""이미지 처리 API"""

import json
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from src.domain.order.service import OrderService
from src.domain.order.schemas import ImageRatioRequest
from src.domain.calculator.shape_analyzer import (
    analyze_image,
    analyze_with_custom_mask,
    convert_to_mm,
    create_transparent_preview,
    create_preview_with_custom_mask,
)
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

        # 이미지 크기 읽기 (PIL 우선, 실패 시 OpenCV 폴백)
        is_transparent = False
        try:
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
                else:
                    # JPG 등 투명도 없는 이미지는 전체 크기 사용
                    original_width, original_height = img.size
        except Exception:
            # PIL 실패 시 OpenCV로 폴백
            import cv2
            cv_img = cv2.imread(str(temp_path), cv2.IMREAD_UNCHANGED)
            if cv_img is None:
                raise ValueError("이미지 파일을 읽을 수 없습니다. 다른 파일을 첨부해 주세요.")
            h, w = cv_img.shape[:2]
            original_width, original_height = w, h
            # RGBA인 경우 투명 배경 처리
            if len(cv_img.shape) == 3 and cv_img.shape[2] == 4:
                is_transparent = True

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
            # 비율 계산 - target_size 필수
            if target_size is None or target_size <= 0:
                raise ValueError("원하는 크기(mm)를 입력해 주세요")

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
        preview_path = None
        if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            metrics = analyze_image(str(temp_path))
            if metrics is not None:
                # JPG 배경 제거 성공 판정: fill_ratio < 0.95이면 실제 객체 분리 성공
                bg_removed = (
                    not is_transparent
                    and ext in [".jpg", ".jpeg", ".bmp"]
                    and metrics.fill_ratio < 0.95
                )
                if bg_removed:
                    obj_w, obj_h = metrics.bounding_box_px
                    if obj_w > 0 and obj_h > 0:
                        original_width = obj_w
                        original_height = obj_h
                        is_transparent = True  # 배경 분리 성공 표시

                        # 비율/크기 재계산
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
                            svc = OrderService()
                            ratio_request = ImageRatioRequest(
                                original_width=original_width,
                                original_height=original_height,
                                target_size=target_size,
                                target_dimension=target_dimension,
                            )
                            result = svc.calculate_image_ratio(ratio_request)

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

                # 배경 분리 성공한 JPG만 투명 미리보기 생성
                if bg_removed:
                    preview_filename = f"temp_{file.filename}_preview.png"
                    preview_output = UPLOAD_DIR / preview_filename
                    if create_transparent_preview(str(temp_path), str(preview_output)):
                        preview_path = f"/static/uploads/{preview_filename}"

        # 템플릿 렌더링
        return templates.TemplateResponse(
            "partials/image_ratio.html",
            {
                "request": request,
                "result": result,
                "filename": file.filename,
                "is_transparent": is_transparent,
                "file_path": f"/static/uploads/temp_{file.filename}",
                "preview_path": preview_path,
                "shape_analysis": shape_analysis,
            },
        )

    except ValueError as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>⚠️ 입력 오류</h3>'
            f'<p style="color:#856404;font-size:14px;">{str(e)}</p></div>',
            status_code=200,
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>❌ 처리 오류</h3>'
            f'<p style="color:#c0392b;font-size:14px;">이미지 처리 중 오류가 발생했습니다: {str(e)}</p></div>',
            status_code=200,
        )


@router.post("/manual-mask", response_class=HTMLResponse)
async def manual_mask(
    request: Request,
    file_path: str = Form(...),
    polygon: str = Form(...),
    target_width: float = Form(...),
    target_height: float = Form(...),
) -> HTMLResponse:
    """
    사용자 수동 영역 선택으로 형상 분석

    Args:
        file_path: 업로드된 파일의 static 경로 (예: /static/uploads/temp_xxx.jpg)
        polygon: JSON 문자열 [[x,y],[x,y],...]
        target_width: 목표 가로 크기 (mm)
        target_height: 목표 세로 크기 (mm)

    Returns:
        비율 계산 결과 HTML (image_ratio.html)
    """
    try:
        # 폴리곤 파싱
        polygon_points = json.loads(polygon)
        if not polygon_points or len(polygon_points) < 3:
            raise ValueError("최소 3개 이상의 점이 필요합니다")

        # file_path에서 실제 파일 시스템 경로 복원 (URL 인코딩 디코딩)
        decoded_path = unquote(file_path)
        filename = Path(decoded_path).name
        actual_path = UPLOAD_DIR / filename
        if not actual_path.exists():
            raise ValueError("이미지 파일을 찾을 수 없습니다")

        # 커스텀 마스크로 형상 분석
        metrics = analyze_with_custom_mask(str(actual_path), polygon_points)
        if metrics is None:
            raise ValueError("선택한 영역을 분석할 수 없습니다. 다시 시도해주세요.")

        metrics = convert_to_mm(metrics, target_width, target_height)

        # 가격 계산
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

        # 투명 미리보기 생성
        preview_filename = f"{filename}_manual_preview.png"
        preview_output = UPLOAD_DIR / preview_filename
        preview_path = None
        if create_preview_with_custom_mask(
            str(actual_path), str(preview_output), polygon_points
        ):
            preview_path = f"/static/uploads/{preview_filename}"

        # 원본 이미지 크기 읽기
        import cv2
        from src.domain.calculator.shape_analyzer import _imread_safe

        img = _imread_safe(str(actual_path), cv2.IMREAD_UNCHANGED)
        if img is not None:
            oh, ow = img.shape[:2]
        else:
            ow, oh = 100, 100

        ratio = ow / oh if oh > 0 else 1

        from src.domain.order.schemas import ImageRatioResponse

        result = ImageRatioResponse(
            original_width=ow,
            original_height=oh,
            target_width=round(target_width),
            target_height=round(target_height),
            ratio=round(ratio, 4),
            target_dimension="manual",
        )

        return templates.TemplateResponse(
            "partials/image_ratio.html",
            {
                "request": request,
                "result": result,
                "filename": filename,
                "is_transparent": False,
                "is_manual_mask": True,
                "file_path": file_path,
                "preview_path": preview_path,
                "shape_analysis": shape_analysis,
                "manual_polygon": polygon,
            },
        )

    except ValueError as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>⚠️ 영역 선택 오류</h3>'
            f'<p style="color:#856404;font-size:14px;">{str(e)}</p></div>',
            status_code=200,
        )
    except Exception as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>❌ 처리 오류</h3>'
            f'<p style="color:#c0392b;font-size:14px;">영역 분석 중 오류가 발생했습니다: {str(e)}</p></div>',
            status_code=200,
        )
