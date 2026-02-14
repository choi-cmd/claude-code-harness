"""주문 처리 서비스"""

from pathlib import Path
from src.domain.order.schemas import (
    OrderCreate,
    OrderResponse,
    ImageRatioRequest,
    ImageRatioResponse,
)
from src.domain.order.repository import OrderRepository
from src.domain.calculator.service import CalculatorService
from src.domain.calculator.schemas import CalculateRequest


class OrderService:
    """주문 처리 서비스"""

    def __init__(
        self,
        repository: OrderRepository = None,
        calculator: CalculatorService = None,
    ):
        self.repository = repository or OrderRepository()
        self.calculator = calculator or CalculatorService()

    def calculate_image_ratio(
        self, request: ImageRatioRequest
    ) -> ImageRatioResponse:
        """
        이미지 비율 계산

        Args:
            request: 원본 크기와 목표 크기/방향

        Returns:
            계산된 가로/세로 크기
        """
        ratio = request.original_width / request.original_height

        if request.target_dimension == "height":
            target_height = request.target_size
            target_width = round(request.target_size * ratio)
        else:
            target_width = request.target_size
            target_height = round(request.target_size / ratio)

        return ImageRatioResponse(
            original_width=request.original_width,
            original_height=request.original_height,
            target_width=target_width,
            target_height=target_height,
            ratio=round(ratio, 4),
            target_dimension=request.target_dimension,
        )

    def create_order(self, order: OrderCreate) -> OrderResponse:
        """
        주문 생성

        Args:
            order: 주문 정보

        Returns:
            생성된 주문
        """
        # 단가 계산
        calc_request = CalculateRequest(
            width=order.width, height=order.height, quantity=order.quantity
        )
        calc_result = self.calculator.calculate(calc_request)

        # 주문 데이터 준비
        order_data = {
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "customer_email": order.customer_email,
            "width": order.width,
            "height": order.height,
            "quantity": order.quantity,
            "min_quantity": calc_result.min_quantity,
            "unit_price": calc_result.unit_price,
            "total_price": calc_result.total_price,
            "is_sample": calc_result.is_sample,
            "file_path": order.file_path,
            "notes": order.notes,
        }

        # 저장
        saved_order = self.repository.create(order_data)

        return OrderResponse(**saved_order)

    def get_all_orders(self) -> list[OrderResponse]:
        """전체 주문 조회"""
        orders = self.repository.get_all()
        return [OrderResponse(**order) for order in orders]

    def get_order_by_id(self, order_id: str) -> OrderResponse | None:
        """주문 ID로 조회"""
        order = self.repository.get_by_id(order_id)
        if order:
            return OrderResponse(**order)
        return None
