"""
脆弱性情報収集 Lambda ハンドラー
Phase 1: JVNのみ対応
"""
import json
import os
import sys
from datetime import datetime

# 共通ライブラリのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../common"))

from logger import get_logger
from dynamodb_client import DynamoDBClient
from sources.jvn import JVNCollector

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Lambda ハンドラー関数

    Args:
        event: イベントデータ
        context: Lambda コンテキスト

    Returns:
        実行結果
    """
    logger.info("Starting vulnerability collection", event=event)

    try:
        # DynamoDB クライアント初期化
        db_client = DynamoDBClient()

        # 収集期間（デフォルト: 7日間）
        days_back = event.get("days_back", 7)

        # Phase 1: JVNから収集
        logger.info("Collecting from JVN", days_back=days_back)
        jvn_collector = JVNCollector()
        vulnerabilities = jvn_collector.collect(days_back=days_back)

        logger.info(f"Collected {len(vulnerabilities)} vulnerabilities from JVN")

        # DynamoDBに保存
        saved_count = 0
        duplicate_count = 0

        for vuln in vulnerabilities:
            try:
                if db_client.put_vulnerability(vuln):
                    saved_count += 1
                else:
                    duplicate_count += 1

            except Exception as e:
                logger.error(
                    "Failed to save vulnerability",
                    vulnerability_id=vuln.get("PK"),
                    error=str(e)
                )
                continue

        logger.info(
            "Vulnerability collection completed",
            total=len(vulnerabilities),
            saved=saved_count,
            duplicates=duplicate_count
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Vulnerability collection completed",
                "total_collected": len(vulnerabilities),
                "saved": saved_count,
                "duplicates": duplicate_count,
                "vulnerabilities": [v["PK"] for v in vulnerabilities[:10]]  # 最初の10件のIDを返す
            }
        }

    except Exception as e:
        logger.error("Vulnerability collection failed", error=str(e))

        return {
            "statusCode": 500,
            "body": {
                "message": "Vulnerability collection failed",
                "error": str(e)
            }
        }
