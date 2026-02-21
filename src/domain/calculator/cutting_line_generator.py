"""재단 라인 + 인쇄 라인 자동 생성 엔진"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from src.domain.calculator.shape_analyzer import _imread_safe, _imwrite_safe

CUTTING_CONFIG_PATH = Path("data/cutting_config.json")


def _smooth_contour(contour: np.ndarray, window: int = 15, passes: int = 2) -> np.ndarray:
    """컨투어 포인트에 이동 평균 적용 → 부드러운 곡선 (형태 보존)"""
    pts = contour.reshape(-1, 2).astype(np.float64)
    n = len(pts)
    if n < 30:
        return contour

    # 서브샘플링 (균일 간격)
    target = min(n, 400)
    if n > target:
        indices = np.linspace(0, n - 1, target, dtype=int)
        pts = pts[indices]
        n = len(pts)

    # 윈도우를 포인트 수 대비 ~8%로 제한
    w = min(window, max(5, n // 12)) | 1
    if n < w * 3:
        return contour

    half = w // 2
    for _ in range(passes):
        result = np.zeros_like(pts)
        for i in range(n):
            idx = [(i + j - half) % n for j in range(w)]
            result[i] = pts[idx].mean(axis=0)
        pts = result

    return pts.astype(np.int32).reshape(-1, 1, 2)


def _load_cutting_config() -> dict:
    """재단 설정 파일 로드"""
    if CUTTING_CONFIG_PATH.exists():
        return json.loads(CUTTING_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "print_offset_mm": 2.0,
        "cutting_offset_mm": 2.0,
        "smoothing_factor": 0.02,
        "keyring_hole": {
            "diameter_mm": 4.0,
            "edge_distance_mm": 3.0,
            "bridge_width_mm": 2.5,
        },
    }


@dataclass
class CuttingLineResult:
    """재단 라인 생성 결과"""

    # 컨투어 (OpenCV 형식)
    print_contour: np.ndarray  # 인쇄 라인 (마스크 + print_offset)
    cutting_contour: np.ndarray  # 재단 라인 (인쇄 라인 + cutting_offset)

    # 마스크
    print_mask: np.ndarray  # 인쇄 영역 마스크
    cutting_mask: np.ndarray  # 재단 영역 마스크

    # 고리/타공 정보 (키링인 경우)
    hole_center: tuple[int, int] | None = None
    hole_radius_px: int = 0
    hole_size_px: tuple[int, int] | None = None  # 내부 타공: (w, h) px
    bridge_contour: np.ndarray | None = None

    # 메타데이터
    product_type: str = "objet"  # objet or keyring
    hole_type: str = "ring"  # ring(고리형) or internal(내부 타공)
    keyring_position: str = "top"

    # 오프셋 정보 (px)
    print_offset_px: float = 0.0
    cutting_offset_px: float = 0.0


def get_keyring_size_addition_mm(position: str = "top") -> tuple[float, float]:
    """
    키링 고리로 인한 전체 크기 증가량 (mm)

    고리+브릿지가 재단 라인 밖으로 돌출되므로 전체 크기가 커진다.
    돌출량 = edge_distance + hole_diameter

    Args:
        position: 고리 위치 (top/bottom/left/right)

    Returns:
        (width_addition_mm, height_addition_mm)
    """
    config = _load_cutting_config()
    kh = config.get("keyring_hole", {})
    # 돌출량 = edge_distance + hole_radius + dome_radius
    tab_margin_mm = 1.0
    protrusion = kh.get("edge_distance_mm", 4.0) + kh.get("diameter_mm", 4.0) + tab_margin_mm

    if position in ("top", "bottom"):
        return (0.0, protrusion)
    else:  # left, right
        return (protrusion, 0.0)


def get_drilling_fee() -> int:
    """타공 비용 (원) 반환"""
    config = _load_cutting_config()
    return config.get("drilling_fee", 100)


def get_internal_hole_size_mm() -> tuple[float, float]:
    """내부 타공 크기 (mm) 반환 → (width, height)"""
    config = _load_cutting_config()
    ih = config.get("internal_hole", {})
    return (ih.get("width_mm", 3.214), ih.get("height_mm", 3.168))


def generate_offset_contour(
    mask: np.ndarray,
    offset_px: float,
    smoothing_factor: float = 0.02,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """
    마스크에서 오프셋된 컨투어와 마스크 생성

    Args:
        mask: 원본 이진 마스크 (0/255)
        offset_px: 오프셋 크기 (px)
        smoothing_factor: 스무딩 계수 (epsilon = factor * perimeter)

    Returns:
        (offset_contour, offset_mask) 또는 실패 시 (None, None)
    """
    if mask is None or offset_px <= 0:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, None
        main = max(contours, key=cv2.contourArea)
        return main, mask.copy()

    h, w = mask.shape[:2]

    # 1단계: 원본 마스크 사전 스무딩 (돌기/노이즈 제거 → 부드러운 윤곽)
    # 블러 후 dilate하면 오프셋 거리가 정확하게 유지됨
    pre_blur = max(7, min(h, w) // 60) | 1
    pre_smoothed = cv2.GaussianBlur(mask, (pre_blur, pre_blur), 0)
    _, pre_smoothed = cv2.threshold(pre_smoothed, 127, 255, cv2.THRESH_BINARY)

    # 2단계: dilate로 오프셋 확장
    kernel_size = max(3, int(offset_px * 2) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    iterations = max(1, int(math.ceil(offset_px / (kernel_size / 2))))
    expanded = cv2.dilate(pre_smoothed, kernel, iterations=iterations)

    # 3단계: 가벼운 엣지 블러 (오프셋 거리를 밀지 않음)
    edge_blur = max(3, int(offset_px * 0.5)) | 1
    smoothed = cv2.GaussianBlur(expanded, (edge_blur, edge_blur), 0)
    _, smoothed = cv2.threshold(smoothed, 127, 255, cv2.THRESH_BINARY)

    # 컨투어 추출
    contours, _ = cv2.findContours(smoothed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None

    main_contour = max(contours, key=cv2.contourArea)

    # 스무딩된 마스크 생성
    offset_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.drawContours(offset_mask, [main_contour], -1, 255, -1)

    return main_contour, offset_mask


def _calculate_keyring_hole(
    cutting_contour: np.ndarray,
    position: str,
    hole_diameter_px: float,
    edge_distance_px: float,
) -> tuple[tuple[int, int], int]:
    """
    키링 고리 구멍 위치 계산

    Returns:
        (hole_center, hole_radius)
    """
    x, y, bw, bh = cv2.boundingRect(cutting_contour)
    hole_r = int(hole_diameter_px / 2)
    dist = int(edge_distance_px)

    if position == "top":
        cx, cy = x + bw // 2, y - dist - hole_r
    elif position == "bottom":
        cx, cy = x + bw // 2, y + bh + dist + hole_r
    elif position == "left":
        cx, cy = x - dist - hole_r, y + bh // 2
    elif position == "right":
        cx, cy = x + bw + dist + hole_r, y + bh // 2
    else:
        cx, cy = x + bw // 2, y - dist - hole_r

    return (cx, cy), hole_r


def _calculate_internal_hole(
    cutting_contour: np.ndarray,
    cutting_mask: np.ndarray,
    position: str,
    hole_w_px: float,
    hole_h_px: float,
    edge_distance_px: float,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    내부 타공 위치 계산 (재단 라인 내부에 구멍)

    Args:
        cutting_contour: 재단 라인 컨투어
        cutting_mask: 재단 영역 마스크
        position: 타공 위치 (top/bottom/left/right)
        hole_w_px: 타공 가로 크기 (px)
        hole_h_px: 타공 세로 크기 (px)
        edge_distance_px: 재단 라인 가장자리로부터 타공 중심까지 거리 (px)

    Returns:
        (hole_center, hole_size_px)
    """
    h, w = cutting_mask.shape[:2]
    x, y, bw, bh = cv2.boundingRect(cutting_contour)

    hw = int(hole_w_px / 2)
    hh = int(hole_h_px / 2)
    dist = int(edge_distance_px)

    # 위치별 타공 중심 계산 (재단 라인 안쪽)
    if position == "top":
        cx = x + bw // 2
        cy = y + dist
    elif position == "bottom":
        cx = x + bw // 2
        cy = y + bh - dist
    elif position == "left":
        cx = x + dist
        cy = y + bh // 2
    elif position == "right":
        cx = x + bw - dist
        cy = y + bh // 2
    else:
        cx = x + bw // 2
        cy = y + dist

    # 이미지 범위 내로 클램프
    cx = max(hw + 2, min(w - hw - 2, cx))
    cy = max(hh + 2, min(h - hh - 2, cy))

    hole_center = (cx, cy)
    hole_size = (int(hole_w_px), int(hole_h_px))

    return hole_center, hole_size


