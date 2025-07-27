"""
測定データ登録APIのテスト（MVP4 + MVP6）

POST /v1/measurements/bulk のテスト
- 正常系：有効なデータでの一括登録
- 異常系：バリデーションエラー
- エッジケース：空配列、大量データ
- 認証：JWT認証の統合（MVP6）
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from src.api.v1.dependencies.auth import create_access_token
from src.main import app

client = TestClient(app)


class TestMeasurementsBulkAPI:
    """測定データ一括登録APIのテスト"""

    def get_auth_headers(self) -> dict[str, str]:
        """認証用のヘッダーを取得"""
        token = create_access_token(
            data={"sub": "test_user", "email": "test@example.com"}
        )
        return {"Authorization": f"Bearer {token}"}

    def test_bulk_create_with_valid_data(self):
        """正常系：有効なデータで一括登録が成功する"""
        # Arrange
        now = datetime.now(UTC)
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": (now - timedelta(hours=1)).isoformat(),
                "device_id": "apple_watch_001"
            },
            {
                "metric_type": "body_weight",
                "value": 65.5,
                "unit": "kg",
                "measured_at": (now - timedelta(hours=2)).isoformat(),
                "notes": "朝食前の測定"
            },
            {
                "metric_type": "blood_pressure_systolic",
                "value": 120.0,
                "unit": "mmHg",
                "measured_at": now.isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=measurements_data, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "success_count" in data
        assert data["success_count"] == 3
        assert "failed_count" in data
        assert data["failed_count"] == 0
        assert "measurements" in data
        assert len(data["measurements"]) == 3

        # 各測定データにIDが付与されている
        for measurement in data["measurements"]:
            assert "id" in measurement
            assert "metric_type" in measurement
            assert "value" in measurement

    def test_bulk_create_with_invalid_data(self):
        """異常系：無効なデータで422エラーが返る"""
        # Arrange
        invalid_data = [
            {
                "metric_type": "heart_rate",
                "value": -10.0,  # 負の値は無効
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                "metric_type": "invalid_type",  # 無効なメトリックタイプ
                "value": 100.0,
                "unit": "unknown",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                "metric_type": "body_weight",
                "value": 600.0,  # 範囲外の値
                "unit": "kg",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=invalid_data, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # バリデーションエラーの詳細が含まれている
        assert len(data["detail"]) >= 3

    def test_bulk_create_with_empty_array(self):
        """エッジケース：空配列で400エラーが返る"""
        # Act
        response = client.post("/v1/measurements/bulk", json=[], headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()

    def test_bulk_create_with_partial_invalid_data(self):
        """エッジケース：一部無効なデータがある場合、有効なデータのみ登録される"""
        # Arrange
        mixed_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                "metric_type": "heart_rate",
                "value": 300.0,  # 範囲外
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                "metric_type": "body_weight",
                "value": 70.0,
                "unit": "kg",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=mixed_data, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 207  # Multi-Status
        data = response.json()
        assert data["success_count"] == 2
        assert data["failed_count"] == 1
        assert "errors" in data
        assert len(data["errors"]) == 1
        assert data["errors"][0]["index"] == 1
        assert "Heart rate value 300.0 is out of range" in data["errors"][0]["message"]

    def test_bulk_create_with_large_dataset(self):
        """エッジケース：大量データ（100件）の登録"""
        # Arrange
        base_time = datetime.now(UTC)
        large_dataset = []

        for i in range(100):
            measurement = {
                "metric_type": "steps",
                "value": float(5000 + i * 100),
                "unit": "steps",
                "measured_at": (base_time - timedelta(hours=i)).isoformat(),
                "device_id": f"fitbit_{i:03d}"
            }
            large_dataset.append(measurement)

        # Act
        response = client.post("/v1/measurements/bulk", json=large_dataset, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 100
        assert data["failed_count"] == 0
        assert len(data["measurements"]) == 100

    def test_bulk_create_with_future_date(self):
        """異常系：未来の日時でバリデーションエラー"""
        # Arrange
        future_time = datetime.now(UTC) + timedelta(days=1)
        future_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": future_time.isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=future_data, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # バリデーションエラーメッセージに未来の日時に関する記述がある
        error_messages = str(data["detail"])
        assert "future" in error_messages.lower()

    def test_bulk_create_with_missing_required_fields(self):
        """異常系：必須フィールドが欠けている場合"""
        # Arrange
        incomplete_data = [
            {
                "metric_type": "heart_rate",
                # value is missing
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                # metric_type is missing
                "value": 120.0,
                "unit": "mmHg",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=incomplete_data, headers=self.get_auth_headers())

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # 両方のエラーが報告される
        assert len(data["detail"]) >= 2


class TestMeasurementsBulkAPIWithAuth:
    """測定データ一括登録APIの認証テスト（MVP6）"""

    def get_valid_token(self, user_id: str = "user123", email: str = "test@example.com") -> str:
        """テスト用の有効なJWTトークンを生成"""
        return create_access_token(
            data={"sub": user_id, "email": email}
        )

    def get_invalid_token(self) -> str:
        """テスト用の無効なJWTトークンを返す"""
        return "invalid.jwt.token"

    def test_bulk_create_without_auth_returns_401(self):
        """認証なしでアクセスすると401エラーが返る"""
        # Arrange
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post("/v1/measurements/bulk", json=measurements_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Not authenticated"

    def test_bulk_create_with_invalid_token_returns_401(self):
        """無効なトークンでアクセスすると401エラーが返る"""
        # Arrange
        invalid_token = self.get_invalid_token()
        headers = {"Authorization": f"Bearer {invalid_token}"}
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post(
            "/v1/measurements/bulk",
            json=measurements_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Could not validate credentials" in data["detail"]

    def test_bulk_create_with_valid_token_succeeds(self):
        """有効なトークンでアクセスすると正常に処理される"""
        # Arrange
        valid_token = self.get_valid_token()
        headers = {"Authorization": f"Bearer {valid_token}"}
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            },
            {
                "metric_type": "body_weight",
                "value": 65.5,
                "unit": "kg",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post(
            "/v1/measurements/bulk",
            json=measurements_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["measurements"]) == 2

    def test_bulk_create_with_expired_token_returns_401(self):
        """期限切れトークンでアクセスすると401エラーが返る"""
        # Arrange
        # 過去の期限で生成（-1分）
        expired_token = create_access_token(
            data={"sub": "user123", "email": "test@example.com"},
            expires_delta=timedelta(minutes=-1)
        )
        headers = {"Authorization": f"Bearer {expired_token}"}
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post(
            "/v1/measurements/bulk",
            json=measurements_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Could not validate credentials" in data["detail"]

    @pytest.mark.parametrize("auth_header", [
        {"Authorization": "InvalidScheme token123"},  # 不正なスキーム
        {"Authorization": "Bearer"},  # トークンなし
        {},  # Authorizationヘッダーなし
    ])
    def test_bulk_create_with_various_invalid_auth_returns_401(self, auth_header):
        """様々な不正な認証ヘッダーで401エラーが返る"""
        # Arrange
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 72.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat()
            }
        ]

        # Act
        response = client.post(
            "/v1/measurements/bulk",
            json=measurements_data,
            headers=auth_header
        )

        # Assert
        assert response.status_code == 401

