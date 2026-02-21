"""형상 기반 가격 계산 서비스"""

import json
import math
from pathlib import Path

from src.domain.calculator.shape_analyzer import ShapeMetrics

PRICING_CONFIG_PATH = Path("data/pricing_config.json")


def _load_config() -> dict:
    """가격 설정 파일 로드"""
    if PRICING_CONFIG_PATH.exists():
        return json.loads(PRICING_CONFIG_PATH.read_text(encoding="utf-8"))
    # 기본값
    return {
        "material_rate": 0.07,
        "processing_rate": 1.86,
        "margin": 2.98,
    }


class ShapePricingService:
    """형상 기반 가격 계산 서비스"""

    # 아크릴 판 사양 (CalculatorService와 동일)
    PANEL_WIDTH = 406.4  # mm
    PANEL_HEIGHT = 609.6  # mm
    MARGIN = 5  # mm
    SAMPLE_FEE = 10000  # 원

    def __init__(self) -> None:
        self.config = _load_config()

    def complexity_multiplier(self, complexity_score: float) -> tuple[float, str]:
        """
        복잡도 점수 → 할증 계수 + 등급 라벨

        Args:
            complexity_score: 0~1 복잡도 점수

        Returns:
            (할증 계수, 등급 라벨)
        """
        levels = self.config.get("complexity_levels", {})
        for level in ["low", "normal", "high", "very_high"]:
            info = levels.get(level, {})
            if complexity_score <= info.get("max_score", 1.0):
                return info.get("multiplier", 1.0), info.get("label", level)
        return 1.4, "매우 복잡"

    def fill_efficiency_surcharge(self, fill_ratio: float) -> tuple[float, str]:
        """
        채움률 → 효율 할증 계수 + 등급 라벨

        Args:
            fill_ratio: 0~1 채움률

        Returns:
            (효율 계수, 등급 라벨)
        """
        levels = self.config.get("efficiency_levels", {})
        for level in ["excellent", "good", "fair", "poor"]:
            info = levels.get(level, {})
            if fill_ratio >= info.get("min_fill", 0):
                return info.get("surcharge", 1.0), info.get("label", level)
        return 1.35, "비효율"

    def calculate_shape_price(
        self, metrics: ShapeMetrics, drilling_fee: int = 0
    ) -> dict:
        """
        형상 기반 가격 계산

        Args:
            metrics: mm 변환이 완료된 ShapeMetrics
            drilling_fee: 타공 비용 (키링 고리 등, 기본 0원)

        Returns:
            상세 견적 정보 dict
        """
        material_rate = self.config.get("material_rate", 0.07)
        processing_rate = self.config.get("processing_rate", 1.86)
        margin = self.config.get("margin", 2.98)

        # 재료비 = 실제 면적 × 단가
        material_cost = metrics.area_mm2 * material_rate
        # 가공비 = 아웃라인 길이 × 단가
        processing_cost = metrics.perimeter_mm * processing_rate

        # 복잡도 계수
        complexity_mult, complexity_label = self.complexity_multiplier(
            metrics.complexity_score
        )
        # 효율 계수
        efficiency_mult, efficiency_label = self.fill_efficiency_surcharge(
            metrics.fill_ratio
        )

        # 최종 단가
        raw_price = (
            (material_cost + processing_cost)
            * complexity_mult
            * efficiency_mult
            * margin
        )
        unit_price = int(math.ceil(raw_price / 10) * 10) + drilling_fee

        return {
            "material_cost": round(material_cost, 1),
            "processing_cost": round(processing_cost, 1),
            "complexity_multiplier": complexity_mult,
            "complexity_label": complexity_label,
            "complexity_score": metrics.complexity_score,
            "outline_length_score": metrics.outline_length_score,
            "direction_change_score": metrics.direction_change_score,
            "outline_length_pct": round(metrics.outline_length_score * 100, 1),
            "direction_change_pct": round(metrics.direction_change_score * 100, 1),
            "efficiency_multiplier": efficiency_mult,
            "efficiency_label": efficiency_label,
            "fill_ratio": metrics.fill_ratio,
            "margin": margin,
            "drilling_fee": drilling_fee,
            "unit_price": unit_price,
            "area_mm2": metrics.area_mm2,
            "perimeter_mm": metrics.perimeter_mm,
            "bbox_width_mm": metrics.bbox_width_mm,
            "bbox_height_mm": metrics.bbox_height_mm,
        }

    def calculate_min_quantity(
        self, width: float, height: float
    ) -> tuple[int, str]:
        """1판 최소 수량 계산 (CalculatorService와 동일 로직)"""
        actual_w = width + (self.MARGIN * 2)
        actual_h = height + (self.MARGIN * 2)

        cols1 = math.floor(self.PANEL_WIDTH / actual_w)
        rows1 = math.floor(self.PANEL_HEIGHT / actual_h)
        count1 = cols1 * rows1

        cols2 = math.floor(self.PANEL_WIDTH / actual_h)
        rows2 = math.floor(self.PANEL_HEIGHT / actual_w)
        count2 = cols2 * rows2

        if count1 >= count2:
            return count1, f"{cols1}개 x {rows1}개 배치"
        return count2, f"{cols2}개 x {rows2}개 배치 (90도 회전)"

    def full_quote(
        self, metrics: ShapeMetrics, quantity: int, drilling_fee: int = 0
    ) -> dict:
        """
        전체 견적 산출 (단가 + 수량 + 샘플비)

        Args:
            metrics: mm 변환 완료된 ShapeMetrics
            quantity: 주문 수량
            drilling_fee: 타공 비용 (키링 고리 등, 기본 0원)

        Returns:
            전체 견적 정보
        """
        price_info = self.calculate_shape_price(metrics, drilling_fee=drilling_fee)
        unit_price = price_info["unit_price"]

        min_qty, layout_info = self.calculate_min_quantity(
            metrics.bbox_width_mm, metrics.bbox_height_mm
        )

        subtotal = unit_price * quantity
        is_sample = quantity < min_qty
        sample_fee = self.SAMPLE_FEE if is_sample else 0
        total_price = subtotal + sample_fee

        return {
            **price_info,
            "quantity": quantity,
            "min_quantity": min_qty,
            "layout_info": layout_info,
            "subtotal": subtotal,
            "sample_fee": sample_fee,
            "total_price": total_price,
            "is_sample": is_sample,
        }
