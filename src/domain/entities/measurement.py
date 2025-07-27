"""測定データのドメインエンティティ"""
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class MetricType(str, Enum):
    """測定データのタイプ"""
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic"
    BODY_WEIGHT = "body_weight"
    BODY_TEMPERATURE = "body_temperature"
    BLOOD_GLUCOSE = "blood_glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    STEPS = "steps"
    DISTANCE = "distance"
    CALORIES_BURNED = "calories_burned"


# メトリックタイプごとの有効な単位
VALID_UNITS: dict[MetricType, set[str]] = {
    MetricType.HEART_RATE: {"bpm", "beats/min"},
    MetricType.BLOOD_PRESSURE_SYSTOLIC: {"mmHg"},
    MetricType.BLOOD_PRESSURE_DIASTOLIC: {"mmHg"},
    MetricType.BODY_WEIGHT: {"kg", "lb"},
    MetricType.BODY_TEMPERATURE: {"°C", "°F"},
    MetricType.BLOOD_GLUCOSE: {"mg/dL", "mmol/L"},
    MetricType.OXYGEN_SATURATION: {"%"},
    MetricType.STEPS: {"steps"},
    MetricType.DISTANCE: {"m", "km", "mi"},
    MetricType.CALORIES_BURNED: {"kcal", "cal"},
}

# メトリックタイプごとの値の範囲
VALUE_RANGES: dict[MetricType, tuple[float, float]] = {
    MetricType.HEART_RATE: (20.0, 250.0),
    MetricType.BLOOD_PRESSURE_SYSTOLIC: (50.0, 250.0),
    MetricType.BLOOD_PRESSURE_DIASTOLIC: (30.0, 150.0),
    MetricType.BODY_WEIGHT: (0.1, 500.0),
    MetricType.BODY_TEMPERATURE: (25.0, 45.0),  # °C
    MetricType.BLOOD_GLUCOSE: (20.0, 600.0),  # mg/dL
    MetricType.OXYGEN_SATURATION: (50.0, 100.0),
    MetricType.STEPS: (0.0, 100000.0),
    MetricType.DISTANCE: (0.0, 1000000.0),  # meters
    MetricType.CALORIES_BURNED: (0.0, 10000.0),
}


class Measurement(BaseModel):
    """測定データエンティティ"""

    metric_type: MetricType = Field(..., description="測定データのタイプ")
    value: float = Field(..., description="測定値")
    unit: str = Field(..., description="単位")
    measured_at: datetime = Field(..., description="測定日時")
    device_id: Optional[str] = Field(None, description="測定デバイスID")
    metadata: Optional[dict[str, Any]] = Field(None, description="追加メタデータ")
    notes: Optional[str] = Field(None, description="メモ")

    @field_validator("value")
    @classmethod
    def validate_positive_value(cls, v: float, info: Any) -> float:
        """値が正であることを確認（一部のメトリックタイプのみ）"""
        if v <= 0:
            # ステップ数やカロリーは0を許可
            metric_type = info.data.get("metric_type")
            if metric_type not in [MetricType.STEPS, MetricType.CALORIES_BURNED]:
                raise ValueError(f"Value must be greater than 0, got {v}")
        return v

    @field_validator("measured_at")
    @classmethod
    def validate_not_future(cls, v: datetime) -> datetime:
        """測定日時が未来でないことを確認"""
        now = datetime.now(UTC)
        # タイムゾーンがない場合はUTCとして扱う
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)

        if v > now:
            raise ValueError("Measurement date cannot be in the future")
        return v

    @model_validator(mode="after")
    def validate_unit_for_metric_type(self) -> "Measurement":
        """メトリックタイプに対して単位が適切かを確認"""
        valid_units = VALID_UNITS.get(self.metric_type, set())
        if valid_units and self.unit not in valid_units:
            raise ValueError(
                f"Invalid unit '{self.unit}' for metric type {self.metric_type.value}. "
                f"Valid units are: {', '.join(valid_units)}"
            )
        return self

    @model_validator(mode="after")
    def validate_value_range(self) -> "Measurement":
        """メトリックタイプに対して値が適切な範囲内かを確認"""
        value_range = VALUE_RANGES.get(self.metric_type)
        if value_range:
            min_val, max_val = value_range
            if not min_val <= self.value <= max_val:
                if self.metric_type == MetricType.HEART_RATE:
                    raise ValueError(
                        f"Heart rate value {self.value} is out of range. "
                        f"Expected range: {min_val} to {max_val}"
                    )
                else:
                    raise ValueError(
                        f"Value {self.value} is out of range for {self.metric_type.value}. "
                        f"Expected range: {min_val} to {max_val}"
                    )
        return self

    @field_serializer("measured_at", when_used="json")
    def serialize_measured_at(self, measured_at: datetime) -> str:
        """日時をISO形式でシリアライズ（JSON出力時のみ）"""
        return measured_at.isoformat()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": "2024-01-01T12:00:00Z",
                "device_id": "Apple Watch Series 8",
                "metadata": {
                    "quality": "high",
                    "activity": "resting"
                },
                "notes": "Morning measurement"
            }
        }
    )
