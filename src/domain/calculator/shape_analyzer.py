"""OpenCV 기반 이미지 형상 분석기"""

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


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

    # mm 변환 값 (pixel_to_mm 호출 후 설정)
    area_mm2: float = 0.0
    perimeter_mm: float = 0.0
    bbox_width_mm: float = 0.0
    bbox_height_mm: float = 0.0


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
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    # 마스크 생성
    mask = _create_mask(img)
    if mask is None:
        return None

    # 컨투어 추출
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # 가장 큰 컨투어 선택 (주요 형상)
    main_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(main_contour)
    if area < 100:  # 너무 작은 컨투어 무시
        return None

    perimeter = cv2.arcLength(main_contour, closed=True)
    x, y, w, h = cv2.boundingRect(main_contour)
    bbox_area = w * h

    # 꼭짓점 수 (Douglas-Peucker 근사)
    epsilon = 0.01 * perimeter
    approx = cv2.approxPolyDP(main_contour, epsilon, closed=True)
    vertex_count = len(approx)

    # 원형도: 4π × area / perimeter²  (원=1, 복잡할수록 0에 가까움)
    circularity = (4 * math.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
    circularity = min(circularity, 1.0)

    # 채움률
    fill_ratio = area / bbox_area if bbox_area > 0 else 0

    # 복잡도 점수 계산
    complexity = _calculate_complexity(circularity, vertex_count, perimeter, area)

    return ShapeMetrics(
        contour_area_px=area,
        contour_perimeter_px=perimeter,
        bounding_box_px=(w, h),
        vertex_count=vertex_count,
        circularity=round(circularity, 4),
        fill_ratio=round(fill_ratio, 4),
        complexity_score=round(complexity, 4),
    )


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


def _create_mask(img: np.ndarray) -> np.ndarray | None:
    """이미지에서 전경 마스크 생성"""
    if img is None or img.size == 0:
        return None

    # RGBA (PNG 투명 배경)
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        return mask

    # 그레이스케일 변환
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # Otsu 이진화 (배경과 전경 자동 분리)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 배경이 어두운 경우 반전
    white_ratio = np.count_nonzero(mask) / mask.size
    if white_ratio > 0.5:
        mask = cv2.bitwise_not(mask)

    return mask


def _calculate_complexity(
    circularity: float,
    vertex_count: int,
    perimeter: float,
    area: float,
) -> float:
    """
    형상 복잡도 점수 산출 (0~1)

    3가지 요소의 가중 합산:
    - 원형도 반전 (복잡할수록 높음) : 40%
    - 꼭짓점 밀도 : 30%
    - 둘레/면적 비율 : 30%
    """
    # 1. 원형도 반전 (원형=0, 복잡=1)
    complexity_circularity = 1.0 - circularity

    # 2. 꼭짓점 밀도 (4~50개 범위로 정규화)
    vertex_norm = min(max((vertex_count - 4) / 46, 0), 1)

    # 3. 둘레/면적 비율 (높을수록 복잡)
    if area > 0:
        # 원의 둘레/면적 비율을 기준으로 정규화
        # 원: perimeter/sqrt(area) = 2*sqrt(pi) ≈ 3.545
        ratio = perimeter / math.sqrt(area)
        pa_norm = min(max((ratio - 3.545) / 10, 0), 1)
    else:
        pa_norm = 0

    score = (
        complexity_circularity * 0.4
        + vertex_norm * 0.3
        + pa_norm * 0.3
    )
    return min(max(score, 0), 1)
