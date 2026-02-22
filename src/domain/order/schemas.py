"""주문 관련 Pydantic 스키마"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class ImageRatioRequest(BaseModel):
    """이미지 비율 계산 요청"""

    original_width: float = Field(..., gt=0, description="원본 가로 (px)")
    original_height: float = Field(..., gt=0, description="원본 세로 (px)")
    target_size: Optional[float] = Field(None, gt=0, description="목표 크기 (mm)")
    target_dimension: str = Field(default="width", description="기준 방향 (width/height)")


class ImageRatioResponse(BaseModel):
    """이미지 비율 계산 응답"""

    original_width: float = Field(..., description="원본 가로 (px)")
    original_height: float = Field(..., description="원본 세로 (px)")
    target_width: float = Field(..., description="목표 가로 (mm)")
    target_height: float = Field(..., description="목표 세로 (mm)")
    ratio: float = Field(..., description="가로/세로 비율")
    target_dimension: str = Field(default="width", description="기준 방향")


class OrderCreate(BaseModel):
    """주문 생성 요청"""

    customer_name: str = Field(..., min_length=1, description="고객 이름")
    customer_phone: str = Field(..., min_length=10, description="연락처")
    customer_email: EmailStr = Field(..., description="이메일")
    width: float = Field(..., gt=0, description="가로 (mm)")
    height: float = Field(..., gt=0, description="세로 (mm)")
    quantity: int = Field(..., gt=0, description="주문 수량")
    file_path: Optional[str] = Field(None, description="업로드 파일 경로")
    notes: Optional[str] = Field(None, description="요청사항")
    proof_requested: bool = Field(default=False, description="시안 확인 요청")
    template_file_requested: bool = Field(default=False, description="작업틀 파일 요청")
    order_type: str = Field(default="order", description="주문 타입 (order/proof_only)")


class OrderResponse(BaseModel):
    """주문 응답"""

    order_id: str = Field(..., description="주문 번호")
    customer_name: str = Field(..., description="고객 이름")
    customer_phone: str = Field(..., description="연락처")
    customer_email: str = Field(..., description="이메일")
    width: float = Field(..., description="가로 (mm)")
    height: float = Field(..., description="세로 (mm)")
    quantity: int = Field(..., description="주문 수량")
    min_quantity: int = Field(..., description="최소 수량")
    unit_price: int = Field(..., description="개당 단가 (원)")
    total_price: int = Field(..., description="총 금액 (원)")
    is_sample: bool = Field(..., description="샘플 제작 여부")
    file_path: Optional[str] = Field(None, description="업로드 파일 경로")
    notes: Optional[str] = Field(None, description="요청사항")
    created_at: str = Field(..., description="주문 일시")
    status: str = Field(default="pending", description="주문 상태")
    proof_requested: bool = Field(default=False, description="시안 확인 요청")
    template_file_requested: bool = Field(default=False, description="작업틀 파일 요청")
    order_type: str = Field(default="order", description="주문 타입")

    model_config = {"from_attributes": True}
