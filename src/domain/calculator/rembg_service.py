"""rembg 배경 제거 서비스 래퍼"""

import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# 모듈 레벨 세션 싱글톤 (모델 로딩 1회)
_session = None


def _get_session():
    """rembg 세션 싱글톤 반환 (첫 호출 시 모델 로딩)"""
    global _session
    if _session is None:
        from rembg import new_session

        logger.info("rembg 모델 로딩 중 (birefnet-general)...")
        _session = new_session("birefnet-general")
        logger.info("rembg 모델 로딩 완료")
    return _session


def preload_model() -> None:
    """앱 시작 시 모델 사전 로딩"""
    _get_session()


def remove_background(image_path: str | Path) -> tuple[np.ndarray, np.ndarray] | None:
    """
    rembg로 배경 제거하여 RGBA 이미지와 마스크 반환

    Args:
        image_path: 원본 이미지 경로

    Returns:
        (rgba_ndarray, mask_ndarray) 또는 실패 시 None
    """
    from rembg import remove

    image_path = Path(image_path)
    if not image_path.exists():
        return None

    try:
        # PIL로 이미지 열기
        pil_img = Image.open(image_path).convert("RGB")

        # rembg로 배경 제거
        session = _get_session()
        result = remove(pil_img, session=session)

        # PIL → numpy 변환 (RGBA)
        rgba = np.array(result)

        # RGBA → BGRA (OpenCV 호환)
        bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)

        # 알파 채널에서 마스크 추출
        mask = bgra[:, :, 3]
        _, mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

        return bgra, mask

    except Exception as e:
        logger.error("rembg 배경 제거 실패: %s", e)
        return None


def remove_background_to_mask(image_path: str | Path) -> np.ndarray | None:
    """
    배경 제거 후 마스크만 반환 (경량 버전)

    Args:
        image_path: 원본 이미지 경로

    Returns:
        이진 마스크 (0/255) 또는 실패 시 None
    """
    result = remove_background(image_path)
    if result is None:
        return None
    _, mask = result
    return mask


def save_mask(mask: np.ndarray, output_path: str | Path) -> bool:
    """마스크를 파일로 저장 (캐싱용)"""
    from src.domain.calculator.shape_analyzer import _imwrite_safe

    return _imwrite_safe(str(output_path), mask)


def load_mask(mask_path: str | Path) -> np.ndarray | None:
    """저장된 마스크 파일 로드"""
    from src.domain.calculator.shape_analyzer import _imread_safe

    mask = _imread_safe(str(mask_path), cv2.IMREAD_GRAYSCALE)
    return mask
