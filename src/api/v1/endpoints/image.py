"""이미지 처리 API - rembg 배경 제거 + 재단/인쇄 라인 자동 생성"""

import json
import logging
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
    analyze_from_mask,
    analyze_with_custom_mask,
    convert_to_mm,
    create_transparent_preview,
    create_preview_with_custom_mask,
    create_outline_preview,
    create_outline_with_custom_mask,
)
from src.domain.calculator.shape_pricing import ShapePricingService
from src.domain.calculator.rembg_service import (
    remove_background,
    save_mask,
    load_mask,
)
from src.domain.calculator.cutting_line_generator import (
    generate_cutting_lines,
    create_cutting_preview,
    get_cutting_metrics,
    get_keyring_size_addition_mm,
    get_drilling_fee,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image", tags=["image"])
templates = Jinja2Templates(directory="src/templates")

UPLOAD_DIR = Path("src/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MASK_DIR = UPLOAD_DIR / "masks"
MASK_DIR.mkdir(parents=True, exist_ok=True)


def _build_shape_analysis(
    metrics, pricing: ShapePricingService, drilling_fee: int = 0
) -> dict:
    """ShapeMetrics + ShapePricingService로 shape_analysis dict 생성"""
    price_info = pricing.calculate_shape_price(metrics, drilling_fee=drilling_fee)
    _, complexity_label = pricing.complexity_multiplier(metrics.complexity_score)
    return {
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
        "drilling_fee": price_info.get("drilling_fee", 0),
    }


@router.post("/upload", response_class=HTMLResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    target_size: Optional[float] = Form(None),
    target_dimension: str = Form("auto"),
    product_type: str = Form("objet"),
    keyring_position: str = Form("top"),
    hole_type: str = Form("ring"),
) -> HTMLResponse:
    """
    이미지 업로드 → rembg 배경 제거 → 재단/인쇄 라인 자동 생성 → 견적 산출

    Args:
        file: 업로드 이미지
        target_size: 목표 크기 (mm)
        target_dimension: 기준 방향 (width/height/auto)
        product_type: 제품 타입 (objet/keyring)
        keyring_position: 키링 고리/타공 위치 (top/bottom/left/right)
        hole_type: 타공 타입 (ring=고리형, internal=내부타공)
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
                if img.mode in ("RGBA", "LA") or (
                    img.mode == "P" and "transparency" in img.info
                ):
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    bbox = img.getbbox()
                    if bbox:
                        original_width = bbox[2] - bbox[0]
                        original_height = bbox[3] - bbox[1]
                        is_transparent = True
                    else:
                        original_width, original_height = img.size
                else:
                    original_width, original_height = img.size
        except Exception:
            import cv2
            cv_img = cv2.imread(str(temp_path), cv2.IMREAD_UNCHANGED)
            if cv_img is None:
                raise ValueError("이미지 파일을 읽을 수 없습니다. 다른 파일을 첨부해 주세요.")
            h, w = cv_img.shape[:2]
            original_width, original_height = w, h
            if len(cv_img.shape) == 3 and cv_img.shape[2] == 4:
                is_transparent = True

        # --- rembg 배경 제거 + 마스크 생성 ---
        rembg_mask = None
        rembg_used = False
        need_rembg = False

        # PNG: 먼저 알파 채널에서 마스크 추출 시도
        if ext == ".png" and is_transparent:
            import cv2
            from src.domain.calculator.shape_analyzer import _imread_safe
            png_img = _imread_safe(str(temp_path), cv2.IMREAD_UNCHANGED)
            if png_img is not None and len(png_img.shape) == 3 and png_img.shape[2] == 4:
                alpha = png_img[:, :, 3]
                _, alpha_mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)

                # 알파 마스크가 95% 이상이면 = 실질적 불투명(배경 제거 안 됨)
                fg_ratio = cv2.countNonZero(alpha_mask) / alpha_mask.size
                if fg_ratio < 0.95:
                    # 유효한 투명 배경 → 알파 마스크 사용
                    rembg_mask = alpha_mask
                    mask_filename = f"temp_{file.filename}_mask.png"
                    mask_path = MASK_DIR / mask_filename
                    save_mask(rembg_mask, str(mask_path))
                else:
                    # 실질적 불투명 PNG → rembg로 배경 제거 필요
                    logger.info("PNG 알파 마스크 fg_ratio=%.2f (거의 불투명) → rembg 시도", fg_ratio)
                    need_rembg = True
                    is_transparent = False  # 사실상 불투명

        # PNG 비투명 또는 JPG/BMP → rembg 배경 제거
        if ext == ".png" and not is_transparent:
            need_rembg = True
        if ext in [".jpg", ".jpeg", ".bmp"] and not is_transparent:
            need_rembg = True

        if need_rembg and rembg_mask is None:
            logger.info("rembg 배경 제거 시도: %s", file.filename)
            bg_result = remove_background(str(temp_path))
            if bg_result is not None:
                import cv2
                bgra, rembg_mask = bg_result
                rembg_used = True

                # 마스크 캐싱
                mask_filename = f"temp_{file.filename}_mask.png"
                mask_path = MASK_DIR / mask_filename
                save_mask(rembg_mask, str(mask_path))

                # rembg 마스크 기준 바운딩 박스로 크기 재계산
                contours, _ = cv2.findContours(
                    rembg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                if contours:
                    main_c = max(contours, key=cv2.contourArea)
                    _, _, obj_w, obj_h = cv2.boundingRect(main_c)
                    if obj_w > 0 and obj_h > 0:
                        original_width = obj_w
                        original_height = obj_h
                        is_transparent = True

                # 투명 미리보기 생성 (rembg 결과)
                from src.domain.calculator.shape_analyzer import _imwrite_safe
                preview_filename = f"temp_{file.filename}_preview.png"
                preview_output = UPLOAD_DIR / preview_filename
                _imwrite_safe(str(preview_output), bgra)

        # 비율 계산
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

        # --- 재단/인쇄 라인 생성 ---
        shape_analysis = None
        preview_path = None
        outline_path = None
        cutting_preview_path = None

        # 키링이면 drilling_fee 적용 (고리형/내부타공 모두)
        drilling_fee = get_drilling_fee() if product_type == "keyring" else 0

        if ext in [".jpg", ".jpeg", ".png", ".bmp"] and rembg_mask is not None:
            import cv2

            # 마스크 기준 형상 분석
            metrics = analyze_from_mask(rembg_mask)
            if metrics is not None:
                metrics = convert_to_mm(
                    metrics,
                    float(result.target_width),
                    float(result.target_height),
                )
                pricing = ShapePricingService()
                shape_analysis = _build_shape_analysis(
                    metrics, pricing, drilling_fee=drilling_fee
                )

                # 재단/인쇄 라인 생성
                h_px, w_px = rembg_mask.shape[:2]
                cutting_result = generate_cutting_lines(
                    mask=rembg_mask,
                    size_px=(w_px, h_px),
                    size_mm=(float(result.target_width), float(result.target_height)),
                    product_type=product_type,
                    keyring_position=keyring_position,
                    hole_type=hole_type,
                )

                if cutting_result is not None:
                    # 재단 라인 기준 메트릭으로 견적 업데이트
                    cutting_metrics = get_cutting_metrics(
                        cutting_result,
                        (float(result.target_width), float(result.target_height)),
                        (w_px, h_px),
                    )
                    shape_analysis["cutting_area_mm2"] = cutting_metrics["area_mm2"]
                    shape_analysis["cutting_perimeter_mm"] = cutting_metrics["perimeter_mm"]

                    # 고리형 키링: 고리 돌출만큼 전체 크기 증가 (내부 타공은 크기 변동 없음)
                    if product_type == "keyring" and hole_type == "ring":
                        w_add, h_add = get_keyring_size_addition_mm(keyring_position)
                        from src.domain.order.schemas import ImageRatioResponse
                        new_w = float(result.target_width) + w_add
                        new_h = float(result.target_height) + h_add
                        result = ImageRatioResponse(
                            original_width=result.original_width,
                            original_height=result.original_height,
                            target_width=round(new_w),
                            target_height=round(new_h),
                            ratio=round(result.ratio, 4),
                            target_dimension=result.target_dimension,
                        )

                    # 2겹 라인 미리보기 생성
                    cutting_preview_filename = f"temp_{file.filename}_cutting.png"
                    cutting_preview_output = UPLOAD_DIR / cutting_preview_filename
                    if create_cutting_preview(
                        str(temp_path), cutting_result, str(cutting_preview_output)
                    ):
                        cutting_preview_path = f"/static/uploads/{cutting_preview_filename}"

                # rembg로 배경 제거된 경우 투명 미리보기 경로
                if rembg_used:
                    preview_path = f"/static/uploads/temp_{file.filename}_preview.png"

        elif ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            # rembg 마스크 없는 경우 기존 OpenCV 분석 폴백
            metrics = analyze_image(str(temp_path))
            if metrics is not None:
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
                        is_transparent = True
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
                shape_analysis = _build_shape_analysis(metrics, pricing)

                if bg_removed:
                    preview_filename = f"temp_{file.filename}_preview.png"
                    preview_output = UPLOAD_DIR / preview_filename
                    if create_transparent_preview(str(temp_path), str(preview_output)):
                        preview_path = f"/static/uploads/{preview_filename}"

                outline_filename = f"temp_{file.filename}_outline.png"
                outline_output = UPLOAD_DIR / outline_filename
                is_rect = metrics.fill_ratio >= 0.95
                if create_outline_preview(str(temp_path), str(outline_output), is_rectangle=is_rect):
                    outline_path = f"/static/uploads/{outline_filename}"

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
                "outline_path": outline_path,
                "cutting_preview_path": cutting_preview_path,
                "shape_analysis": shape_analysis,
                "product_type": product_type,
                "hole_type": hole_type,
                "keyring_position": keyring_position,
                "rembg_used": rembg_used,
            },
        )

    except ValueError as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>입력 오류</h3>'
            f'<p style="color:#856404;font-size:14px;">{str(e)}</p></div>',
            status_code=200,
        )
    except Exception as e:
        logger.exception("이미지 처리 오류")
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>처리 오류</h3>'
            f'<p style="color:#c0392b;font-size:14px;">이미지 처리 중 오류가 발생했습니다: {str(e)}</p></div>',
            status_code=200,
        )


@router.post("/update-cutting-lines", response_class=HTMLResponse)
async def update_cutting_lines(
    request: Request,
    file_path: str = Form(...),
    target_width: float = Form(...),
    target_height: float = Form(...),
    product_type: str = Form("objet"),
    keyring_position: str = Form("top"),
    hole_type: str = Form("ring"),
) -> HTMLResponse:
    """
    키링 옵션 변경 시 캐싱된 마스크로 재단 라인만 재생성

    Args:
        file_path: 원본 이미지 static 경로
        target_width: 목표 가로 (mm)
        target_height: 목표 세로 (mm)
        product_type: 제품 타입
        keyring_position: 키링 고리/타공 위치
        hole_type: 타공 타입 (ring/internal)
    """
    try:
        import cv2

        # 파일 경로 복원
        decoded_path = unquote(file_path)
        filename = Path(decoded_path).name
        actual_path = UPLOAD_DIR / filename
        if not actual_path.exists():
            raise ValueError("이미지 파일을 찾을 수 없습니다")

        # 캐싱된 마스크 로드
        mask_filename = f"{filename}_mask.png"
        mask_path = MASK_DIR / mask_filename
        mask = load_mask(str(mask_path))
        if mask is None:
            raise ValueError("마스크 파일을 찾을 수 없습니다. 이미지를 다시 업로드해 주세요.")

        h_px, w_px = mask.shape[:2]

        # 마스크 기준 형상 분석
        metrics = analyze_from_mask(mask)
        if metrics is None:
            raise ValueError("형상 분석에 실패했습니다")

        metrics = convert_to_mm(metrics, target_width, target_height)
        drilling_fee = get_drilling_fee() if product_type == "keyring" else 0
        pricing = ShapePricingService()
        shape_analysis = _build_shape_analysis(
            metrics, pricing, drilling_fee=drilling_fee
        )

        # 재단/인쇄 라인 재생성
        cutting_result = generate_cutting_lines(
            mask=mask,
            size_px=(w_px, h_px),
            size_mm=(target_width, target_height),
            product_type=product_type,
            keyring_position=keyring_position,
            hole_type=hole_type,
        )

        cutting_preview_path = None
        if cutting_result is not None:
            cutting_metrics = get_cutting_metrics(
                cutting_result,
                (target_width, target_height),
                (w_px, h_px),
            )
            shape_analysis["cutting_area_mm2"] = cutting_metrics["area_mm2"]
            shape_analysis["cutting_perimeter_mm"] = cutting_metrics["perimeter_mm"]

            cutting_preview_filename = f"{filename}_cutting.png"
            cutting_preview_output = UPLOAD_DIR / cutting_preview_filename
            if create_cutting_preview(
                str(actual_path), cutting_result, str(cutting_preview_output)
            ):
                cutting_preview_path = f"/static/uploads/{cutting_preview_filename}"

        # 부분 HTML 반환 (미리보기 + 분석 결과만)
        return templates.TemplateResponse(
            "partials/cutting_preview.html",
            {
                "request": request,
                "cutting_preview_path": cutting_preview_path,
                "shape_analysis": shape_analysis,
                "product_type": product_type,
                "hole_type": hole_type,
                "keyring_position": keyring_position,
            },
        )

    except ValueError as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<p style="color:#856404;font-size:14px;">{str(e)}</p></div>',
            status_code=200,
        )
    except Exception as e:
        logger.exception("재단 라인 업데이트 오류")
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<p style="color:#c0392b;font-size:14px;">재단 라인 업데이트 오류: {str(e)}</p></div>',
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
        file_path: 업로드된 파일의 static 경로
        polygon: JSON 문자열 [[x,y],[x,y],...]
        target_width: 목표 가로 크기 (mm)
        target_height: 목표 세로 크기 (mm)
    """
    try:
        polygon_points = json.loads(polygon)
        if not polygon_points or len(polygon_points) < 3:
            raise ValueError("최소 3개 이상의 점이 필요합니다")

        decoded_path = unquote(file_path)
        filename = Path(decoded_path).name
        actual_path = UPLOAD_DIR / filename
        if not actual_path.exists():
            raise ValueError("이미지 파일을 찾을 수 없습니다")

        metrics = analyze_with_custom_mask(str(actual_path), polygon_points)
        if metrics is None:
            raise ValueError("선택한 영역을 분석할 수 없습니다. 다시 시도해주세요.")

        metrics = convert_to_mm(metrics, target_width, target_height)

        pricing = ShapePricingService()
        shape_analysis = _build_shape_analysis(metrics, pricing)

        preview_filename = f"{filename}_manual_preview.png"
        preview_output = UPLOAD_DIR / preview_filename
        preview_path = None
        if create_preview_with_custom_mask(
            str(actual_path), str(preview_output), polygon_points
        ):
            preview_path = f"/static/uploads/{preview_filename}"

        outline_filename = f"{filename}_manual_outline.png"
        outline_output = UPLOAD_DIR / outline_filename
        outline_path = None
        if create_outline_with_custom_mask(
            str(actual_path), str(outline_output), polygon_points
        ):
            outline_path = f"/static/uploads/{outline_filename}"

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
                "outline_path": outline_path,
                "shape_analysis": shape_analysis,
                "manual_polygon": polygon,
            },
        )

    except ValueError as e:
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>영역 선택 오류</h3>'
            f'<p style="color:#856404;font-size:14px;">{str(e)}</p></div>',
            status_code=200,
        )
    except Exception as e:
        logger.exception("수동 영역 분석 오류")
        return HTMLResponse(
            f'<div class="ratio-result-card ratio-error">'
            f'<h3>처리 오류</h3>'
            f'<p style="color:#c0392b;font-size:14px;">영역 분석 중 오류가 발생했습니다: {str(e)}</p></div>',
            status_code=200,
        )
