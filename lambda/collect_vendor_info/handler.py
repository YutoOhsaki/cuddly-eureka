"""
ベンダー情報収集 Lambda ハンドラー
Phase 2で実装予定（現在は基本実装のみ）
"""
import json
import os
import sys
from datetime import datetime, timedelta

# 共通ライブラリのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../common"))

from logger import get_logger
from dynamodb_client import DynamoDBClient

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Lambda ハンドラー関数

    Args:
        event: イベントデータ
        context: Lambda コンテキスト

    Returns:
        収集結果
    """
    logger.info("Starting vendor info collection", event=event)

    try:
        # Phase 1では基本実装のみ
        # Phase 2で本格実装予定

        db_client = DynamoDBClient()

        # 脆弱性IDを取得
        vulnerability_ids = []
        if "body" in event and "vulnerabilities_list" in event["body"]:
            vulnerability_ids = event["body"]["vulnerabilities_list"]
        elif "body" in event and "vulnerabilities" in event["body"]:
            vulnerability_ids = event["body"]["vulnerabilities"]
        else:
            # 最近の脆弱性を取得
            start_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
            recent_vulns = db_client.query_vulnerabilities_by_date(start_date)
            vulnerability_ids = [v["PK"] for v in recent_vulns]

        logger.info(f"Processing {len(vulnerability_ids)} vulnerabilities for vendor info")

        # Phase 1では基本情報のみ設定
        processed_count = 0

        for vuln_id in vulnerability_ids:
            try:
                # 脆弱性データを取得
                vulnerabilities = db_client.query_vulnerabilities_by_date(
                    (datetime.now() - timedelta(days=30)).isoformat() + "Z"
                )

                vuln_data = None
                for v in vulnerabilities:
                    if v.get("PK") == vuln_id:
                        vuln_data = v
                        break

                if not vuln_data:
                    continue

                # Phase 1では基本的なベンダー情報を設定
                vendor_info = {
                    "status": "pending",
                    "message": "Phase 2で詳細なベンダー情報を収集予定",
                    "collected_at": datetime.now().isoformat() + "Z"
                }

                # DynamoDBに保存
                db_client.update_vulnerability(
                    vulnerability_id=vuln_data["PK"],
                    sort_key=vuln_data["SK"],
                    updates={
                        "vendor_info": vendor_info
                    }
                )

                processed_count += 1

            except Exception as e:
                logger.error(
                    f"Failed to process vendor info for: {vuln_id}",
                    error=str(e)
                )
                continue

        logger.info(
            "Vendor info collection completed",
            total=len(vulnerability_ids),
            processed=processed_count
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Vendor info collection completed (Phase 1)",
                "total": len(vulnerability_ids),
                "processed": processed_count,
                "vulnerabilities_list": vulnerability_ids
            }
        }

    except Exception as e:
        logger.error("Vendor info collection failed", error=str(e))

        return {
            "statusCode": 500,
            "body": {
                "message": "Vendor info collection failed",
                "error": str(e)
            }
        }
