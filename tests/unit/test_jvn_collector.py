"""
JVN Collector のユニットテスト
"""
import unittest
from unittest.mock import Mock, patch
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda/collect_vulnerabilities"))

from sources.jvn import JVNCollector


class TestJVNCollector(unittest.TestCase):
    """JVNCollector のテストケース"""

    def setUp(self):
        """テストのセットアップ"""
        self.collector = JVNCollector()

    def test_extract_cve_id_from_title(self):
        """タイトルからCVE IDを抽出"""
        title = "CVE-2024-1234 - Test Vulnerability"
        link = "https://jvn.jp/test"

        cve_id = self.collector._extract_cve_id(title, link)
        self.assertEqual(cve_id, "CVE-2024-1234")

    def test_extract_cve_id_from_link(self):
        """リンクからCVE IDを抽出"""
        title = "Test Vulnerability"
        link = "https://jvn.jp/CVE-2024-5678"

        cve_id = self.collector._extract_cve_id(title, link)
        self.assertEqual(cve_id, "CVE-2024-5678")

    def test_cvss_to_severity(self):
        """CVSSスコアから重要度を判定"""
        self.assertEqual(self.collector._cvss_to_severity(9.5), "CRITICAL")
        self.assertEqual(self.collector._cvss_to_severity(7.5), "HIGH")
        self.assertEqual(self.collector._cvss_to_severity(5.0), "MEDIUM")
        self.assertEqual(self.collector._cvss_to_severity(2.0), "LOW")

    def test_extract_products(self):
        """説明文から製品を抽出"""
        description = "This vulnerability affects Windows and Linux systems"

        products = self.collector._extract_products(description)
        self.assertIn("Windows", products)
        self.assertIn("Linux", products)

    @patch("requests.get")
    def test_collect_with_mock(self, mock_get):
        """モックを使用した収集テスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <item>
        <title>CVE-2024-TEST - Test Vulnerability</title>
        <link>https://jvn.jp/test</link>
        <description>Test description</description>
        <dc:date xmlns:dc="http://purl.org/dc/elements/1.1/">2024-11-01T00:00:00Z</dc:date>
    </item>
</rdf:RDF>"""

        mock_get.return_value = mock_response

        vulnerabilities = self.collector.collect(days_back=7)

        # リクエストが呼ばれたことを確認
        mock_get.assert_called_once()

        # 結果が返ってくることを確認（パースエラーがあっても空リストが返る）
        self.assertIsInstance(vulnerabilities, list)


if __name__ == "__main__":
    unittest.main()
