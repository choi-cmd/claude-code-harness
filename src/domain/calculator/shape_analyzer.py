"""OpenCV 기반 이미지 형상 분석기"""

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


def _imread_safe(path: str, flags: int = cv2.IMREAD_UNCHANGED) -> np.ndarray | None:
    """한글/특수문자 경로도 읽을 수 있는 imread (Windows 호환)"""
    img = cv2.imread(path, flags)
    if img is not None:
        return img
    # cv2.imread 실패 시 numpy 버퍼 경유
    try:
        buf = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(buf, flags)
    except Exception:
        return None


def _imwrite_safe(path: str, img: np.ndarray) -> bool:
    """한글/특수문자 경로에도 쓸 수 있는 imwrite (Windows 호환)"""
    try:
        result, buf = cv2.imencode(Path(path).suffix, img)
        if result:
            buf.tofile(path)
            return True
    except Exception:
        pass
    return False


@dataclass
class ShapeMetrics:
    """형상 측정 결과"""

    contour_area_px: float  # 실제 면적 (px²)
    contour_perimeter_px: float  # 아웃라인 길이 (px)
    bounding_box_px: tuple[int, int]  # 바운딩 박스 (w, h) px
    vertex_count: int  # 꼭짓점 수
    circularity: float  # 원형도 (0~1, 1=완전한 원)
    fill_ratio: float  # 채움률 (실제면적/바운딩박스면적)
    complexity_score: float  # 복잡도 점수 (0~1)

    # 복잡도 서브스코어 (각 0~1)
    outline_length_score: float = 0.0  # 아웃라인 길이 점수
    direction_change_score: float = 0.0  # 방향 전환 점수

    # mm 변환 값 (pixel_to_mm 호출 후 설정)
    area_mm2: float = 0.0
    perimeter_mm: float = 0.0
    bbox_width_mm: float = 0.0
    bbox_height_mm: float = 0.0


def analyze_from_mask(mask: np.ndarray) -> ShapeMetrics | None:
    """
    미리 생성된 마스크에서 형상 분석 (rembg 연동용)

    Args:
        mask: 이진 마스크 (0/255)

    Returns:
        ShapeMetrics 또는 실패 시 None
    """
    if mask is None or mask.size == 0:
        return None

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    return _analyze_contours(contours)


