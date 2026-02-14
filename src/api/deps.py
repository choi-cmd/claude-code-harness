"""공통 의존성"""

from typing import Annotated
from fastapi import Depends

from src.domain.calculator.service import CalculatorService


def get_calculator_service() -> CalculatorService:
    """Calculator 서비스 의존성"""
    return CalculatorService()


CalculatorServiceDep = Annotated[CalculatorService, Depends(get_calculator_service)]
