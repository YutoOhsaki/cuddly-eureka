"""
AI分析 Lambda ハンドラー
Amazon Bedrock (Claude 3.5 Sonnet) を使用して脆弱性を分析
"""
import json
import os
import sys
from datetime import datetime, timedelta

# 共通ライブラリのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../common"))

from logger import get_logger
from dynamodb_client import DynamoDBClient
from bedrock_client import BedrockClient

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    Lambda ハンドラー関数

    Args:
        event: イベントデータ（前のステップからの出力）
        context: Lambda コンテキスト

    Returns:
        分析結果
    """
    logger.info("Starting AI vulnerability analysis", event=event)

    try:
        # クライアント初期化
        db_client = DynamoDBClient()
        bedrock_client = BedrockClient()

        # 前のステップから脆弱性IDを取得
        vulnerability_ids = []

        if "body" in event and "vulnerabilities" in event["body"]:
            vulnerability_ids = event["body"]["vulnerabilities"]
        else:
            # イベントに脆弱性IDがない場合は、最近の脆弱性を取得
            logger.info("No vulnerability IDs in event, fetching recent vulnerabilities")
            start_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
            recent_vulns = db_client.query_vulnerabilities_by_date(start_date)
            vulnerability_ids = [v["PK"] for v in recent_vulns]

        logger.info(f"Analyzing {len(vulnerability_ids)} vulnerabilities")

        analyzed_count = 0
        failed_count = 0

        # 各脆弱性を分析
        for vuln_id in vulnerability_ids:
            try:
                # DynamoDBから脆弱性データを取得
                # 注: 実際のSKが必要なので、スキャンまたはクエリで取得
                vulnerabilities = db_client.query_vulnerabilities_by_date(
                    (datetime.now() - timedelta(days=30)).isoformat() + "Z"
                )

                vuln_data = None
                for v in vulnerabilities:
                    if v.get("PK") == vuln_id:
                        vuln_data = v
                        break

                if not vuln_data:
                    logger.warning(f"Vulnerability not found: {vuln_id}")
                    failed_count += 1
                    continue

                # 既に分析済みの場合はスキップ
                if vuln_data.get("ai_analysis"):
                    logger.info(f"Vulnerability already analyzed: {vuln_id}")
                    analyzed_count += 1
                    continue

                # AI分析を実行
                logger.info(f"Analyzing vulnerability: {vuln_id}")
                analysis_result = bedrock_client.analyze_vulnerability(vuln_data)

                # DynamoDBに分析結果を保存
                db_client.update_vulnerability(
                    vulnerability_id=vuln_data["PK"],
                    sort_key=vuln_data["SK"],
                    updates={
                        "ai_analysis": analysis_result,
                        "analyzed_at": datetime.now().isoformat() + "Z"
                    }
                )

                analyzed_count += 1
                logger.info(
                    f"Analysis completed for {vuln_id}",
                    importance=analysis_result.get("importance")
                )

            except Exception as e:
                logger.error(
                    f"Failed to analyze vulnerability: {vuln_id}",
                    error=str(e)
                )
                failed_count += 1
                continue

        logger.info(
            "AI analysis completed",
            total=len(vulnerability_ids),
            analyzed=analyzed_count,
            failed=failed_count
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "AI analysis completed",
                "total": len(vulnerability_ids),
                "analyzed": analyzed_count,
                "failed": failed_count,
                "vulnerabilities": vulnerability_ids
            }
        }

    except Exception as e:
        logger.error("AI analysis failed", error=str(e))

        return {
            "statusCode": 500,
            "body": {
                "message": "AI analysis failed",
                "error": str(e)
            }
        }
