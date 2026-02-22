"""계산기 설정 저장소 (JSON)"""

import json
from pathlib import Path
from typing import Optional


class SettingsRepository:
    """계산기 설정 JSON 저장소"""

    VALID_TYPES = {"acrylic", "aluminum", "birchwood"}

    def __init__(self, data_dir: Path = Path("data")):
        self.data_dir = data_dir
        self.settings_file = data_dir / "calculator_settings.json"
        self._init_storage()

    def _init_storage(self) -> None:
        """저장소 초기화"""
        self.data_dir.mkdir(exist_ok=True)
        if not self.settings_file.exists():
            self.settings_file.write_text("{}", encoding="utf-8")

    def _load(self) -> dict:
        """전체 설정 로드"""
        return json.loads(self.settings_file.read_text(encoding="utf-8"))

    def _save(self, data: dict) -> None:
        """전체 설정 저장"""
        self.settings_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get_all(self) -> dict:
        """전체 계산기 설정 조회"""
        return self._load()

    def get_by_type(self, calc_type: str) -> Optional[dict]:
        """특정 계산기 설정 조회"""
        if calc_type not in self.VALID_TYPES:
            return None
        data = self._load()
        return data.get(calc_type)

    def update_section(self, calc_type: str, section: str, values: dict) -> Optional[dict]:
        """계산기 설정의 특정 섹션 업데이트"""
        if calc_type not in self.VALID_TYPES:
            return None
        data = self._load()
        if calc_type not in data:
            data[calc_type] = {}
        data[calc_type][section] = values
        self._save(data)
        return data[calc_type]

    def update(self, calc_type: str, settings: dict) -> Optional[dict]:
        """계산기 전체 설정 업데이트"""
        if calc_type not in self.VALID_TYPES:
            return None
        data = self._load()
        if calc_type not in data:
            data[calc_type] = {}
        data[calc_type].update(settings)
        self._save(data)
        return data[calc_type]
