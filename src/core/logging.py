"""構造化ロギングの設定と管理"""
import logging
import sys
from typing import Any, Optional

import structlog
from structlog.types import EventDict, Processor


def add_timestamp(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """タイムスタンプをISO形式で追加"""
    from datetime import datetime, timezone
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """構造化ロギングを設定
    
    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # 既存のハンドラーをクリア
    logging.root.handlers = []
    
    # Python標準ロギングの設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
        force=True,
    )
    
    # structlogの設定
    processors: list[Processor] = [
        # ログレベルを追加
        structlog.stdlib.add_log_level,
        # ログ名を追加
        structlog.stdlib.add_logger_name,
        # タイムスタンプを追加
        add_timestamp,
        # 位置引数をフォーマット
        structlog.stdlib.PositionalArgumentsFormatter(),
        # スタックトレースをレンダリング
        structlog.processors.StackInfoRenderer(),
        # 例外情報をフォーマット
        structlog.processors.format_exc_info,
        # イベント辞書をレンダリング
        structlog.processors.dict_tracebacks,
        # Unicode文字をデコード
        structlog.processors.UnicodeDecoder(),
        # JSON形式で出力
        structlog.processors.JSONRenderer(),
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """構造化ロガーを取得
    
    Args:
        name: ロガー名（省略時は呼び出し元のモジュール名）
    
    Returns:
        構造化ロガーインスタンス
    """
    return structlog.get_logger(name)