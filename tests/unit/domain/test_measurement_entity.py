"""Measurementエンティティのユニットテスト"""
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from freezegun import freeze_time
from pydantic import ValidationError

from domain.entities.measurement import Measurement, MetricType


class TestMeasurementEntity:
    """Measurementエンティティのテスト"""

    def test_create_measurement_with_valid_data(self):
        """正常なデータでMeasurementが作成できることを確認"""
        measurement_data = {
            "metric_type": MetricType.HEART_RATE,
            "value": 72.0,
            "unit": "bpm",
            "measured_at": datetime.now(timezone.utc),
            "device_id": "Apple Watch Series 8",
            "metadata": {"quality": "high", "activity": "resting"}
        }
        
        measurement = Measurement(**measurement_data)
        
        assert measurement.metric_type == MetricType.HEART_RATE
        assert measurement.value == 72.0
        assert measurement.unit == "bpm"
        assert measurement.device_id == "Apple Watch Series 8"
        assert measurement.metadata["quality"] == "high"

    def test_metric_type_enum_values(self):
        """MetricTypeが正しい値を持つことを確認"""
        assert MetricType.HEART_RATE.value == "heart_rate"
        assert MetricType.BLOOD_PRESSURE_SYSTOLIC.value == "blood_pressure_systolic"
        assert MetricType.BLOOD_PRESSURE_DIASTOLIC.value == "blood_pressure_diastolic"
        assert MetricType.BODY_WEIGHT.value == "body_weight"
        assert MetricType.BODY_TEMPERATURE.value == "body_temperature"
        assert MetricType.BLOOD_GLUCOSE.value == "blood_glucose"
        assert MetricType.OXYGEN_SATURATION.value == "oxygen_saturation"
        assert MetricType.STEPS.value == "steps"
        assert MetricType.DISTANCE.value == "distance"
        assert MetricType.CALORIES_BURNED.value == "calories_burned"

    def test_invalid_metric_type_raises_error(self):
        """無効なmetric_typeでエラーが発生することを確認"""
        with pytest.raises(ValidationError) as exc_info:
            Measurement(
                metric_type="invalid_type",
                value=100.0,
                unit="unknown",
                measured_at=datetime.now(timezone.utc)
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("metric_type",) for error in errors)

    def test_negative_value_validation(self):
        """負の値が適切に検証されることを確認"""
        # 心拍数は負の値を許可しない
        with pytest.raises(ValidationError) as exc_info:
            Measurement(
                metric_type=MetricType.HEART_RATE,
                value=-10.0,
                unit="bpm",
                measured_at=datetime.now(timezone.utc)
            )
        
        errors = exc_info.value.errors()
        assert any("greater than 0" in str(error) for error in errors)

    def test_value_range_validation(self):
        """値の範囲が適切に検証されることを確認"""
        # 心拍数の異常値
        with pytest.raises(ValidationError) as exc_info:
            Measurement(
                metric_type=MetricType.HEART_RATE,
                value=300.0,  # 異常に高い心拍数
                unit="bpm",
                measured_at=datetime.now(timezone.utc)
            )
        
        errors = exc_info.value.errors()
        assert any("heart rate" in str(error).lower() for error in errors)

    @freeze_time("2024-01-01 12:00:00")
    def test_future_date_validation(self):
        """未来の日時が拒否されることを確認"""
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            Measurement(
                metric_type=MetricType.HEART_RATE,
                value=72.0,
                unit="bpm",
                measured_at=future_date
            )
        
        errors = exc_info.value.errors()
        assert any("future" in str(error).lower() for error in errors)

    def test_unit_validation_for_metric_type(self):
        """メトリックタイプに応じた単位の検証"""
        # 心拍数にkgの単位は不適切
        with pytest.raises(ValidationError) as exc_info:
            Measurement(
                metric_type=MetricType.HEART_RATE,
                value=72.0,
                unit="kg",  # 不適切な単位
                measured_at=datetime.now(timezone.utc)
            )
        
        errors = exc_info.value.errors()
        assert any("unit" in str(error).lower() for error in errors)

    def test_measurement_to_dict(self):
        """Measurementがdictに変換できることを確認"""
        now = datetime.now(timezone.utc)
        measurement = Measurement(
            metric_type=MetricType.BODY_WEIGHT,
            value=70.5,
            unit="kg",
            measured_at=now,
            device_id="Withings Scale"
        )
        
        data = measurement.model_dump()
        
        assert data["metric_type"] == "body_weight"
        assert data["value"] == 70.5
        assert data["unit"] == "kg"
        assert data["device_id"] == "Withings Scale"
        # model_dumpではmode="json"を指定しない限りdatetimeオブジェクトのまま
        assert data["measured_at"] == now

    def test_measurement_json_serialization(self):
        """MeasurementがJSONにシリアライズできることを確認"""
        now = datetime.now(timezone.utc)
        measurement = Measurement(
            metric_type=MetricType.BLOOD_GLUCOSE,
            value=95.0,
            unit="mg/dL",
            measured_at=now
        )
        
        json_data = measurement.model_dump_json()
        parsed_data = json.loads(json_data)
        
        assert parsed_data["metric_type"] == "blood_glucose"
        assert parsed_data["value"] == 95.0
        assert parsed_data["unit"] == "mg/dL"
        # ISO形式の日時文字列になることを確認
        assert isinstance(parsed_data["measured_at"], str)

    def test_measurement_from_dict(self):
        """dictからMeasurementが作成できることを確認"""
        data = {
            "metric_type": "oxygen_saturation",
            "value": 98.0,
            "unit": "%",
            "measured_at": "2024-01-01T12:00:00Z"
        }
        
        measurement = Measurement.model_validate(data)
        
        assert measurement.metric_type == MetricType.OXYGEN_SATURATION
        assert measurement.value == 98.0
        assert measurement.unit == "%"
        assert isinstance(measurement.measured_at, datetime)

    def test_decimal_precision_for_measurements(self):
        """測定値の精度が保持されることを確認"""
        measurement = Measurement(
            metric_type=MetricType.BODY_TEMPERATURE,
            value=36.67,  # 小数点以下2桁
            unit="°C",
            measured_at=datetime.now(timezone.utc)
        )
        
        # 精度が保持されることを確認
        assert measurement.value == 36.67
        assert str(measurement.value) == "36.67"

    def test_optional_fields(self):
        """オプションフィールドの動作を確認"""
        # 最小限の必須フィールドのみ
        measurement = Measurement(
            metric_type=MetricType.STEPS,
            value=10000,
            unit="steps",
            measured_at=datetime.now(timezone.utc)
        )
        
        assert measurement.device_id is None
        assert measurement.metadata is None
        assert measurement.notes is None

    def test_measurement_with_notes(self):
        """メモ付きの測定データを確認"""
        measurement = Measurement(
            metric_type=MetricType.BLOOD_PRESSURE_SYSTOLIC,
            value=120,
            unit="mmHg",
            measured_at=datetime.now(timezone.utc),
            notes="朝食前の測定"
        )
        
        assert measurement.notes == "朝食前の測定"