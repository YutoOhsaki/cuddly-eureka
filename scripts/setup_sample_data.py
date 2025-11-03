#!/usr/bin/env python3
"""
サンプル資産データを DynamoDB に投入するスクリプト
"""
import boto3
import sys
from datetime import datetime
from decimal import Decimal

# 環境変数から テーブル名を取得（または引数から）
ASSETS_TABLE_NAME = sys.argv[1] if len(sys.argv) > 1 else "VulnMgmt-Database-ITAssetsTable"
REGION = "ap-northeast-1"

# サンプル資産データ
SAMPLE_ASSETS = [
    # Windows PC
    {
        "PK": "ASSET-001",
        "asset_type": "software",
        "name": "Windows 10",
        "version": "21H2",
        "vendor": "Microsoft",
        "location": "本社営業部",
        "responsible_person": "情報システム部",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-002",
        "asset_type": "software",
        "name": "Windows 11",
        "version": "22H2",
        "vendor": "Microsoft",
        "location": "本社開発部",
        "responsible_person": "情報システム部",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-003",
        "asset_type": "software",
        "name": "Windows Server",
        "version": "2019",
        "vendor": "Microsoft",
        "location": "データセンター",
        "responsible_person": "インフラチーム",
        "last_updated": datetime.now().isoformat()
    },

    # Webサーバー
    {
        "PK": "ASSET-004",
        "asset_type": "middleware",
        "name": "Apache HTTP Server",
        "version": "2.4.54",
        "vendor": "Apache",
        "location": "Webサーバー01",
        "responsible_person": "Webチーム",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-005",
        "asset_type": "middleware",
        "name": "Nginx",
        "version": "1.22.0",
        "vendor": "F5",
        "location": "Webサーバー02",
        "responsible_person": "Webチーム",
        "last_updated": datetime.now().isoformat()
    },

    # データベース
    {
        "PK": "ASSET-006",
        "asset_type": "software",
        "name": "MySQL",
        "version": "8.0.30",
        "vendor": "Oracle",
        "location": "DBサーバー01",
        "responsible_person": "DBチーム",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-007",
        "asset_type": "software",
        "name": "PostgreSQL",
        "version": "14.5",
        "vendor": "PostgreSQL",
        "location": "DBサーバー02",
        "responsible_person": "DBチーム",
        "last_updated": datetime.now().isoformat()
    },

    # プログラミング言語・ランタイム
    {
        "PK": "ASSET-008",
        "asset_type": "middleware",
        "name": "Java",
        "version": "11.0.16",
        "vendor": "Oracle",
        "location": "APサーバー01",
        "responsible_person": "開発チーム",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-009",
        "asset_type": "middleware",
        "name": "Python",
        "version": "3.10.8",
        "vendor": "Python",
        "location": "APサーバー02",
        "responsible_person": "開発チーム",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-010",
        "asset_type": "middleware",
        "name": "Node.js",
        "version": "18.12.0",
        "vendor": "Node.js",
        "location": "APサーバー03",
        "responsible_person": "開発チーム",
        "last_updated": datetime.now().isoformat()
    },

    # ブラウザ
    {
        "PK": "ASSET-011",
        "asset_type": "software",
        "name": "Google Chrome",
        "version": "108.0",
        "vendor": "Google",
        "location": "全社PC",
        "responsible_person": "情報システム部",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-012",
        "asset_type": "software",
        "name": "Mozilla Firefox",
        "version": "108.0",
        "vendor": "Mozilla",
        "location": "開発部PC",
        "responsible_person": "情報システム部",
        "last_updated": datetime.now().isoformat()
    },

    # CMS
    {
        "PK": "ASSET-013",
        "asset_type": "software",
        "name": "WordPress",
        "version": "6.1",
        "vendor": "WordPress",
        "location": "コーポレートサイト",
        "responsible_person": "マーケティング部",
        "last_updated": datetime.now().isoformat()
    },

    # VMware
    {
        "PK": "ASSET-014",
        "asset_type": "software",
        "name": "VMware vSphere",
        "version": "7.0",
        "vendor": "VMware",
        "location": "データセンター",
        "responsible_person": "インフラチーム",
        "last_updated": datetime.now().isoformat()
    },

    # Linux
    {
        "PK": "ASSET-015",
        "asset_type": "software",
        "name": "Ubuntu Server",
        "version": "22.04 LTS",
        "vendor": "Canonical",
        "location": "クラウドサーバー",
        "responsible_person": "インフラチーム",
        "last_updated": datetime.now().isoformat()
    },
    {
        "PK": "ASSET-016",
        "asset_type": "software",
        "name": "Red Hat Enterprise Linux",
        "version": "8.6",
        "vendor": "Red Hat",
        "location": "エンタープライズサーバー",
        "responsible_person": "インフラチーム",
        "last_updated": datetime.now().isoformat()
    },

    # Adobe製品
    {
        "PK": "ASSET-017",
        "asset_type": "software",
        "name": "Adobe Acrobat Reader",
        "version": "2022.003",
        "vendor": "Adobe",
        "location": "全社PC",
        "responsible_person": "情報システム部",
        "last_updated": datetime.now().isoformat()
    },

    # Cisco機器
    {
        "PK": "ASSET-018",
        "asset_type": "hardware",
        "name": "Cisco IOS",
        "version": "15.2",
        "vendor": "Cisco",
        "location": "ネットワーク機器",
        "responsible_person": "ネットワークチーム",
        "last_updated": datetime.now().isoformat()
    },

    # SSL/TLS
    {
        "PK": "ASSET-019",
        "asset_type": "middleware",
        "name": "OpenSSL",
        "version": "3.0.7",
        "vendor": "OpenSSL",
        "location": "全サーバー",
        "responsible_person": "インフラチーム",
        "last_updated": datetime.now().isoformat()
    },

    # コンテナ
    {
        "PK": "ASSET-020",
        "asset_type": "software",
        "name": "Docker",
        "version": "20.10.21",
        "vendor": "Docker",
        "location": "開発環境",
        "responsible_person": "開発チーム",
        "last_updated": datetime.now().isoformat()
    }
]


def main():
    """メイン処理"""
    print(f"Starting asset data setup...")
    print(f"Target table: {ASSETS_TABLE_NAME}")
    print(f"Region: {REGION}")

    # DynamoDB クライアント作成
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(ASSETS_TABLE_NAME)

    # データを投入
    success_count = 0
    error_count = 0

    for asset in SAMPLE_ASSETS:
        try:
            table.put_item(Item=asset)
            print(f"✓ Inserted: {asset['PK']} - {asset['name']} {asset['version']}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to insert {asset['PK']}: {str(e)}")
            error_count += 1

    print("\n" + "="*60)
    print(f"Asset data setup completed!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(SAMPLE_ASSETS)}")
    print("="*60)


if __name__ == "__main__":
    main()
