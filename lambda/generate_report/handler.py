"""
報告書生成 Lambda ハンドラー
Bedrock を使用して自然な日本語で報告書を生成
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

import boto3

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
        生成結果
    """
    logger.info("Starting report generation", event=event)

    try:
        # クライアント初期化
        db_client = DynamoDBClient()
        bedrock_client = BedrockClient()
        s3_client = boto3.client("s3")

        # レポート対象期間
        days_back = event.get("days_back", 7)
        start_date = datetime.now() - timedelta(days=days_back)

        # 脆弱性データを取得
        vulnerabilities = db_client.query_vulnerabilities_by_date(
            start_date.isoformat() + "Z"
        )

        logger.info(f"Generating report for {len(vulnerabilities)} vulnerabilities")

        # 統計情報を計算
        stats = _calculate_statistics(vulnerabilities)

        # エグゼクティブサマリーを生成
        executive_summary = _generate_executive_summary(
            vulnerabilities,
            stats,
            bedrock_client
        )

        # 技術詳細レポートを生成
        technical_report = _generate_technical_report(
            vulnerabilities,
            stats,
            bedrock_client
        )

        # S3に保存
        bucket_name = os.environ.get("REPORTS_BUCKET_NAME")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        executive_key = f"reports/{timestamp}_executive_summary.md"
        technical_key = f"reports/{timestamp}_technical_detail.md"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=executive_key,
            Body=executive_summary.encode("utf-8"),
            ContentType="text/markdown"
        )

        s3_client.put_object(
            Bucket=bucket_name,
            Key=technical_key,
            Body=technical_report.encode("utf-8"),
            ContentType="text/markdown"
        )

        logger.info(
            "Reports generated successfully",
            executive_key=executive_key,
            technical_key=technical_key
        )

        return {
            "statusCode": 200,
            "body": {
                "message": "Report generation completed",
                "executive_summary_key": executive_key,
                "technical_report_key": technical_key,
                "bucket": bucket_name,
                "statistics": stats
            }
        }

    except Exception as e:
        logger.error("Report generation failed", error=str(e))

        return {
            "statusCode": 500,
            "body": {
                "message": "Report generation failed",
                "error": str(e)
            }
        }


def _calculate_statistics(vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """統計情報を計算"""
    stats = {
        "total": len(vulnerabilities),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "unknown": 0,
        "sources": {},
        "affected_assets": 0,
        "critical_assets": 0,
        "high_assets": 0
    }

    for vuln in vulnerabilities:
        # 重要度別カウント
        severity = vuln.get("severity", "UNKNOWN").upper()
        if severity == "CRITICAL":
            stats["critical"] += 1
        elif severity == "HIGH":
            stats["high"] += 1
        elif severity == "MEDIUM":
            stats["medium"] += 1
        elif severity == "LOW":
            stats["low"] += 1
        else:
            stats["unknown"] += 1

        # 情報源別カウント
        source = vuln.get("source", "Unknown")
        stats["sources"][source] = stats["sources"].get(source, 0) + 1

        # 影響資産カウント
        matched_assets = vuln.get("matched_assets", [])
        if matched_assets:
            stats["affected_assets"] += len(matched_assets)

            for asset in matched_assets:
                risk_level = asset.get("risk_level", "").upper()
                if risk_level == "CRITICAL":
                    stats["critical_assets"] += 1
                elif risk_level == "HIGH":
                    stats["high_assets"] += 1

    return stats


def _generate_executive_summary(
    vulnerabilities: List[Dict[str, Any]],
    stats: Dict[str, Any],
    bedrock_client: BedrockClient
) -> str:
    """エグゼクティブサマリーを生成"""

    # テンプレートを読み込む
    template_path = os.path.join(
        os.path.dirname(__file__),
        "templates",
        "executive_summary.md"
    )

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        # テンプレートがない場合は基本的な構造を使用
        template = """# 脆弱性管理レポート - エグゼクティブサマリー

**報告日**: {report_date}

## 概要
{summary}

## 重要な脆弱性
{critical_vulnerabilities_summary}

## 推奨アクション
{recommended_actions}
"""

    # Critical脆弱性の要約をBedrockで生成
    critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]

    if critical_vulns:
        critical_summary = _generate_critical_summary(critical_vulns, bedrock_client)
        actions = _generate_recommended_actions(critical_vulns, bedrock_client)
    else:
        critical_summary = "現時点でCritical（緊急）レベルの脆弱性は検出されていません。"
        actions = "定期的な監視を継続してください。"

    # テンプレートに値を埋め込む
    report = template.format(
        report_date=datetime.now().strftime("%Y年%m月%d日"),
        period=f"過去7日間",
        total_vulnerabilities=stats["total"],
        critical_count=stats["critical"],
        high_count=stats["high"],
        medium_count=stats["medium"],
        low_count=stats["low"],
        affected_assets_count=stats["affected_assets"],
        critical_assets=stats["critical_assets"],
        high_assets=stats["high_assets"],
        critical_vulnerabilities_summary=critical_summary,
        recommended_actions=actions
    )

    return report


