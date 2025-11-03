"""
データベーススタック
DynamoDB テーブルと S3 バケットを定義
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class DatabaseStack(Stack):
    """データベースとストレージのスタック"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =======================================
        # DynamoDB: Vulnerabilities テーブル
        # =======================================
        self.vulnerabilities_table = dynamodb.Table(
            self,
            "VulnerabilitiesTable",
            partition_key=dynamodb.Attribute(
                name="PK",  # CVE-ID
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="SK",  # 公開日時 (ISO 8601形式)
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,  # オンデマンドモード
            point_in_time_recovery=True,  # ポイントインタイムリカバリ有効化
            removal_policy=RemovalPolicy.RETAIN,  # 削除時もテーブルを保持
            encryption=dynamodb.TableEncryption.AWS_MANAGED,  # 暗号化有効
        )

        # GSI: 日付でソートするためのインデックス
        self.vulnerabilities_table.add_global_secondary_index(
            index_name="SourceIndex",
            partition_key=dynamodb.Attribute(
                name="source",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="collected_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # GSI: 重要度でフィルタリング
        self.vulnerabilities_table.add_global_secondary_index(
            index_name="SeverityIndex",
            partition_key=dynamodb.Attribute(
                name="severity",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="collected_at",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # =======================================
        # DynamoDB: IT Assets テーブル
        # =======================================
        self.assets_table = dynamodb.Table(
            self,
            "ITAssetsTable",
            partition_key=dynamodb.Attribute(
                name="PK",  # asset_id
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        # GSI: 資産タイプでフィルタリング
        self.assets_table.add_global_secondary_index(
            index_name="AssetTypeIndex",
            partition_key=dynamodb.Attribute(
                name="asset_type",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # GSI: ベンダーでフィルタリング
        self.assets_table.add_global_secondary_index(
            index_name="VendorIndex",
            partition_key=dynamodb.Attribute(
                name="vendor",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # =======================================
        # S3: レポート保存バケット
        # =======================================
        self.reports_bucket = s3.Bucket(
            self,
            "ReportsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,  # 暗号化有効
            versioned=True,  # バージョニング有効
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # パブリックアクセスブロック
            removal_policy=RemovalPolicy.RETAIN,  # 削除時もバケットを保持
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldReports",
                    enabled=True,
                    expiration_days=90,  # 90日後に削除
                    noncurrent_version_expiration_days=30  # 古いバージョンは30日で削除
                )
            ]
        )

        # =======================================
        # 出力（他のスタックで参照）
        # =======================================
        self.vulnerabilities_table_name = self.vulnerabilities_table.table_name
        self.assets_table_name = self.assets_table.table_name
        self.reports_bucket_name = self.reports_bucket.bucket_name
