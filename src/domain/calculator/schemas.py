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
