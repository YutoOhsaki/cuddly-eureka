"""
Bedrock Client のユニットテスト
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/common"))

from bedrock_client import BedrockClient


class TestBedrockClient(unittest.TestCase):
    """BedrockClient のテストケース"""

    @patch("boto3.client")
    def setUp(self, mock_boto_client):
        """テストのセットアップ"""
        self.mock_client = Mock()
        mock_boto_client.return_value = self.mock_client
        self.bedrock = BedrockClient(region="ap-northeast-1")

    def test_estimate_importance(self):
        """重要度推定のテスト"""
        # Critical
        vuln_data = {"cvss_score": 9.5}
        self.assertEqual(self.bedrock._estimate_importance(vuln_data), "CRITICAL")

        # High
        vuln_data = {"cvss_score": 7.5}
        self.assertEqual(self.bedrock._estimate_importance(vuln_data), "HIGH")

        # Medium
        vuln_data = {"cvss_score": 5.0}
        self.assertEqual(self.bedrock._estimate_importance(vuln_data), "MEDIUM")

        # Low
        vuln_data = {"cvss_score": 2.0}
        self.assertEqual(self.bedrock._estimate_importance(vuln_data), "LOW")

    @patch("boto3.client")
    def test_invoke_success(self, mock_boto_client):
        """Bedrock API呼び出しの成功テスト"""
        # モッククライアントの設定
        mock_client = Mock()
        mock_boto_client.return_value = mock_client

        # モックレスポンス
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [
                {
                    "text": '{"importance": "HIGH", "attack_ease": "EASY"}'
                }
            ]
        }).encode("utf-8")

        mock_client.invoke_model.return_value = mock_response

        # テスト実行
        bedrock = BedrockClient(region="ap-northeast-1")
        result = bedrock.invoke(prompt="Test prompt")

        # 検証
        self.assertIn("content", result)
        mock_client.invoke_model.assert_called_once()

    def test_analyze_vulnerability_with_invalid_json(self):
        """無効なJSONレスポンスの処理テスト"""
        # モックレスポンス（無効なJSON）
        mock_response = {
            "body": MagicMock()
        }
        mock_response["body"].read.return_value = json.dumps({
            "content": [
                {
                    "text": "Invalid JSON response"
                }
            ]
        }).encode("utf-8")

        self.mock_client.invoke_model.return_value = mock_response

        vuln_data = {
            "title": "Test",
            "description": "Test description",
            "cvss_score": 7.5
        }

        # フォールバック処理が動作することを確認
        result = self.bedrock.analyze_vulnerability(vuln_data)

        self.assertIn("importance", result)
        self.assertIn("affected_products", result)


if __name__ == "__main__":
    unittest.main()
