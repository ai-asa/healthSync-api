"""
認証付きAPI統合テスト（MVP6）

実際のトークン生成からAPIアクセスまでの統合的な動作を検証
"""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from src.api.v1.dependencies.auth import create_access_token
from src.main import app

client = TestClient(app)


class TestAPIAuthIntegration:
    """API認証の統合テスト"""

    def test_full_auth_flow_with_measurements(self):
        """トークン生成→認証→測定データ登録の完全なフローテスト"""
        # Step 1: トークン生成
        user_data = {
            "sub": "integration_test_user",
            "email": "integration@example.com"
        }
        access_token = create_access_token(data=user_data)
        assert access_token is not None
        assert len(access_token) > 50  # JWTトークンは通常長い文字列

        # Step 2: 認証ヘッダーの作成
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 3: 測定データの準備
        measurements_data = [
            {
                "metric_type": "heart_rate",
                "value": 75.0,
                "unit": "bpm",
                "measured_at": datetime.now(UTC).isoformat(),
                "device_id": "integration_test_device"
            },
            {
                "metric_type": "body_weight",
                "value": 68.5,
                "unit": "kg",
                "measured_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
                "notes": "Integration test measurement"
            }
        ]

        # Step 4: APIエンドポイントへのアクセス
        response = client.post(
            "/v1/measurements/bulk",
            json=measurements_data,
            headers=headers
        )

        # Step 5: レスポンスの検証
        assert response.status_code == 201
        data = response.json()
        
        # 成功件数の確認
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        
        # 測定データの確認
        assert len(data["measurements"]) == 2
        for measurement in data["measurements"]:
            assert "id" in measurement
            assert "created_at" in measurement
            assert measurement["id"] is not None

    def test_token_expiration_flow(self):
        """トークン有効期限のテスト"""
        # Step 1: 短い有効期限でトークン生成（1秒）
        user_data = {"sub": "test_user", "email": "test@example.com"}
        short_lived_token = create_access_token(
            data=user_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Step 2: 即座にアクセス（成功するはず）
        headers = {"Authorization": f"Bearer {short_lived_token}"}
        response = client.post(
            "/v1/measurements/bulk",
            json=[{"metric_type": "heart_rate", "value": 70.0, "unit": "bpm", "measured_at": datetime.now(UTC).isoformat()}],
            headers=headers
        )
        assert response.status_code == 201
        
        # Step 3: 2秒待機
        import time
        time.sleep(2)
        
        # Step 4: 再度アクセス（失敗するはず）
        response = client.post(
            "/v1/measurements/bulk",
            json=[{"metric_type": "heart_rate", "value": 70.0, "unit": "bpm", "measured_at": datetime.now(UTC).isoformat()}],
            headers=headers
        )
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_multiple_users_isolation(self):
        """複数ユーザーの認証が独立していることを確認"""
        # User 1のトークン
        user1_token = create_access_token(
            data={"sub": "user1", "email": "user1@example.com"}
        )
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        
        # User 2のトークン
        user2_token = create_access_token(
            data={"sub": "user2", "email": "user2@example.com"}
        )
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        
        # 両方のユーザーがアクセスできることを確認
        for headers in [headers1, headers2]:
            response = client.post(
                "/v1/measurements/bulk",
                json=[{
                    "metric_type": "steps",
                    "value": 10000.0,
                    "unit": "steps",
                    "measured_at": datetime.now(UTC).isoformat()
                }],
                headers=headers
            )
            assert response.status_code == 201

    def test_malformed_token_handling(self):
        """不正な形式のトークンが適切に処理されることを確認"""
        test_cases = [
            # ケース1: トークンの一部を改変
            {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.MODIFIED.SIGNATURE", "description": "Modified token"},
            # ケース2: 完全にランダムな文字列
            {"token": "not_a_valid_jwt_token", "description": "Random string"},
            # ケース3: 空文字列
            {"token": "", "description": "Empty token"},
        ]
        
        for test_case in test_cases:
            headers = {"Authorization": f"Bearer {test_case['token']}"}
            response = client.post(
                "/v1/measurements/bulk",
                json=[{"metric_type": "heart_rate", "value": 72.0, "unit": "bpm", "measured_at": datetime.now(UTC).isoformat()}],
                headers=headers
            )
            assert response.status_code == 401, f"Failed for {test_case['description']}"
            # エラーメッセージは「Could not validate credentials」または「Not authenticated」のいずれか
            detail = response.json()["detail"]
            assert "Could not validate credentials" in detail or "Not authenticated" in detail

    @pytest.mark.parametrize("endpoint", [
        "/v1/measurements/bulk",
        # 将来追加されるエンドポイントをここに追加
    ])
    def test_all_protected_endpoints_require_auth(self, endpoint):
        """全ての保護されたエンドポイントが認証を要求することを確認"""
        # 認証なしでアクセス
        response = client.post(
            endpoint,
            json=[{"metric_type": "heart_rate", "value": 72.0, "unit": "bpm", "measured_at": datetime.now(UTC).isoformat()}]
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"