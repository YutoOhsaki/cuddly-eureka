"""
資産照合 Lambda ハンドラー
脆弱性と社内資産を照合
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
        event: イベントデータ
        context: Lambda コンテキスト

    Returns:
        照合結果
    """
    logger.info("Starting asset matching", event=event)

    try:
        # クライアント初期化
        db_client = DynamoDBClient()
        bedrock_client = BedrockClient()

        # 全資産を取得
        assets = db_client.get_all_assets()
        logger.info(f"Loaded {len(assets)} assets")

        # 脆弱性IDを取得
        vulnerability_ids = []
        if "body" in event and "vulnerabilities" in event["body"]:
            vulnerability_ids = event["body"]["vulnerabilities"]
        else:
            # 最近の脆弱性を取得
            start_date = (datetime.now() - timedelta(days=7)).isoformat() + "Z"
            recent_vulns = db_client.query_vulnerabilities_by_date(start_date)
            vulnerability_ids = [v["PK"] for v in recent_vulns]

        logger.info(f"Matching {len(vulnerability_ids)} vulnerabilities with {len(assets)} assets")

        matched_count = 0
        total_matches = 0

        # 各脆弱性について資産照合
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
                    logger.warning(f"Vulnerability not found: {vuln_id}")
                    continue

                # 資産とのマッチング
                matched_assets = self._match_assets_with_vulnerability(
                    vuln_data,
                    assets,
                    bedrock_client
                )

                if matched_assets:
                    # DynamoDBに保存
                    db_client.update_vulnerability(
                        vulnerability_id=vuln_data["PK"],
                        sort_key=vuln_data["SK"],
                        updates={
                            "matched_assets": matched_assets,
                            "matched_at": datetime.now().isoformat() + "Z"
                        }
                    )

                    matched_count += 1
                    total_matches += len(matched_assets)

                    logger.info(
                        f"Matched {len(matched_assets)} assets for {vuln_id}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to match assets for vulnerability: {vuln_id}",
                    error=str(e)
                )
                continue

        logger.info(
            "Asset matching completed",
            vulnerabilities=len(vulnerability_ids),
            matched=matched_count,
            total_matches=total_matches
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Asset matching completed",
                "vulnerabilities": len(vulnerability_ids),
                "matched": matched_count,
                "total_matches": total_matches,
                "vulnerabilities_list": vulnerability_ids
            }
        }

    except Exception as e:
        logger.error("Asset matching failed", error=str(e))

        return {
            "statusCode": 500,
            "body": {
                "message": "Asset matching failed",
                "error": str(e)
            }
        }


def _match_assets_with_vulnerability(
    vuln_data: dict,
    assets: list,
    bedrock_client: BedrockClient
) -> list:
    """
    脆弱性と資産をマッチング

    Args:
        vuln_data: 脆弱性データ
        assets: 資産リスト
        bedrock_client: Bedrock クライアント

    Returns:
        マッチした資産のリスト
    """
    matched_assets = []

    # 影響を受ける製品を取得
    affected_products = []

    # AI分析結果から取得
    if vuln_data.get("ai_analysis") and vuln_data["ai_analysis"].get("affected_products"):
        affected_products.extend(vuln_data["ai_analysis"]["affected_products"])

    # 脆弱性データ自体から取得
    if vuln_data.get("affected_products"):
        affected_products.extend(vuln_data["affected_products"])

    # 簡易マッチング（製品名の部分一致）
    for asset in assets:
        asset_name = asset.get("name", "").lower()
        asset_vendor = asset.get("vendor", "").lower()

        for product in affected_products:
            product_lower = product.lower()

            # 製品名またはベンダー名でマッチング
            if (product_lower in asset_name or
                product_lower in asset_vendor or
                asset_name in product_lower):

                matched_assets.append({
                    "asset_id": asset.get("PK"),
                    "asset_name": asset.get("name"),
                    "asset_type": asset.get("asset_type"),
                    "vendor": asset.get("vendor"),
                    "version": asset.get("version"),
                    "location": asset.get("location"),
                    "responsible_person": asset.get("responsible_person"),
                    "risk_level": _calculate_risk_level(vuln_data, asset),
                    "matched_product": product
                })
                break

    return matched_assets


def _calculate_risk_level(vuln_data: dict, asset: dict) -> str:
    """
    リスクレベルを計算

    Args:
        vuln_data: 脆弱性データ
        asset: 資産データ

    Returns:
        リスクレベル (CRITICAL/HIGH/MEDIUM/LOW)
    """
    # CVSSスコアベースの判定
    cvss_score = float(vuln_data.get("cvss_score", 0))

    # AI分析結果も考慮
    if vuln_data.get("ai_analysis"):
        importance = vuln_data["ai_analysis"].get("importance", "MEDIUM")
        attack_ease = vuln_data["ai_analysis"].get("attack_ease", "MODERATE")

        # 攻撃が容易な場合はリスクを上げる
        if attack_ease == "EASY":
            if cvss_score >= 7.0:
                return "CRITICAL"
            elif cvss_score >= 4.0:
                return "HIGH"

    # CVSSスコアのみで判定
    if cvss_score >= 9.0:
        return "CRITICAL"
    elif cvss_score >= 7.0:
        return "HIGH"
    elif cvss_score >= 4.0:
        return "MEDIUM"
    else:
        return "LOW"
