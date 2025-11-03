"""
EventBridge スタック
スケジュール実行とStep Functionsを定義
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_logs as logs,
    aws_iam as iam,
)
from constructs import Construct


class EventBridgeStack(Stack):
    """EventBridgeとStep Functionsのスタック"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_stack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =======================================
        # Step Functions: 脆弱性管理ワークフロー
        # =======================================

        # タスク1: 脆弱性収集
        collect_task = tasks.LambdaInvoke(
            self,
            "CollectVulnerabilities",
            lambda_function=lambda_stack.collect_vulnerabilities_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        # タスク2: AI分析
        analyze_task = tasks.LambdaInvoke(
            self,
            "AnalyzeVulnerabilities",
            lambda_function=lambda_stack.analyze_vulnerabilities_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        # タスク3: 資産照合
        match_task = tasks.LambdaInvoke(
            self,
            "MatchAssets",
            lambda_function=lambda_stack.match_assets_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        # タスク4: ベンダー情報収集
        vendor_task = tasks.LambdaInvoke(
            self,
            "CollectVendorInfo",
            lambda_function=lambda_stack.collect_vendor_info_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        # タスク5: 報告書生成
        report_task = tasks.LambdaInvoke(
            self,
            "GenerateReport",
            lambda_function=lambda_stack.generate_report_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        # 成功状態
        succeed = sfn.Succeed(
            self,
            "WorkflowSucceeded",
            comment="脆弱性管理ワークフローが正常に完了しました"
        )

        # 失敗状態
        failed = sfn.Fail(
            self,
            "WorkflowFailed",
            cause="ワークフローの実行中にエラーが発生しました",
            error="WorkflowExecutionError"
        )

        # ワークフロー定義（逐次実行）
        definition = (
            collect_task
            .next(analyze_task)
            .next(match_task)
            .next(vendor_task)
            .next(report_task)
            .next(succeed)
        )

        # エラーハンドリング
        collect_task.add_catch(failed, errors=["States.ALL"], result_path="$.error")
        analyze_task.add_catch(failed, errors=["States.ALL"], result_path="$.error")
        match_task.add_catch(failed, errors=["States.ALL"], result_path="$.error")
        vendor_task.add_catch(failed, errors=["States.ALL"], result_path="$.error")
        report_task.add_catch(failed, errors=["States.ALL"], result_path="$.error")

        # Step Functionsステートマシン
        self.state_machine = sfn.StateMachine(
            self,
            "VulnerabilityManagementWorkflow",
            definition=definition,
            timeout=Duration.minutes(30),
            logs=sfn.LogOptions(
                destination=logs.LogGroup(
                    self,
                    "StateMachineLogGroup",
                    retention=logs.RetentionDays.ONE_WEEK
                ),
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            )
        )

        # =======================================
        # EventBridge: 週次スケジュール
        # =======================================

        # 毎週月曜日 9:00 JST (00:00 UTC = 09:00 JST)
        # 注: EventBridgeはUTC時刻を使用
        rule = events.Rule(
            self,
            "WeeklyScheduleRule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="0",  # UTC 00:00 = JST 09:00
                week_day="MON",
                month="*",
                year="*"
            ),
            description="脆弱性管理システムを毎週月曜日に実行"
        )

        # Step Functionsをターゲットに設定
        rule.add_target(
            targets.SfnStateMachine(
                self.state_machine,
                input=events.RuleTargetInput.from_object({
                    "execution_type": "scheduled",
                    "execution_time": events.EventField.time
                })
            )
        )

        # =======================================
        # 出力
        # =======================================
        self.state_machine_arn = self.state_machine.state_machine_arn