def analyze_image(image_path: str | Path) -> ShapeMetrics | None:
    """
    이미지에서 주요 형상을 분석하여 측정값 반환

    Args:
        image_path: 이미지 파일 경로

    Returns:
        ShapeMetrics 또는 분석 실패 시 None
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return None

    # 이미지 읽기 (알파 채널 포함)
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    h, w = img.shape[:2]
    has_alpha = len(img.shape) == 3 and img.shape[2] == 4

    if has_alpha:
        # PNG: 알파 채널로 정확한 마스크 생성
        mask = _create_mask(img)
    else:
        # JPG/BMP: 모서리 샘플링만 시도 (Otsu 폴백 사용 안 함)
        # 모서리 샘플링 실패 = 뚜렷한 배경 없음 = 이미지 전체가 사각형
        if len(img.shape) == 3:
            mask = _create_mask_by_corner_sampling(img)
        else:
            mask = None

        if mask is None:
            # 배경 분리 불가 → 사각형으로 처리
            return ShapeMetrics(
                contour_area_px=float(w * h),
                contour_perimeter_px=float(2 * (w + h)),
                bounding_box_px=(w, h),
                vertex_count=4,
                circularity=round(math.pi / 4, 4),
                fill_ratio=1.0,
                complexity_score=0.0,
            )

    if mask is None:
        return None

    # 컨투어 추출
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    return _analyze_contours(contours)


def _analyze_contours(contours: list) -> ShapeMetrics | None:
    """컨투어 목록에서 가장 큰 컨투어를 분석하여 ShapeMetrics 반환"""
    main_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(main_contour)
    if area < 100:
        return None

    perimeter = cv2.arcLength(main_contour, closed=True)
    x, y, w, h = cv2.boundingRect(main_contour)
    bbox_area = w * h

    # 꼭짓점 수 (Douglas-Peucker 근사)
    epsilon = 0.01 * perimeter
    approx = cv2.approxPolyDP(main_contour, epsilon, closed=True)
    vertex_count = len(approx)

    # 원형도: 4π × area / perimeter²
    circularity = (4 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
    circularity = min(circularity, 1.0)

    # 채움률
    fill_ratio = area / bbox_area if bbox_area > 0 else 0

    # 예각 비율 계산 (레이저 재단 시 감속 필요 구간)
    acute_ratio = _calculate_acute_ratio(approx)

    # 채움률이 95% 이상이면 사실상 사각형
    # → 사각형은 레이저 재단에서 가장 단순한 형상이므로 복잡도 0
    if fill_ratio > 0.95:
        vertex_count = 4
        circularity = math.pi / 4
        complexity = 0.0
        ol_score = 0.0
        dc_score = 0.0
    else:
        # 복잡도 점수 계산 (레이저 재단 기준)
        complexity, ol_score, dc_score = _calculate_complexity(
            vertex_count, perimeter, area, acute_ratio, main_contour
        )

    return ShapeMetrics(
        contour_area_px=area,
        contour_perimeter_px=perimeter,
        bounding_box_px=(w, h),
        vertex_count=vertex_count,
        circularity=round(circularity, 4),
        fill_ratio=round(fill_ratio, 4),
        complexity_score=round(complexity, 4),
        outline_length_score=round(ol_score, 4),
        direction_change_score=round(dc_score, 4),
    )


def _refine_mask_in_region(img: np.ndarray, region_mask: np.ndarray) -> np.ndarray:
    """
    사용자가 지정한 영역(region_mask) 안에서 실제 객체를 감지하여 정제된 마스크 반환.

    GrabCut 알고리즘으로 영역 내 전경/배경을 자동 분리한다.
    실패 시 원본 region_mask를 그대로 반환.
    """
    h, w = img.shape[:2]

    # GrabCut용 BGR 이미지 필요
    if len(img.shape) == 2:
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        bgr = img

    try:
        # GrabCut 마스크 초기화: 영역 밖=확실한 배경, 영역 안=아마도 전경
        gc_mask = np.full((h, w), cv2.GC_BGD, dtype=np.uint8)
        gc_mask[region_mask > 0] = cv2.GC_PR_FGD

        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        cv2.grabCut(bgr, gc_mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)

        # 전경 + 아마도 전경 = 최종 마스크
        refined = np.where(
            (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)

        # 정제 결과가 너무 작으면 (원래의 10% 미만) 원본 사용
        orig_area = np.count_nonzero(region_mask)
        refined_area = np.count_nonzero(refined)
        if refined_area < orig_area * 0.1:
            return region_mask

        # 모폴로지로 노이즈 정리
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel)

        return refined
    except Exception:
        return region_mask


def analyze_with_custom_mask(
    image_path: str | Path,
    polygon_points: list[list[int]],
) -> ShapeMetrics | None:
    """
    사용자 지정 폴리곤 내부에서 실제 객체를 감지하여 형상 분석.
    GrabCut으로 선택 영역 안의 실제 이미지를 인식해서 마스크를 정제한다.
    """
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    h, w = img.shape[:2]
    region_mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(polygon_points, dtype=np.int32)
    cv2.fillPoly(region_mask, [pts], 255)

    # 영역 내 객체 자동 감지로 마스크 정제
    refined_mask = _refine_mask_in_region(img, region_mask)

    contours, _ = cv2.findContours(refined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    return _analyze_contours(contours)


def create_preview_with_custom_mask(
    image_path: str | Path,
    output_path: str | Path,
    polygon_points: list[list[int]],
) -> bool:
    """
    사용자 지정 폴리곤 내부에서 실제 객체를 감지하여 투명 미리보기 PNG 생성.
    """
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return False

    h, w = img.shape[:2]
    region_mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(polygon_points, dtype=np.int32)
    cv2.fillPoly(region_mask, [pts], 255)

    # 영역 내 객체 자동 감지로 마스크 정제
    refined_mask = _refine_mask_in_region(img, region_mask)

    # BGR → BGRA
    if len(img.shape) == 3 and img.shape[2] == 4:
        bgra = img.copy()
    elif len(img.shape) == 3:
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    else:
        bgra = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)

    bgra[:, :, 3] = refined_mask
    _imwrite_safe(str(output_path), bgra)
    return True


def convert_to_mm(
    metrics: ShapeMetrics,
    target_width_mm: float,
    target_height_mm: float,
) -> ShapeMetrics:
    """
    픽셀 단위 측정값을 mm 단위로 변환

    Args:
        metrics: 픽셀 단위 측정 결과
        target_width_mm: 사용자 지정 목표 가로 크기 (mm)
        target_height_mm: 사용자 지정 목표 세로 크기 (mm)

    Returns:
        mm 값이 설정된 ShapeMetrics
    """
    bbox_w_px, bbox_h_px = metrics.bounding_box_px

    # 스케일 비율 (px → mm)
    scale_x = target_width_mm / bbox_w_px if bbox_w_px > 0 else 1
    scale_y = target_height_mm / bbox_h_px if bbox_h_px > 0 else 1
    scale = (scale_x + scale_y) / 2  # 평균 스케일

    metrics.area_mm2 = round(metrics.contour_area_px * scale * scale, 2)
    metrics.perimeter_mm = round(metrics.contour_perimeter_px * scale, 2)
    metrics.bbox_width_mm = round(target_width_mm, 2)
    metrics.bbox_height_mm = round(target_height_mm, 2)

    return metrics


def create_outline_preview(
    image_path: str | Path,
    output_path: str | Path,
    is_rectangle: bool = False,
) -> bool:
    """
    원본 이미지 위에 재단 아웃라인(커팅 경로)을 표시한 미리보기 생성.
    재단 영역 밖은 어둡게 처리하고, 빨간 선으로 커팅 경로를 표시한다.

    Args:
        image_path: 원본 이미지 경로
        output_path: 출력 PNG 경로
        is_rectangle: True이면 이미지 전체를 사각형 재단선으로 표시
    """
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return False

    h, w = img.shape[:2]

    # BGR 변환 (그리기용)
    if len(img.shape) == 2:
        draw_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        draw_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        draw_img = img.copy()

    if is_rectangle:
        mask = np.ones((h, w), dtype=np.uint8) * 255
        contour = np.array([[[0, 0]], [[w - 1, 0]], [[w - 1, h - 1]], [[0, h - 1]]])
    else:
        mask = _create_mask(img)
        if mask is None:
            return False
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        contour = max(contours, key=cv2.contourArea)

    # 재단 영역 밖 어둡게 (30% 밝기)
    mask_inv = cv2.bitwise_not(mask)
    draw_img[mask_inv > 0] = (draw_img[mask_inv > 0].astype(np.float32) * 0.3).astype(
        np.uint8
    )

    # 재단 아웃라인 빨간색으로 표시
    thickness = max(2, min(h, w) // 200)
    cv2.drawContours(draw_img, [contour], -1, (0, 0, 255), thickness)

    _imwrite_safe(str(output_path), draw_img)
    return True


def create_outline_with_custom_mask(
    image_path: str | Path,
    output_path: str | Path,
    polygon_points: list[list[int]],
) -> bool:
    """
    사용자 지정 영역의 정제된 아웃라인을 원본 이미지 위에 표시.
    """
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return False

    h, w = img.shape[:2]
    region_mask = np.zeros((h, w), dtype=np.uint8)
    pts = np.array(polygon_points, dtype=np.int32)
    cv2.fillPoly(region_mask, [pts], 255)

    refined_mask = _refine_mask_in_region(img, region_mask)

    contours, _ = cv2.findContours(refined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False
    contour = max(contours, key=cv2.contourArea)

    # BGR 변환
    if len(img.shape) == 2:
        draw_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        draw_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    else:
        draw_img = img.copy()

    # 재단 영역 밖 어둡게
    mask_inv = cv2.bitwise_not(refined_mask)
    draw_img[mask_inv > 0] = (draw_img[mask_inv > 0].astype(np.float32) * 0.3).astype(
        np.uint8
    )

    # 재단 아웃라인
    thickness = max(2, min(h, w) // 200)
    cv2.drawContours(draw_img, [contour], -1, (0, 0, 255), thickness)

    _imwrite_safe(str(output_path), draw_img)
    return True


def create_transparent_preview(image_path: str | Path, output_path: str | Path) -> bool:
    """
    JPG 등 불투명 이미지에서 배경을 제거한 투명 PNG 생성

    Args:
        image_path: 원본 이미지 경로
        output_path: 출력 PNG 경로

    Returns:
        성공 여부 (이미 투명이거나 실패 시 False)
    """
    img = _imread_safe(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return False

    # 이미 RGBA면 스킵
    if len(img.shape) == 3 and img.shape[2] == 4:
        return False

    mask = _create_mask(img)
    if mask is None:
        return False

    # BGR → BGRA (알파 채널로 마스크 적용)
    if len(img.shape) == 3:
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    else:
        bgra = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)

    bgra[:, :, 3] = mask
    _imwrite_safe(str(output_path), bgra)
    return True


def _create_mask(img: np.ndarray) -> np.ndarray | None:
    """이미지에서 전경 마스크 생성"""
    if img is None or img.size == 0:
        return None

    # RGBA (PNG 투명 배경)
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        return mask

    # RGB (JPG 등) - 모서리 배경색 샘플링 방식 시도
    if len(img.shape) == 3:
        mask = _create_mask_by_corner_sampling(img)
        if mask is not None:
            return mask

    # 폴백: 기존 Otsu 이진화
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 배경이 어두운 경우 반전
    white_ratio = np.count_nonzero(mask) / mask.size
    if white_ratio > 0.5:
        mask = cv2.bitwise_not(mask)

    return mask


def _create_mask_by_corner_sampling(img: np.ndarray) -> np.ndarray | None:
    """
    모서리 배경색 샘플링으로 배경 분리

    네 모서리의 10×10px 영역을 샘플링하여 가장 빈도 높은 색상을
    배경색으로 추정하고, 유클리드 거리 기반으로 배경/전경을 분리합니다.

    Args:
        img: BGR 이미지 (3채널)

    Returns:
        전경 마스크 또는 실패 시 None
    """
    h, w = img.shape[:2]
    sample_size = 10

    if h < sample_size * 2 or w < sample_size * 2:
        return None

    # 네 모서리 10×10px 영역 샘플링
    corners = [
        img[0:sample_size, 0:sample_size],                    # 좌상
        img[0:sample_size, w - sample_size:w],                # 우상
        img[h - sample_size:h, 0:sample_size],                # 좌하
        img[h - sample_size:h, w - sample_size:w],            # 우하
    ]

    # 모든 모서리 픽셀을 모아 최빈 색상 계산
    all_pixels = np.vstack([c.reshape(-1, 3) for c in corners])

    # 색상 양자화 (8단위)하여 최빈 배경색 추정
    quantized = (all_pixels // 8) * 8
    # 각 픽셀을 단일 정수로 변환하여 최빈값 계산
    pixel_keys = (
        quantized[:, 0].astype(np.int32) * 65536
        + quantized[:, 1].astype(np.int32) * 256
        + quantized[:, 2].astype(np.int32)
    )
    unique_keys, counts = np.unique(pixel_keys, return_counts=True)
    dominant_key = unique_keys[np.argmax(counts)]

    # 최빈 색상 복원
    bg_color = np.array([
        (dominant_key // 65536) & 0xFF,
        (dominant_key // 256) & 0xFF,
        dominant_key & 0xFF,
    ], dtype=np.float32)

    # 최빈 색상이 모서리 픽셀의 50% 이상이어야 배경색으로 신뢰
    dominant_ratio = np.max(counts) / len(pixel_keys)
    if dominant_ratio < 0.5:
        return None

    # 각 픽셀과 배경색의 유클리드 거리 계산
    img_float = img.astype(np.float32)
    diff = img_float - bg_color
    distance = np.sqrt(np.sum(diff * diff, axis=2))

    # 임계값 이내 = 배경 (0), 나머지 = 전경 (255)
    threshold = 35
    mask = np.where(distance > threshold, 255, 0).astype(np.uint8)

    # 모폴로지 연산으로 노이즈 제거
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # 작은 노이즈 제거
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 내부 구멍 메우기

    # 전경이 너무 적거나 너무 많으면 실패로 간주
    fg_ratio = np.count_nonzero(mask) / mask.size
    if fg_ratio < 0.01 or fg_ratio > 0.95:
        return None

    return mask


def _calculate_acute_ratio(approx_poly: np.ndarray) -> float:
    """
    근사 폴리곤에서 예각(90° 미만) 꼭짓점의 비율 계산.
    레이저 재단 시 예각 구간은 감속이 필요하여 난이도가 높다.

    Returns:
        예각 비율 (0~1)
    """
    pts = approx_poly.reshape(-1, 2)
    n = len(pts)
    if n < 3:
        return 0.0

    acute_count = 0
    for i in range(n):
        p1 = pts[(i - 1) % n].astype(float)
        p2 = pts[i].astype(float)
        p3 = pts[(i + 1) % n].astype(float)

        v1 = p1 - p2
        v2 = p3 - p2
        dot = np.dot(v1, v2)
        mag1 = np.linalg.norm(v1)
        mag2 = np.linalg.norm(v2)

        if mag1 == 0 or mag2 == 0:
            continue

        cos_angle = dot / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))
        angle_deg = math.degrees(math.acos(cos_angle))

        if angle_deg < 90:
            acute_count += 1

    return acute_count / n if n > 0 else 0.0


def _calculate_complexity(
    vertex_count: int,
    perimeter: float,
    area: float,
    acute_ratio: float,
    contour: np.ndarray,
) -> tuple[float, float, float]:
    """
    레이저 재단 복잡도 점수 (0~1) + 2기준별 서브스코어

    2가지 기준:
    - 아웃라인 길이 (50%): bbox 둘레 대비 실제 둘레 비율
    - 방향 전환 (50%): 꼭짓점 수 + 예각 비율 혼합

    Returns:
        (전체 복잡도, 아웃라인 길이 점수, 방향 전환 점수)
    """
    # 1. 아웃라인 길이 점수 - bbox 둘레 대비 실제 둘레 비율
    x, y, bw, bh = cv2.boundingRect(contour)
    bbox_perimeter = 2 * (bw + bh) if (bw + bh) > 0 else 1
    outline_ratio = perimeter / bbox_perimeter
    # bbox 둘레와 같으면(사각형) 0, 2배 이상이면 1
    outline_length_score = min(max((outline_ratio - 1.0) / 1.0, 0), 1)

    # 2. 방향 전환 점수 - 꼭짓점 수 + 예각 비율 혼합
    vertex_norm = min(max((vertex_count - 4) / 32, 0), 1)  # 36개 이상이어야 1 (기존 20개→36개)
    acute_norm = min(acute_ratio, 1.0)
    direction_change_score = vertex_norm * 0.6 + acute_norm * 0.4

    # 최종 점수
    score = (
        outline_length_score * 0.50
        + direction_change_score * 0.50
    )
    score = min(max(score, 0), 1)

    return score, outline_length_score, direction_change_score
