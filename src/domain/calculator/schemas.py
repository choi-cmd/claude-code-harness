"""아크릴 단가 계산기 Pydantic 스키마"""

from pydantic import BaseModel, Field, field_validator


class CalculateRequest(BaseModel):
    """단가 계산 요청"""

    width: float = Field(..., gt=0, description="가로 (mm)")
    height: float = Field(..., gt=0, description="세로 (mm)")
    quantity: int = Field(..., gt=0, description="주문 수량")

    @field_validator("width", "height")
    @classmethod
    def validate_size(cls, v: float) -> float:
        """크기는 최대 아크릴 판 크기보다 작아야 함"""
        if v > 600:
            raise ValueError("크기가 너무 큽니다 (최대 600mm)")
        return v


class CalculateResponse(BaseModel):
    """단가 계산 응답"""

    width: float = Field(..., description="가로 (mm)")
    height: float = Field(..., description="세로 (mm)")
    quantity: int = Field(..., description="주문 수량")
    min_quantity: int = Field(..., description="1판 최소 수량")
    unit_price: int = Field(..., description="개당 단가 (원)")
    subtotal: int = Field(..., description="소계 (원)")
    sample_fee: int = Field(0, description="샘플비 (원)")
    total_price: int = Field(..., description="총 금액 (원)")
    is_sample: bool = Field(..., description="샘플 제작 여부")
    layout_info: str = Field(..., description="배치 정보")

    model_config = {"from_attributes": True}


class ShapeAnalysisResult(BaseModel):
    """이미지 형상 분석 결과"""

    area_mm2: float = Field(..., description="실제 면적 (mm²)")
    perimeter_mm: float = Field(..., description="아웃라인 길이 (mm)")
    bbox_width_mm: float = Field(..., description="바운딩 박스 가로 (mm)")
    bbox_height_mm: float = Field(..., description="바운딩 박스 세로 (mm)")
    fill_ratio: float = Field(..., description="채움률 (0~1)")
    complexity_score: float = Field(..., description="복잡도 점수 (0~1)")
    complexity_label: str = Field(..., description="복잡도 등급")
    vertex_count: int = Field(..., description="꼭짓점 수")
    circularity: float = Field(..., description="원형도 (0~1)")


class ShapeCalculateResponse(BaseModel):
    """형상 기반 상세 견적 응답"""

    # 형상 정보
    area_mm2: float = Field(..., description="실제 면적 (mm²)")
    perimeter_mm: float = Field(..., description="아웃라인 길이 (mm)")
    bbox_width_mm: float = Field(..., description="바운딩 박스 가로 (mm)")
    bbox_height_mm: float = Field(..., description="바운딩 박스 세로 (mm)")
    fill_ratio: float = Field(..., description="채움률")
    complexity_score: float = Field(..., description="복잡도 점수")
    complexity_label: str = Field(..., description="복잡도 등급")

    # 가격 분해
    material_cost: float = Field(..., description="재료비 (원)")
    processing_cost: float = Field(..., description="가공비 (원)")
    complexity_multiplier: float = Field(..., description="복잡도 계수")
    efficiency_multiplier: float = Field(..., description="효율 계수")
    efficiency_label: str = Field(..., description="효율 등급")
    margin: float = Field(..., description="마진 배율")
    unit_price: int = Field(..., description="개당 단가 (원)")

    # 주문 정보
    quantity: int = Field(..., description="주문 수량")
    min_quantity: int = Field(..., description="1판 최소 수량")
    layout_info: str = Field(..., description="배치 정보")
    subtotal: int = Field(..., description="소계 (원)")
    sample_fee: int = Field(0, description="샘플비 (원)")
    total_price: int = Field(..., description="총 금액 (원)")
    is_sample: bool = Field(..., description="샘플 제작 여부")
