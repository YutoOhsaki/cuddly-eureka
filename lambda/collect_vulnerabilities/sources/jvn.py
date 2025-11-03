"""
JVN (Japan Vulnerability Notes) からの脆弱性情報収集
RSS/RDFフィードを使用
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Any
from urllib.parse import urlparse
import requests


class JVNCollector:
    """JVNから脆弱性情報を収集"""

    def __init__(self):
        self.rss_url = "https://jvn.jp/rss/jvn.rdf"
        self.timeout = 30

    def collect(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        JVNから脆弱性情報を収集

        Args:
            days_back: 過去何日分を取得するか

        Returns:
            脆弱性情報のリスト
        """
        vulnerabilities = []

        try:
            # RSSフィードを取得
            headers = {
                "User-Agent": "VulnerabilityManagementSystem/1.0"
            }

            response = requests.get(
                self.rss_url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()

            # XML解析
            root = ET.fromstring(response.content)

            # 名前空間の定義
            namespaces = {
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "dc": "http://purl.org/dc/elements/1.1/",
                "dcterms": "http://purl.org/dc/terms/",
                "sec": "http://jvn.jp/rss/mod_sec/3.0/",
            }

            # 対象期間の計算
            cutoff_date = datetime.now() - timedelta(days=days_back)

            # 各アイテムを処理
            for item in root.findall(".//item", namespaces):
                try:
                    vuln = self._parse_item(item, namespaces)

                    # 日付フィルタリング
                    if vuln and vuln.get("published_date"):
                        pub_date = datetime.fromisoformat(
                            vuln["published_date"].replace("Z", "+00:00")
                        )
                        if pub_date >= cutoff_date:
                            vulnerabilities.append(vuln)

                except Exception as e:
                    print(f"Failed to parse JVN item: {e}")
                    continue

            return vulnerabilities

        except requests.RequestException as e:
            print(f"Failed to fetch JVN RSS: {e}")
            return []

        except Exception as e:
            print(f"Unexpected error in JVN collection: {e}")
            return []

    def _parse_item(
        self,
        item: ET.Element,
        namespaces: Dict[str, str]
    ) -> Dict[str, Any]:
        """XMLアイテムから脆弱性情報を抽出"""

        # タイトル
        title_elem = item.find("title")
        title = title_elem.text if title_elem is not None else "N/A"

        # リンク
        link_elem = item.find("link")
        link = link_elem.text if link_elem is not None else ""

        # 説明
        description_elem = item.find("description")
        description = description_elem.text if description_elem is not None else ""

        # CVE ID（タイトルまたはリンクから抽出）
        cve_id = self._extract_cve_id(title, link)

        # 日付
        date_elem = item.find("dc:date", namespaces)
        published_date = date_elem.text if date_elem is not None else datetime.now().isoformat()

        # CVSS（sec名前空間から取得）
        cvss_elem = item.find("sec:cvss", namespaces)
        cvss_score = 0.0
        severity = "UNKNOWN"

        if cvss_elem is not None:
            score_elem = cvss_elem.get("score")
            if score_elem:
                try:
                    cvss_score = float(score_elem)
                    severity = self._cvss_to_severity(cvss_score)
                except ValueError:
                    pass

        # 影響を受ける製品（descriptionから抽出）
        affected_products = self._extract_products(description)

        return {
            "PK": cve_id,
            "SK": published_date,
            "title": title,
            "description": description,
            "cvss_score": cvss_score,
            "severity": severity,
            "affected_products": affected_products,
            "source": "JVN",
            "source_url": link,
            "collected_at": datetime.now().isoformat() + "Z"
        }

    def _extract_cve_id(self, title: str, link: str) -> str:
        """タイトルまたはリンクからCVE IDを抽出"""
        # CVE-YYYY-NNNNN 形式のパターン
        pattern = r"CVE-\d{4}-\d{4,7}"

        # タイトルから検索
        match = re.search(pattern, title)
        if match:
            return match.group(0)

        # リンクから検索
        match = re.search(pattern, link)
        if match:
            return match.group(0)

        # JVN識別子をフォールバックとして使用
        jvn_pattern = r"(JVNDB-\d{4}-\d+|JVN#\d+)"
        match = re.search(jvn_pattern, title)
        if match:
            return match.group(0)

        # それでも見つからない場合はリンクからID部分を使用
        if link:
            path = urlparse(link).path
            parts = path.strip("/").split("/")
            if parts:
                return parts[-1]

        return f"JVN-UNKNOWN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _cvss_to_severity(self, cvss_score: float) -> str:
        """CVSSスコアから重要度を判定"""
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"

    def _extract_products(self, description: str) -> List[str]:
        """説明文から影響を受ける製品を抽出（簡易版）"""
        products = []

        # 一般的な製品名パターン
        common_products = [
            "Windows", "Linux", "macOS", "iOS", "Android",
            "Apache", "Nginx", "MySQL", "PostgreSQL",
            "Java", "Python", "PHP", "Node.js",
            "Chrome", "Firefox", "Safari", "Edge",
            "WordPress", "Drupal", "Joomla"
        ]

        for product in common_products:
            if product.lower() in description.lower():
                products.append(product)

        return products if products else ["詳細は情報源を参照"]
