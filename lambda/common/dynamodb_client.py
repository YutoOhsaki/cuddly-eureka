"""
DynamoDB クライアントラッパー
テーブル操作を簡略化する機能を提供
"""
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from .logger import get_logger

logger = get_logger(__name__)


class DynamoDBClient:
    """DynamoDB操作クライアント"""

    def __init__(self, region: str = None):
        """
        初期化

        Args:
            region: AWSリージョン
        """
        self.region = region or os.environ.get("AWS_REGION", "ap-northeast-1")
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)

        # 環境変数からテーブル名を取得
        self.vulnerabilities_table_name = os.environ.get("VULNERABILITIES_TABLE_NAME")
        self.assets_table_name = os.environ.get("ASSETS_TABLE_NAME")

        logger.info("DynamoDB client initialized", region=self.region)

    def get_table(self, table_name: str):
        """テーブルリソースを取得"""
        return self.dynamodb.Table(table_name)

    def put_vulnerability(self, vulnerability: Dict[str, Any]) -> bool:
        """
        脆弱性情報をDynamoDBに保存

        Args:
            vulnerability: 脆弱性データ

        Returns:
            成功した場合True
        """
        table = self.get_table(self.vulnerabilities_table_name)

        try:
            # Decimal型への変換（DynamoDBはfloatをサポートしないため）
            item = self._convert_floats_to_decimal(vulnerability)

            # 重複チェック用の条件式
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)"
            )

            logger.info(
                "Vulnerability saved",
                vulnerability_id=vulnerability.get("PK")
            )
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.info(
                    "Vulnerability already exists",
                    vulnerability_id=vulnerability.get("PK")
                )
                return False
            else:
                logger.error(
                    "Failed to save vulnerability",
                    error=str(e),
                    vulnerability_id=vulnerability.get("PK")
                )
                raise

    def update_vulnerability(
        self,
        vulnerability_id: str,
        sort_key: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        既存の脆弱性情報を更新

        Args:
            vulnerability_id: 脆弱性ID (PK)
            sort_key: ソートキー (SK)
            updates: 更新する属性の辞書

        Returns:
            成功した場合True
        """
        table = self.get_table(self.vulnerabilities_table_name)

        try:
            # 更新式を構築
            update_expression = "SET "
            expression_attribute_values = {}
            expression_attribute_names = {}

            for i, (key, value) in enumerate(updates.items()):
                placeholder = f":val{i}"
                attr_name = f"#attr{i}"

                if i > 0:
                    update_expression += ", "

                update_expression += f"{attr_name} = {placeholder}"
                expression_attribute_values[placeholder] = self._convert_floats_to_decimal(value)
                expression_attribute_names[attr_name] = key

            table.update_item(
                Key={"PK": vulnerability_id, "SK": sort_key},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ExpressionAttributeNames=expression_attribute_names
            )

            logger.info(
                "Vulnerability updated",
                vulnerability_id=vulnerability_id
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to update vulnerability",
                error=str(e),
                vulnerability_id=vulnerability_id
            )
            raise

    def get_vulnerability(self, vulnerability_id: str, sort_key: str) -> Optional[Dict[str, Any]]:
        """脆弱性情報を取得"""
        table = self.get_table(self.vulnerabilities_table_name)

        try:
            response = table.get_item(
                Key={"PK": vulnerability_id, "SK": sort_key}
            )
            return response.get("Item")
        except Exception as e:
            logger.error(
                "Failed to get vulnerability",
                error=str(e),
                vulnerability_id=vulnerability_id
            )
            return None

    def query_vulnerabilities_by_date(
        self,
        start_date: str,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        日付範囲で脆弱性を検索

        Args:
            start_date: 開始日時 (ISO 8601形式)
            end_date: 終了日時 (オプション)
            limit: 取得件数上限

        Returns:
            脆弱性のリスト
        """
        table = self.get_table(self.vulnerabilities_table_name)

        try:
            # GSIを使用した検索（日付でソート）
            # 注: 実際のGSI設計に応じて調整が必要
            response = table.scan(
                Limit=limit,
                FilterExpression="SK >= :start_date",
                ExpressionAttributeValues={":start_date": start_date}
            )

            return response.get("Items", [])

        except Exception as e:
            logger.error("Failed to query vulnerabilities", error=str(e))
            return []

    def get_all_assets(self) -> List[Dict[str, Any]]:
        """全資産情報を取得"""
        table = self.get_table(self.assets_table_name)

        try:
            response = table.scan()
            return response.get("Items", [])
        except Exception as e:
            logger.error("Failed to get assets", error=str(e))
            return []

    def put_asset(self, asset: Dict[str, Any]) -> bool:
        """資産情報を保存"""
        table = self.get_table(self.assets_table_name)

        try:
            item = self._convert_floats_to_decimal(asset)
            table.put_item(Item=item)

            logger.info("Asset saved", asset_id=asset.get("PK"))
            return True

        except Exception as e:
            logger.error("Failed to save asset", error=str(e), asset_id=asset.get("PK"))
            raise

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        floatをDecimalに変換（DynamoDB用）

        Args:
            obj: 変換対象オブジェクト

        Returns:
            変換後のオブジェクト
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj
