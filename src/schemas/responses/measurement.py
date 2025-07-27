"""測定データレスポンススキーマ"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from domain.entities.measurement import MetricType


class MeasurementResponse(BaseModel):
    """測定データレスポンス"""

    model_config = ConfigDict(use_enum_values=True)

    id: str
    metric_type: MetricType
    value: float
    unit: str
    measured_at: datetime
    device_id: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime


class MeasurementBulkCreateResponse(BaseModel):
    """測定データ一括作成レスポンス"""

    success_count: int
    failed_count: int
    measurements: list[MeasurementResponse]
    errors: Optional[list[dict[str, Any]]] = None


class MeasurementErrorDetail(BaseModel):
    """測定データエラー詳細"""

    index: int
    message: str
    field: Optional[str] = None

