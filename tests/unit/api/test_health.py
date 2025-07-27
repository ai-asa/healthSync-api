"""ヘルスチェックエンドポイントのユニットテスト"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


@pytest.fixture
def client():
    """テスト用のFastAPIクライアントを作成"""
    from main import app
    return TestClient(app)


def test_health_check_returns_200(client):
    """ヘルスチェックエンドポイントが正常に200を返すことを確認"""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_format(client):
    """ヘルスチェックのレスポンス形式が正しいことを確認"""
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data
    assert "service" in data
    assert data["service"] == "healthsync-api"


def test_health_check_timestamp_format(client):
    """タイムスタンプがISO形式であることを確認"""
    response = client.get("/health")
    data = response.json()
    
    # ISO形式の日時文字列をパースできることを確認
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert isinstance(timestamp, datetime)