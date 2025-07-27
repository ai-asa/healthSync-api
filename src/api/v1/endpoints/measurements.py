"""測定データエンドポイント"""

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Body, HTTPException, Response, status
from pydantic import ValidationError

from domain.entities.measurement import Measurement
from schemas.requests.measurement import MeasurementCreateRequest
from schemas.responses.measurement import (
    MeasurementBulkCreateResponse,
    MeasurementResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/measurements", tags=["measurements"])


measurements_body = Body(..., description="Array of measurement data")

@router.post("/bulk", response_model=MeasurementBulkCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_measurements_bulk(
    response: Response,
    measurements_data: list[dict[str, Any]] = measurements_body
) -> MeasurementBulkCreateResponse:
    """測定データを一括登録する"""

    # 空配列チェック
    if not measurements_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Measurements array cannot be empty"
        )

    # 結果を格納する変数
    successful_measurements = []
    errors = []

    # 各測定データを処理
    for index, raw_data in enumerate(measurements_data):
        try:
            # まずPydanticモデルでバリデーション
            measurement_request = MeasurementCreateRequest(**raw_data)

            # 次にMeasurementエンティティでバリデーション
            measurement = Measurement(
                metric_type=measurement_request.metric_type,
                value=measurement_request.value,
                unit=measurement_request.unit,
                measured_at=measurement_request.measured_at,
                device_id=measurement_request.device_id,
                metadata=measurement_request.metadata,
                notes=measurement_request.notes
            )

            # 成功した場合、レスポンス用のデータを作成（モック実装）
            measurement_response = MeasurementResponse(
                id=str(uuid.uuid4()),
                metric_type=measurement.metric_type,
                value=measurement.value,
                unit=measurement.unit,
                measured_at=measurement.measured_at,
                device_id=measurement.device_id,
                metadata=measurement.metadata,
                notes=measurement.notes,
                created_at=datetime.now(UTC)
            )
            successful_measurements.append(measurement_response)

        except ValidationError as e:
            # Pydanticバリデーションエラーの場合
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
                errors.append({
                    "index": index,
                    "message": error["msg"],
                    "field": field_path
                })
        except ValueError as e:
            # Measurementエンティティのバリデーションエラー
            errors.append({
                "index": index,
                "message": str(e)
            })

    # ログ出力
    logger.info(
        "Bulk measurement creation completed",
        total_count=len(measurements_data),
        success_count=len(successful_measurements),
        failed_count=len(errors)
    )

    # 一部失敗がある場合は207 Multi-Status
    if errors and successful_measurements:
        response.status_code = 207  # Multi-Status
        return MeasurementBulkCreateResponse(
            success_count=len(successful_measurements),
            failed_count=len(errors),
            measurements=successful_measurements,
            errors=errors
        )

    # すべて失敗した場合は422
    if errors and not successful_measurements:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors
        )

    # すべて成功
    return MeasurementBulkCreateResponse(
        success_count=len(successful_measurements),
        failed_count=0,
        measurements=successful_measurements,
        errors=None
    )
