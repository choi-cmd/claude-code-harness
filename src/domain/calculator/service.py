"""아크릴 단가 계산 서비스"""

import math
from src.domain.calculator.schemas import CalculateRequest, CalculateResponse


class CalculatorService:
    """아크릴 단가 계산 서비스"""

    # 아크릴 판 사양
    PANEL_WIDTH = 406.4  # mm
    PANEL_HEIGHT = 609.6  # mm
    MARGIN = 5  # mm (상하좌우 레이저 컷팅 여백)

    # 가격 계산 상수
    BASE_RATE = 0.34  # 기본 단가 계수
    MARKUP = 1.265  # 마진 (1.1 × 1.15)
    SAMPLE_FEE = 10000  # 샘플비 (원)

    def calculate_min_quantity(self, width: float, height: float) -> tuple[int, str]:
        """
        1판 최소 수량 계산

        Args:
            width: 가로 (mm)
            height: 세로 (mm)

        Returns:
            (최소 수량, 배치 정보)
        """
        # 레이저 여백 포함 실제 크기
        actual_width = width + (self.MARGIN * 2)
        actual_height = height + (self.MARGIN * 2)

        # 케이스1: 가로×세로 배치
        layout1_cols = math.floor(self.PANEL_WIDTH / actual_width)
        layout1_rows = math.floor(self.PANEL_HEIGHT / actual_height)
        count1 = layout1_cols * layout1_rows

        # 케이스2: 세로×가로 배치 (90도 회전)
        layout2_cols = math.floor(self.PANEL_WIDTH / actual_height)
        layout2_rows = math.floor(self.PANEL_HEIGHT / actual_width)
        count2 = layout2_cols * layout2_rows

        # 더 많이 들어가는 케이스 선택
        if count1 >= count2:
            layout_info = f"{layout1_cols}개 × {layout1_rows}개 배치"
            return count1, layout_info
        else:
            layout_info = f"{layout2_cols}개 × {layout2_rows}개 배치 (90° 회전)"
            return count2, layout_info

    def calculate_unit_price(self, width: float, height: float) -> int:
        """
        개당 단가 계산

        Args:
            width: 가로 (mm)
            height: 세로 (mm)

        Returns:
            개당 단가 (원, 10원 단위 반올림)
        """
        # 기본 단가 = roundup(가로 × 세로 × 0.34, -1) × 1.265
        base = width * height * self.BASE_RATE
        rounded_base = math.ceil(base / 10) * 10  # 10원 단위 올림
        final_price = rounded_base * self.MARKUP

        return int(final_price)

    def calculate(self, request: CalculateRequest) -> CalculateResponse:
        """
        단가 계산

        Args:
            request: 계산 요청 (가로, 세로, 수량)

        Returns:
            계산 결과
        """
        # 1. 최소 수량 계산
        min_quantity, layout_info = self.calculate_min_quantity(
            request.width, request.height
        )

        # 2. 개당 단가 계산
        unit_price = self.calculate_unit_price(request.width, request.height)

        # 3. 총액 계산
        subtotal = unit_price * request.quantity
        is_sample = request.quantity < min_quantity
        sample_fee = self.SAMPLE_FEE if is_sample else 0
        total_price = subtotal + sample_fee

        return CalculateResponse(
            width=request.width,
            height=request.height,
            quantity=request.quantity,
            min_quantity=min_quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            sample_fee=sample_fee,
            total_price=total_price,
            is_sample=is_sample,
            layout_info=layout_info,
        )
