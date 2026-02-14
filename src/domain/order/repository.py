"""주문 데이터 저장소 (JSON)"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


class OrderRepository:
    """주문 JSON 저장소"""

    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.orders_file = data_dir / "orders.json"
        self._init_storage()

    def _init_storage(self) -> None:
        """저장소 초기화"""
        self.data_dir.mkdir(exist_ok=True)
        if not self.orders_file.exists():
            self.orders_file.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        """주문 목록 로드"""
        return json.loads(self.orders_file.read_text(encoding="utf-8"))

    def _save(self, orders: list[dict]) -> None:
        """주문 목록 저장"""
        self.orders_file.write_text(
            json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def generate_order_id(self) -> str:
        """주문 번호 생성 (ORD-YYYYMMDD-NNNN)"""
        orders = self._load()
        today = datetime.now().strftime("%Y%m%d")
        today_orders = [o for o in orders if o["order_id"].startswith(f"ORD-{today}")]
        sequence = len(today_orders) + 1
        return f"ORD-{today}-{sequence:04d}"

    def create(self, order_data: dict) -> dict:
        """주문 생성"""
        orders = self._load()
        order_data["order_id"] = self.generate_order_id()
        order_data["created_at"] = datetime.now().isoformat()
        order_data["status"] = "pending"
        orders.append(order_data)
        self._save(orders)
        return order_data

    def get_all(self) -> list[dict]:
        """전체 주문 조회"""
        orders = self._load()
        return sorted(orders, key=lambda x: x["created_at"], reverse=True)

    def get_by_id(self, order_id: str) -> Optional[dict]:
        """주문 ID로 조회"""
        orders = self._load()
        return next((o for o in orders if o["order_id"] == order_id), None)

    def update_status(self, order_id: str, status: str) -> Optional[dict]:
        """주문 상태 업데이트"""
        orders = self._load()
        for order in orders:
            if order["order_id"] == order_id:
                order["status"] = status
                self._save(orders)
                return order
        return None

    def delete(self, order_id: str) -> bool:
        """주문 삭제"""
        orders = self._load()
        filtered = [o for o in orders if o["order_id"] != order_id]
        if len(filtered) < len(orders):
            self._save(filtered)
            return True
        return False