def generate_cutting_lines(
    mask: np.ndarray,
    size_px: tuple[int, int],
    size_mm: tuple[float, float],
    product_type: str = "objet",
    keyring_position: str = "top",
    hole_type: str = "ring",
) -> CuttingLineResult | None:
    """
    마스크에서 인쇄 라인 + 재단 라인 생성

    Args:
        mask: 배경 제거된 이진 마스크 (0/255)
        size_px: 이미지 크기 (w, h) px
        size_mm: 목표 크기 (w, h) mm
        product_type: "objet" 또는 "keyring"
        keyring_position: 키링 고리/타공 위치 ("top"/"bottom"/"left"/"right")
        hole_type: "ring"(고리형 외부돌출) 또는 "internal"(내부 타공)

    Returns:
        CuttingLineResult 또는 실패 시 None
    """
    config = _load_cutting_config()
    print_offset_mm = config.get("print_offset_mm", 2.0)
    cutting_offset_mm = config.get("cutting_offset_mm", 2.0)
    smoothing = config.get("smoothing_factor", 0.02)

    w_px, h_px = size_px
    w_mm, h_mm = size_mm

    # px/mm 스케일 계산
    scale_x = w_px / w_mm if w_mm > 0 else 1
    scale_y = h_px / h_mm if h_mm > 0 else 1
    scale = (scale_x + scale_y) / 2

    # mm → px 변환
    print_offset_px = print_offset_mm * scale
    cutting_offset_px = cutting_offset_mm * scale

    # 1단계: 인쇄 라인 (원본 마스크 + print_offset)
    print_contour, print_mask = generate_offset_contour(
        mask, print_offset_px, smoothing
    )
    if print_contour is None:
        return None

    # 2단계: 재단 라인 (인쇄 마스크 + cutting_offset)
    cutting_contour, cutting_mask = generate_offset_contour(
        print_mask, cutting_offset_px, smoothing
    )
    if cutting_contour is None:
        return None

    result = CuttingLineResult(
        print_contour=print_contour,
        cutting_contour=cutting_contour,
        print_mask=print_mask,
        cutting_mask=cutting_mask,
        product_type=product_type,
        hole_type=hole_type,
        keyring_position=keyring_position,
        print_offset_px=print_offset_px,
        cutting_offset_px=cutting_offset_px,
    )

    # 키링이면 타공 추가
    if product_type == "keyring":
        if hole_type == "internal":
            # 내부 타공: 재단 라인 내부에 구멍
            ih_cfg = config.get("internal_hole", {})
            hole_w_px = ih_cfg.get("width_mm", 3.214) * scale
            hole_h_px = ih_cfg.get("height_mm", 3.168) * scale
            edge_d_px = ih_cfg.get("edge_distance_mm", 5.0) * scale

            hole_center, hole_size = _calculate_internal_hole(
                cutting_contour,
                cutting_mask,
                keyring_position,
                hole_w_px,
                hole_h_px,
                edge_d_px,
            )
            result.hole_center = hole_center
            result.hole_size_px = hole_size
            # 원형에 가까우므로 radius = 평균 반지름
            result.hole_radius_px = int((hole_size[0] + hole_size[1]) / 4)

            # 내부 타공을 재단 마스크에서 제거 (타원)
            axes = (hole_size[0] // 2, hole_size[1] // 2)
            cv2.ellipse(cutting_mask, hole_center, axes, 0, 0, 360, 0, -1)
            result.cutting_mask = cutting_mask

        else:
            # 고리형: 외부 돌출 (미리보기에서 탭 형태로 표시)
            keyring_cfg = config.get("keyring_hole", {})
            hole_d_px = keyring_cfg.get("diameter_mm", 4.0) * scale
            edge_d_px = keyring_cfg.get("edge_distance_mm", 4.0) * scale

            hole_center, hole_r = _calculate_keyring_hole(
                cutting_contour,
                keyring_position,
                hole_d_px,
                edge_d_px,
            )
            result.hole_center = hole_center
            result.hole_radius_px = hole_r

    return result


def create_cutting_preview(
    image_path: str,
    result: CuttingLineResult,
    output_path: str,
    size_mm: tuple[float, float] | None = None,
) -> bool:
    """
    예시 이미지 스타일 미리보기 생성

    - 2배 해상도 렌더링 → 얇고 깔끔한 선
    - 흰 배경 + 원본 이미지 알파 합성
    - 고리형 키링: 둥근 캡슐형 탭 + 구멍
    """
    config = _load_cutting_config()

    img = _imread_safe(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(image_path)
            if pil_img.mode in ("RGBA", "LA"):
                pil_img = pil_img.convert("RGBA")
                arr = np.array(pil_img)
                img = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
            else:
                pil_img = pil_img.convert("RGB")
                arr = np.array(pil_img)
                img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception:
            return False

    h, w = img.shape[:2]

    # 2배 해상도 스케일 (예시 이미지 품질에 맞추기)
    S = 2

    # BGR + 알파 추출 → 2x 업스케일
    if len(img.shape) == 2:
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        alpha = np.full((h, w), 255, dtype=np.uint8)
    elif img.shape[2] == 4:
        bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        alpha = img[:, :, 3]
    else:
        bgr = img.copy()
        alpha = np.full((h, w), 255, dtype=np.uint8)

    bgr = cv2.resize(bgr, (w * S, h * S), interpolation=cv2.INTER_LANCZOS4)
    alpha = cv2.resize(alpha, (w * S, h * S), interpolation=cv2.INTER_LANCZOS4)
    sh, sw = h * S, w * S

    # 마스크 2x 업스케일 (LINEAR + threshold → 부드러운 엣지)
    cutting_mask_s = cv2.resize(result.cutting_mask, (w * S, h * S), interpolation=cv2.INTER_LINEAR)
    _, cutting_mask_s = cv2.threshold(cutting_mask_s, 127, 255, cv2.THRESH_BINARY)

    # px/mm 스케일 (2x 캔버스 기준)
    px_per_mm = sw / size_mm[0] if (size_mm and size_mm[0] > 0) else max(sh, sw) / 60.0

    # 여백 계산 (2x 기준)
    base_pad = int(max(sh, sw) * 0.06)
    # 사이즈 텍스트용 하단 여백 추가
    text_pad = int(max(sh, sw) * 0.08) if size_mm is not None else 0
    extra_pad = [0, text_pad, 0, 0]  # top, bottom, left, right

    is_ring = (
        result.product_type == "keyring"
        and result.hole_type != "internal"
        and result.hole_center is not None
    )

    if is_ring:
        kh_cfg = config.get("keyring_hole", {})
        protrusion_mm = kh_cfg.get("edge_distance_mm", 1.5) + kh_cfg.get("diameter_mm", 2.0) + 1.5
        extra_px = max(int(protrusion_mm * px_per_mm), int(max(sh, sw) * 0.12))
        pos_map = {"top": 0, "bottom": 1, "left": 2, "right": 3}
        extra_pad[pos_map.get(result.keyring_position, 0)] = extra_px

    pt = base_pad + extra_pad[0]
    pb = base_pad + extra_pad[1]
    pl = base_pad + extra_pad[2]
    pr = base_pad + extra_pad[3]
    new_h = sh + pt + pb
    new_w = sw + pl + pr
    ox, oy = pl, pt

    # 흰색 배경 캔버스
    canvas = np.full((new_h, new_w, 3), 255, dtype=np.uint8)

    # 원본 이미지 알파 합성
    alpha_f = alpha.astype(np.float32) / 255.0
    for c in range(3):
        canvas[oy : oy + sh, ox : ox + sw, c] = (
            bgr[:, :, c].astype(np.float32) * alpha_f
            + 255.0 * (1.0 - alpha_f)
        ).astype(np.uint8)

    # 선 두께 (2x 해상도에서 1-2px = 원본 대비 ~0.5-1px)
    thin = max(1, min(new_h, new_w) // 600)

    # 2x 좌표 변환
    def s_point(p: tuple[int, int]) -> tuple[int, int]:
        return (p[0] * S + ox, p[1] * S + oy)

    def s_contour(contour: np.ndarray) -> np.ndarray:
        c = contour.copy()
        if c.ndim == 3:
            c[:, :, 0] = c[:, :, 0] * S + ox
            c[:, :, 1] = c[:, :, 1] * S + oy
        return c

    # 색상 (실제 결과물과 동일하게 빨간색 단일 라인)
    line_color = (0, 0, 230)       # 빨간색 (BGR)

    def _smooth_mask(mask_2d: np.ndarray) -> np.ndarray:
        """마스크 외곽선 스무딩 (GaussianBlur → 모서리 라운딩, 형태 보존)

        이동 평균 방식과 달리 GaussianBlur는 전체 형태를 왜곡하지 않으면서
        각진 모서리만 부드럽게 만든다. 인쇄 라인이 재단 라인을 넘지 않음.
        """
        mh, mw = mask_2d.shape[:2]
        # 이미지 크기 대비 ~3% 블러 → 모서리 라운딩 (예시처럼 둥근 모서리)
        blur_k = max(11, min(mh, mw) // 35) | 1
        smoothed = cv2.GaussianBlur(mask_2d, (blur_k, blur_k), 0)
        _, smoothed = cv2.threshold(smoothed, 127, 255, cv2.THRESH_BINARY)
        return smoothed

    def _mask_outline(mask_2d: np.ndarray, color: tuple, lw: int = 1, smooth: bool = True) -> None:
        """마스크의 외곽선을 캔버스에 그리기 (스무딩 옵션)"""
        if smooth:
            mask_2d = _smooth_mask(mask_2d)
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(mask_2d, kernel, iterations=lw)
        outline = cv2.bitwise_xor(mask_2d, eroded)
        canvas[outline > 0] = color

    # --- 캔버스 좌표 마스크 준비 (재단 라인만 표시) ---
    cutting_cv = np.zeros((new_h, new_w), dtype=np.uint8)
    cutting_cv[oy : oy + sh, ox : ox + sw] = cutting_mask_s

    if is_ring:
        hc = s_point(result.hole_center)
        hole_r_s = result.hole_radius_px * S

        # 돔: 정상(3) 기준 돔 외경 ≈ 5.1mm (구멍 3.2mm + 양쪽 ~1mm)
        tab_margin_px = max(3, int(1.0 * px_per_mm))
        tab_r = hole_r_s + tab_margin_px

        # 탭 마스크: 돔 원 + 브릿지 (돔 폭 그대로 → 목 없음)
        tab_mask = np.zeros((new_h, new_w), dtype=np.uint8)
        cv2.circle(tab_mask, hc, tab_r, 255, -1)

        # 브릿지: 돔 폭 그대로 본체까지 직선 연결
        bridge_half = tab_r
        sc = s_contour(result.cutting_contour)
        sbx, sby, sbw, sbh = cv2.boundingRect(sc)
        overlap = max(sbh // 4, bridge_half * 2)  # 본체 깊숙이 겹침

        if result.keyring_position == "top":
            cv2.rectangle(tab_mask, (hc[0] - bridge_half, hc[1]), (hc[0] + bridge_half, sby + overlap), 255, -1)
        elif result.keyring_position == "bottom":
            cv2.rectangle(tab_mask, (hc[0] - bridge_half, sby + sbh - overlap), (hc[0] + bridge_half, hc[1]), 255, -1)
        elif result.keyring_position == "left":
            cv2.rectangle(tab_mask, (hc[0], hc[1] - bridge_half), (sbx + overlap, hc[1] + bridge_half), 255, -1)
        elif result.keyring_position == "right":
            cv2.rectangle(tab_mask, (sbx + sbw - overlap, hc[1] - bridge_half), (hc[0], hc[1] + bridge_half), 255, -1)

        # 돔 블러 → 둥근 꼭대기
        blur_k = max(5, int(tab_r * 0.4)) | 1
        tab_mask = cv2.GaussianBlur(tab_mask, (blur_k, blur_k), 0)
        _, tab_mask = cv2.threshold(tab_mask, 127, 255, cv2.THRESH_BINARY)

        # 합성
        combined = cv2.bitwise_or(cutting_cv, tab_mask)

        # 모폴로지 클로징 → 접합부 안쪽 코너만 둥글게 (돔 바깥쪽은 보존)
        close_k = max(5, int(tab_r * 0.7)) | 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_k, close_k))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        # 가벼운 블러 → 전체 윤곽 부드럽게
        smooth_k = max(5, int(tab_r * 0.4)) | 1
        combined = cv2.GaussianBlur(combined, (smooth_k, smooth_k), 0)
        _, combined = cv2.threshold(combined, 127, 255, cv2.THRESH_BINARY)

        # 구멍 뚫기
        cv2.circle(combined, hc, hole_r_s, 0, -1)

        # 외곽선 (이미 스무딩 완료 → smooth=False로 추가 블러 방지)
        _mask_outline(combined, line_color, thin, smooth=False)
        hole_m = np.zeros((new_h, new_w), dtype=np.uint8)
        cv2.circle(hole_m, hc, hole_r_s, 255, -1)
        _mask_outline(hole_m, line_color, thin, smooth=False)
    else:
        _mask_outline(cutting_cv, line_color, thin)

    # 내부 타공 표시
    if (
        result.product_type == "keyring"
        and result.hole_type == "internal"
        and result.hole_center is not None
        and result.hole_size_px is not None
    ):
        hc = s_point(result.hole_center)
        axes = (result.hole_size_px[0] * S // 2, result.hole_size_px[1] * S // 2)
        hole_m = np.zeros((new_h, new_w), dtype=np.uint8)
        cv2.ellipse(hole_m, hc, axes, 0, 0, 360, 255, -1)
        _mask_outline(hole_m, line_color, thin, smooth=False)

    # 사이즈 표기 (실제 결과물처럼 하단 중앙에 빨간 텍스트)
    if size_mm is not None:
        w_mm, h_mm = size_mm
        # 소수점: 정수면 생략, 아니면 1자리
        def _fmt(v: float) -> str:
            return f"{int(v)}" if v == int(v) else f"{v:.1f}"
        size_text = f"{_fmt(w_mm)}\u00d7{_fmt(h_mm)}mm"

        try:
            from PIL import Image as PILImage, ImageDraw, ImageFont

            pil_canvas = PILImage.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_canvas)
            font_size = max(18, min(new_h, new_w) // 18)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                try:
                    font = ImageFont.truetype("malgun.ttf", font_size)
                except Exception:
                    font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), size_text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (new_w - tw) // 2
            ty = new_h - base_pad // 2 - th // 2
            draw.text((tx, ty), size_text, fill=(230, 0, 0), font=font)
            canvas = cv2.cvtColor(np.array(pil_canvas), cv2.COLOR_RGB2BGR)
        except ImportError:
            pass

    return _imwrite_safe(output_path, canvas)


def get_cutting_metrics(
    result: CuttingLineResult,
    size_mm: tuple[float, float],
    size_px: tuple[int, int],
) -> dict:
    """
    재단 라인 기준 메트릭 계산 (견적용)

    Args:
        result: CuttingLineResult
        size_mm: 목표 크기 (w, h) mm
        size_px: 이미지 크기 (w, h) px

    Returns:
        재단 라인 기준 면적/둘레/복잡도 등
    """
    w_px, h_px = size_px
    w_mm, h_mm = size_mm
    scale_x = w_mm / w_px if w_px > 0 else 1
    scale_y = h_mm / h_px if h_px > 0 else 1
    scale = (scale_x + scale_y) / 2

    # 재단 컨투어 기준 메트릭
    cutting_area_px = cv2.contourArea(result.cutting_contour)
    cutting_perimeter_px = cv2.arcLength(result.cutting_contour, closed=True)
    cx, cy, cw, ch = cv2.boundingRect(result.cutting_contour)

    area_mm2 = cutting_area_px * scale * scale
    perimeter_mm = cutting_perimeter_px * scale

    return {
        "area_mm2": round(area_mm2, 2),
        "perimeter_mm": round(perimeter_mm, 2),
        "cutting_bbox_px": (cw, ch),
        "cutting_bbox_mm": (round(cw * scale, 2), round(ch * scale, 2)),
    }
