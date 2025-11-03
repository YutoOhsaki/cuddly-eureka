"""
Amazon Bedrock クライアントラッパー
Claude 3.5 Sonnetを使用したAI分析機能を提供
"""
import json
import os
import time
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .logger import get_logger

logger = get_logger(__name__)


class BedrockClient:
    """Bedrock APIクライアント"""

    def __init__(self, region: str = None, model_id: str = None):
        """
        初期化

        Args:
            region: AWSリージョン (デフォルト: 環境変数または ap-northeast-1)
            model_id: 使用するモデルID (デフォルト: Claude 3.5 Sonnet)
        """
        self.region = region or os.environ.get("AWS_REGION", "ap-northeast-1")
        self.model_id = model_id or os.environ.get(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region
        )

        logger.info("Bedrock client initialized", region=self.region, model_id=self.model_id)

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Bedrock APIを呼び出し

        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト (オプション)
            max_tokens: 最大トークン数
            temperature: 温度パラメータ (0-1)
            max_retries: 最大リトライ回数

        Returns:
            API応答の辞書
        """
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature
        }

        if system_prompt:
            request_body["system"] = system_prompt

        for attempt in range(max_retries):
            try:
                logger.info(
                    "Invoking Bedrock API",
                    attempt=attempt + 1,
                    model_id=self.model_id
                )

                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )

                response_body = json.loads(response["body"].read())

                logger.info("Bedrock API call successful")
                return response_body

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                logger.warning(
                    "Bedrock API error",
                    attempt=attempt + 1,
                    error_code=error_code,
                    error_message=str(e)
                )

                # スロットリングの場合は指数バックオフでリトライ
                if error_code == "ThrottlingException" and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.info(f"Retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                raise

            except Exception as e:
                logger.error("Unexpected error in Bedrock API call", error=str(e))
                raise

        raise Exception(f"Failed to invoke Bedrock API after {max_retries} attempts")

    def analyze_vulnerability(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        脆弱性情報を分析

        Args:
            vulnerability_data: 脆弱性データ

        Returns:
            分析結果
        """
        system_prompt = """あなたは情報セキュリティの専門家です。
脆弱性情報を分析し、以下の観点で評価してください：
1. 重要度 (CRITICAL/HIGH/MEDIUM/LOW)
2. 影響を受ける製品・バージョン
3. 攻撃の容易性 (EASY/MODERATE/DIFFICULT)
4. 推奨対応アクション

回答はJSON形式で、以下の構造で返してください：
{
  "importance": "CRITICAL|HIGH|MEDIUM|LOW",
  "affected_products": ["製品名 バージョン", ...],
  "attack_ease": "EASY|MODERATE|DIFFICULT",
  "recommended_actions": ["アクション1", "アクション2", ...],
  "summary": "日本語での要約（2-3文）"
}
"""

        prompt = f"""以下の脆弱性情報を分析してください：

タイトル: {vulnerability_data.get('title', 'N/A')}
説明: {vulnerability_data.get('description', 'N/A')}
CVSSスコア: {vulnerability_data.get('cvss_score', 'N/A')}
公開日: {vulnerability_data.get('published_date', 'N/A')}

JSON形式で分析結果を返してください。"""

        try:
            response = self.invoke(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3  # より決定的な結果を得るため低めに設定
            )

            # Claude 3.5のレスポンス形式から本文を抽出
            content = response.get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "")

                # JSON部分を抽出
                if "```json" in text:
                    json_str = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    json_str = text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = text.strip()

                return json.loads(json_str)

            raise ValueError("No content in Bedrock response")

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Bedrock response as JSON", error=str(e))
            # フォールバック: 基本的な分析結果を返す
            return {
                "importance": self._estimate_importance(vulnerability_data),
                "affected_products": [],
                "attack_ease": "MODERATE",
                "recommended_actions": ["詳細な調査が必要です"],
                "summary": "自動分析に失敗したため、手動での確認が必要です。"
            }

    def _estimate_importance(self, vulnerability_data: Dict[str, Any]) -> str:
        """CVSSスコアから重要度を推定"""
        cvss_score = vulnerability_data.get("cvss_score", 0)

        if isinstance(cvss_score, str):
            try:
                cvss_score = float(cvss_score)
            except ValueError:
                return "MEDIUM"

        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"
