"""測定データリクエストスキーマ"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from domain.entities.measurement import MetricType


class MeasurementCreateRequest(BaseModel):
    """測定データ作成リクエスト"""

    model_config = ConfigDict(use_enum_values=True)

    metric_type: MetricType
    value: float
    unit: str
    measured_at: datetime
    device_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    notes: Optional[str] = None