def _generate_technical_report(
    vulnerabilities: List[Dict[str, Any]],
    stats: Dict[str, Any],
    bedrock_client: BedrockClient
) -> str:
    """技術詳細レポートを生成"""

    total = stats["total"] if stats["total"] > 0 else 1

    # 情報源別の内訳
    source_breakdown = "\n".join([
        f"| {source} | {count} |"
        for source, count in stats["sources"].items()
    ])

    # Critical脆弱性の詳細
    critical_details = _generate_vulnerability_details(
        [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
    )

    # High脆弱性の詳細
    high_details = _generate_vulnerability_details(
        [v for v in vulnerabilities if v.get("severity") == "HIGH"]
    )

    # 影響資産の詳細
    affected_assets_details = _generate_affected_assets_details(vulnerabilities)

    # 技術的なアクション
    technical_actions = _generate_technical_actions(vulnerabilities)

    # 外部リンク
    external_links = _generate_external_links(vulnerabilities)

    template = """# 脆弱性管理レポート - 技術詳細

**報告日**: {report_date}

## 統計情報

### 脆弱性の概要

| 重要度 | 件数 | 割合 |
|--------|------|------|
| CRITICAL | {critical_count} | {critical_percent:.1f}% |
| HIGH | {high_count} | {high_percent:.1f}% |
| MEDIUM | {medium_count} | {medium_percent:.1f}% |
| LOW | {low_count} | {low_percent:.1f}% |
| **合計** | **{total}** | **100%** |

### 情報源別

| 情報源 | 件数 |
|--------|------|
{source_breakdown}

## Critical 脆弱性の詳細

{critical_details}

## High 脆弱性の詳細

{high_details}

## 影響を受ける資産

{affected_assets_details}

## 推奨対応アクション

{technical_actions}

## 参考情報

{external_links}
"""

    report = template.format(
        report_date=datetime.now().strftime("%Y年%m月%d日"),
        critical_count=stats["critical"],
        high_count=stats["high"],
        medium_count=stats["medium"],
        low_count=stats["low"],
        total=stats["total"],
        critical_percent=(stats["critical"] / total) * 100,
        high_percent=(stats["high"] / total) * 100,
        medium_percent=(stats["medium"] / total) * 100,
        low_percent=(stats["low"] / total) * 100,
        source_breakdown=source_breakdown if source_breakdown else "| なし | 0 |",
        critical_details=critical_details if critical_details else "該当なし",
        high_details=high_details if high_details else "該当なし",
        affected_assets_details=affected_assets_details if affected_assets_details else "該当なし",
        technical_actions=technical_actions,
        external_links=external_links if external_links else "該当なし"
    )

    return report


def _generate_critical_summary(
    critical_vulns: List[Dict[str, Any]],
    bedrock_client: BedrockClient
) -> str:
    """Critical脆弱性の要約を生成"""

    if not critical_vulns:
        return "該当なし"

    # 最大5件まで
    vulns_to_summarize = critical_vulns[:5]

    prompt = f"""以下の{len(vulns_to_summarize)}件のCritical（緊急）脆弱性について、経営層向けに簡潔な日本語で要約してください。

脆弱性情報:
"""

    for i, vuln in enumerate(vulns_to_summarize, 1):
        prompt += f"""
{i}. {vuln.get('title', 'N/A')}
   - CVSSスコア: {vuln.get('cvss_score', 'N/A')}
   - 説明: {vuln.get('description', 'N/A')[:200]}...
"""

    prompt += """
各脆弱性について、1-2文で要点をまとめてください。箇条書き形式で出力してください。"""

    try:
        response = bedrock_client.invoke(
            prompt=prompt,
            temperature=0.3,
            max_tokens=2000
        )

        content = response.get("content", [])
        if content and len(content) > 0:
            return content[0].get("text", "要約の生成に失敗しました")

    except Exception as e:
        logger.error("Failed to generate critical summary", error=str(e))

    # フォールバック
    return "\n".join([
        f"- {v.get('title', 'N/A')} (CVSSスコア: {v.get('cvss_score', 'N/A')})"
        for v in vulns_to_summarize
    ])


def _generate_recommended_actions(
    critical_vulns: List[Dict[str, Any]],
    bedrock_client: BedrockClient
) -> str:
    """推奨アクションを生成"""

    if not critical_vulns:
        return "- 定期的な脆弱性監視を継続してください"

    # AI分析結果から推奨アクションを集約
    actions = []

    for vuln in critical_vulns[:5]:
        ai_analysis = vuln.get("ai_analysis", {})
        recommended = ai_analysis.get("recommended_actions", [])
        actions.extend(recommended)

    if actions:
        # 重複を削除
        unique_actions = list(set(actions))
        return "\n".join([f"- {action}" for action in unique_actions[:10]])

    return "- 該当する脆弱性について、早急にパッチ適用または回避策の実施を検討してください"


def _generate_vulnerability_details(vulnerabilities: List[Dict[str, Any]]) -> str:
    """脆弱性詳細のMarkdownを生成"""

    if not vulnerabilities:
        return "該当なし"

    details = []

    for vuln in vulnerabilities[:10]:  # 最大10件
        detail = f"""### {vuln.get('title', 'N/A')}

- **CVE ID**: {vuln.get('PK', 'N/A')}
- **CVSSスコア**: {vuln.get('cvss_score', 'N/A')}
- **公開日**: {vuln.get('SK', 'N/A')[:10]}
- **情報源**: [{vuln.get('source', 'N/A')}]({vuln.get('source_url', '#')})

**説明**:
{vuln.get('description', 'N/A')[:300]}...

"""

        # AI分析結果があれば追加
        if vuln.get("ai_analysis"):
            ai_analysis = vuln["ai_analysis"]
            detail += f"""**AI分析**:
- 攻撃の容易性: {ai_analysis.get('attack_ease', 'N/A')}
- 推奨アクション: {', '.join(ai_analysis.get('recommended_actions', [])[:3])}

"""

        details.append(detail)

    return "\n".join(details)


def _generate_affected_assets_details(vulnerabilities: List[Dict[str, Any]]) -> str:
    """影響資産の詳細を生成"""

    assets_map = {}

    for vuln in vulnerabilities:
        matched_assets = vuln.get("matched_assets", [])
        for asset in matched_assets:
            asset_id = asset.get("asset_id")
            if asset_id not in assets_map:
                assets_map[asset_id] = {
                    "name": asset.get("asset_name"),
                    "type": asset.get("asset_type"),
                    "vendor": asset.get("vendor"),
                    "version": asset.get("version"),
                    "risk_level": asset.get("risk_level"),
                    "vulnerabilities": []
                }
            assets_map[asset_id]["vulnerabilities"].append(vuln.get("PK"))

    if not assets_map:
        return "該当する資産はありません"

    details = []

    for asset_id, asset_info in list(assets_map.items())[:20]:  # 最大20件
        detail = f"""### {asset_info['name']}

- **資産ID**: {asset_id}
- **タイプ**: {asset_info['type']}
- **ベンダー**: {asset_info['vendor']}
- **バージョン**: {asset_info['version']}
- **リスクレベル**: {asset_info['risk_level']}
- **該当脆弱性数**: {len(asset_info['vulnerabilities'])}件

"""
        details.append(detail)

    return "\n".join(details)


def _generate_technical_actions(vulnerabilities: List[Dict[str, Any]]) -> str:
    """技術的なアクションを生成"""

    actions = [
        "1. Critical/High脆弱性について、セキュリティパッチの適用を最優先で実施してください",
        "2. パッチが提供されていない場合は、ベンダー提供の回避策を実施してください",
        "3. 該当する資産の管理者に連絡し、対応スケジュールを確認してください",
        "4. 対応完了後、脆弱性スキャンを実施して修正を確認してください"
    ]

    return "\n".join(actions)


def _generate_external_links(vulnerabilities: List[Dict[str, Any]]) -> str:
    """外部リンクを生成"""

    links = []

    for vuln in vulnerabilities[:10]:
        source_url = vuln.get("source_url")
        if source_url:
            links.append(f"- [{vuln.get('PK', 'N/A')}]({source_url})")

    return "\n".join(links) if links else "該当なし"
