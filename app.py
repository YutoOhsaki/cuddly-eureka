#!/usr/bin/env python3
"""
脆弱性管理システム - CDK アプリケーション
"""
import os
import aws_cdk as cdk
from cdk.stacks import DatabaseStack, LambdaStack, EventBridgeStack


app = cdk.App()

# 環境設定（東京リージョン）
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region="ap-northeast-1"
)

# スタック名のプレフィックス
stack_prefix = "VulnMgmt"

# =======================================
# スタックのデプロイ
# =======================================

# 1. データベーススタック
database_stack = DatabaseStack(
    app,
    f"{stack_prefix}-Database",
    env=env,
    description="脆弱性管理システム - データベースとストレージ"
)

# 2. Lambda関数スタック
lambda_stack = LambdaStack(
    app,
    f"{stack_prefix}-Lambda",
    database_stack=database_stack,
    env=env,
    description="脆弱性管理システム - Lambda関数"
)

# 3. EventBridge + Step Functionsスタック
eventbridge_stack = EventBridgeStack(
    app,
    f"{stack_prefix}-EventBridge",
    lambda_stack=lambda_stack,
    env=env,
    description="脆弱性管理システム - スケジュール実行"
)

# スタック間の依存関係を明示
lambda_stack.add_dependency(database_stack)
eventbridge_stack.add_dependency(lambda_stack)

# タグ付け
for stack in [database_stack, lambda_stack, eventbridge_stack]:
    cdk.Tags.of(stack).add("Project", "VulnerabilityManagement")
    cdk.Tags.of(stack).add("Environment", "Production")
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth()
