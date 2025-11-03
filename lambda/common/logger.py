"""
構造化ログ機能を提供するモジュール
CloudWatch Logsに適したJSON形式でログを出力
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict


class StructuredLogger:
    """構造化ログを出力するロガークラス"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # ハンドラーが設定されていない場合のみ追加
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)

    def _log(self, level: str, message: str, **kwargs):
        """構造化ログを出力"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            **kwargs
        }

        log_func = getattr(self.logger, level.lower())
        log_func(json.dumps(log_entry, ensure_ascii=False))

    def info(self, message: str, **kwargs):
        """INFOレベルのログ"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """WARNINGレベルのログ"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """ERRORレベルのログ"""
        self._log("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """DEBUGレベルのログ"""
        self._log("DEBUG", message, **kwargs)


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """ロガーインスタンスを取得"""
    return StructuredLogger(name, level)
