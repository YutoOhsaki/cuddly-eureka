"""
Lambda スタック
各Lambda関数とレイヤーを定義
"""
import os
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class LambdaStack(Stack):
    """Lambda関数のスタック"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database_stack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 共通の環境変数
        common_environment = {
            "VULNERABILITIES_TABLE_NAME": database_stack.vulnerabilities_table_name,
            "ASSETS_TABLE_NAME": database_stack.assets_table_name,
            "REPORTS_BUCKET_NAME": database_stack.reports_bucket_name,
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "AWS_REGION": self.region,
            "LOG_LEVEL": "INFO"
        }

        # =======================================
        # Lambda Layer: 共通ライブラリ
        # =======================================
        # 注: 実際のデプロイでは、lambda/commonディレクトリをzipしてレイヤーとして使用
        # ここでは簡略化のため、各関数に直接含める方式を採用

        # =======================================
        # Lambda関数: 脆弱性収集
        # =======================================
        self.collect_vulnerabilities_function = lambda_.Function(
            self,
            "CollectVulnerabilitiesFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/collect_vulnerabilities"),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=common_environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,  # Step Functionsでリトライを制御
        )

        # DynamoDB書き込み権限
        database_stack.vulnerabilities_table.grant_write_data(
            self.collect_vulnerabilities_function
        )

        # インターネットアクセス用の権限（VPC外で実行）
        self.collect_vulnerabilities_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                resources=["*"]
            )
        )

        # =======================================
        # Lambda関数: AI分析
        # =======================================
        self.analyze_vulnerabilities_function = lambda_.Function(
            self,
            "AnalyzeVulnerabilitiesFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/analyze_vulnerabilities"),
            timeout=Duration.minutes(3),
            memory_size=1024,
            environment=common_environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,
        )

        # DynamoDB読み書き権限
        database_stack.vulnerabilities_table.grant_read_write_data(
            self.analyze_vulnerabilities_function
        )

        # Bedrock呼び出し権限
        self.analyze_vulnerabilities_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
                ]
            )
        )

        # =======================================
        # Lambda関数: 資産照合
        # =======================================
        self.match_assets_function = lambda_.Function(
            self,
            "MatchAssetsFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/match_assets"),
            timeout=Duration.minutes(3),
            memory_size=512,
            environment=common_environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,
        )

        # DynamoDB読み書き権限
        database_stack.vulnerabilities_table.grant_read_write_data(
            self.match_assets_function
        )
        database_stack.assets_table.grant_read_data(
            self.match_assets_function
        )

        # Bedrock呼び出し権限（曖昧マッチング用）
        self.match_assets_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
                ]
            )
        )

        # =======================================
        # Lambda関数: ベンダー情報収集
        # =======================================
        self.collect_vendor_info_function = lambda_.Function(
            self,
            "CollectVendorInfoFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/collect_vendor_info"),
            timeout=Duration.minutes(10),
            memory_size=512,
            environment=common_environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,
        )

        # DynamoDB読み書き権限
        database_stack.vulnerabilities_table.grant_read_write_data(
            self.collect_vendor_info_function
        )

        # =======================================
        # Lambda関数: 報告書生成
        # =======================================
        self.generate_report_function = lambda_.Function(
            self,
            "GenerateReportFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda/generate_report"),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment=common_environment,
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,
        )

        # DynamoDB読み取り権限
        database_stack.vulnerabilities_table.grant_read_data(
            self.generate_report_function
        )
        database_stack.assets_table.grant_read_data(
            self.generate_report_function
        )

        # S3書き込み権限
        database_stack.reports_bucket.grant_write(
            self.generate_report_function
        )

        # Bedrock呼び出し権限（報告書生成用）
        self.generate_report_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
                ]
            )
        )
