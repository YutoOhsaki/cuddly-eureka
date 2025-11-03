#!/usr/bin/env python3
"""
Step Functions を手動でトリガーするスクリプト
"""
import boto3
import json
import sys
from datetime import datetime

REGION = "ap-northeast-1"
STATE_MACHINE_ARN = sys.argv[1] if len(sys.argv) > 1 else None


def main():
    """メイン処理"""
    if not STATE_MACHINE_ARN:
        print("Usage: python manual_trigger.py <STATE_MACHINE_ARN>")
        print("\nExample:")
        print("  python manual_trigger.py arn:aws:states:ap-northeast-1:123456789012:stateMachine:VulnMgmt-EventBridge-VulnerabilityManagementWorkflow...")
        sys.exit(1)

    print(f"Triggering Step Functions...")
    print(f"State Machine ARN: {STATE_MACHINE_ARN}")

    # Step Functions クライアント
    sfn_client = boto3.client("stepfunctions", region_name=REGION)

    # 実行名（タイムスタンプ付き）
    execution_name = f"manual-execution-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # 入力データ
    input_data = {
        "execution_type": "manual",
        "execution_time": datetime.now().isoformat(),
        "days_back": 7
    }

    try:
        # Step Functions を開始
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_name,
            input=json.dumps(input_data)
        )

        execution_arn = response["executionArn"]

        print("\n" + "="*60)
        print(f"✓ Step Functions execution started successfully!")
        print(f"Execution ARN: {execution_arn}")
        print(f"Execution Name: {execution_name}")
        print("="*60)

        print("\nYou can monitor the execution in the AWS Console:")
        print(f"https://console.aws.amazon.com/states/home?region={REGION}#/executions/details/{execution_arn}")

    except Exception as e:
        print(f"\n✗ Failed to start execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
