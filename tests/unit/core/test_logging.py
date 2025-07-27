"""構造化ロギングのユニットテスト"""
import json
import logging
from io import StringIO
from unittest.mock import patch

import pytest
import structlog
from freezegun import freeze_time

from core.logging import configure_logging, get_logger


class TestStructuredLogging:
    """構造化ロギングの設定と動作をテスト"""

    def setup_method(self):
        """各テストの前にロガーをリセット"""
        structlog.reset_defaults()

    def test_configure_logging_returns_none(self):
        """configure_loggingが正常に実行されることを確認"""
        result = configure_logging()
        assert result is None

    def test_logger_outputs_json_format(self):
        """ロガーがJSON形式で出力することを確認"""
        output = StringIO()
        
        # StringIOにログを出力するように設定
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger()
            logger.info("test message", extra_field="value")
        
        # 出力されたログをパース
        log_output = output.getvalue().strip()
        log_data = json.loads(log_output)
        
        assert log_data["event"] == "test message"
        assert log_data["extra_field"] == "value"
        assert "timestamp" in log_data
        assert log_data["level"] == "info"

    @freeze_time("2024-01-01 12:00:00")
    def test_logger_includes_timestamp(self):
        """タイムスタンプがISO形式で含まれることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger()
            logger.info("test")
        
        log_data = json.loads(output.getvalue().strip())
        assert log_data["timestamp"] == "2024-01-01T12:00:00Z"

    def test_logger_includes_correlation_id(self):
        """correlation_idを設定できることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger()
            logger = logger.bind(correlation_id="test-correlation-123")
            logger.info("test with correlation")
        
        log_data = json.loads(output.getvalue().strip())
        assert log_data["correlation_id"] == "test-correlation-123"

    def test_logger_handles_exceptions(self):
        """例外情報が構造化されて出力されることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger()
            try:
                raise ValueError("Test exception")
            except ValueError:
                logger.exception("Error occurred")
        
        log_data = json.loads(output.getvalue().strip())
        assert log_data["event"] == "Error occurred"
        assert log_data["level"] == "error"
        assert "exception" in log_data
        assert "ValueError: Test exception" in log_data["exception"]

    def test_logger_respects_log_level(self):
        """設定されたログレベルが適用されることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging(log_level="WARNING")
            logger = get_logger()
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
        
        # DEBUGとINFOは出力されない
        log_outputs = output.getvalue().strip().split("\n")
        assert len(log_outputs) == 1
        log_data = json.loads(log_outputs[0])
        assert log_data["event"] == "warning message"

    def test_logger_preserves_context(self):
        """bindで設定したコンテキストが保持されることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger()
            logger = logger.bind(user_id="user123", request_id="req456")
            logger.info("first message")
            logger.info("second message")
        
        log_outputs = output.getvalue().strip().split("\n")
        
        # 両方のログにコンテキストが含まれる
        for log_line in log_outputs:
            log_data = json.loads(log_line)
            assert log_data["user_id"] == "user123"
            assert log_data["request_id"] == "req456"

    def test_get_logger_with_name(self):
        """名前付きロガーが作成できることを確認"""
        output = StringIO()
        
        with patch("sys.stdout", output):
            configure_logging()
            logger = get_logger("test.module")
            logger.info("named logger")
        
        log_data = json.loads(output.getvalue().strip())
        assert log_data["logger"] == "test.module"