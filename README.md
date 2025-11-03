# 脆弱性管理自動化システム

AWSを活用した社内SE向けの脆弱性管理業務自動化システムです。IPA、JVN、JPCERT/CC、NVDなどから脆弱性情報を自動収集し、社内資産との照合、AI分析、レポート生成までを自動化します。

## 目次

- [システム概要](#システム概要)
- [機能](#機能)
- [アーキテクチャ](#アーキテクチャ)
- [技術スタック](#技術スタック)
- [前提条件](#前提条件)
- [セットアップ](#セットアップ)
- [デプロイ](#デプロイ)
- [使用方法](#使用方法)
- [カスタマイズ](#カスタマイズ)
- [トラブルシューティング](#トラブルシューティング)
- [コスト見積もり](#コスト見積もり)
- [ロードマップ](#ロードマップ)

---

## システム概要

本システムは、以下の課題を解決します:

- **手作業の削減**: 複数の情報源からの脆弱性情報収集を自動化
- **迅速な対応**: AI分析により、重要な脆弱性を即座に識別
- **資産管理**: 社内IT資産と脆弱性を自動照合
- **報告の簡素化**: 経営層・技術者向けレポートを自動生成

### 主な特徴

- 週次で自動実行（EventBridge + Step Functions）
- Amazon Bedrock（Claude 3.5 Sonnet）によるAI分析
- 複数の脆弱性情報源に対応（JVN、IPA、JPCERT/CC、NVD）
- Markdown形式の読みやすいレポート
- サーバーレスアーキテクチャによる低コスト運用

---

## 機能

### Phase 1（現在実装済み）

- ✅ JVN RSSフィードからの脆弱性情報収集
- ✅ Amazon Bedrock による AI分析
  - 重要度判定
  - 影響製品の抽出
  - 攻撃容易性の評価
  - 推奨アクションの提案
- ✅ 基本的な報告書生成（エグゼクティブサマリー + 技術詳細）
- ✅ 資産照合機能（基本実装）
- ✅ Step Functions による自動ワークフロー
- ✅ 週次スケジュール実行

### Phase 2（今後実装予定）

- 複数情報源対応（IPA、JPCERT/CC、NVD）
- 高度な資産照合（Bedrock による曖昧マッチング）
- ベンダー情報の自動収集
- 詳細な影響分析

### Phase 3（将来実装予定）

- SNS/メール通知機能
- QuickSight ダッシュボード
- より高度なAI分析
- 過去データのトレンド分析

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│            EventBridge (週次スケジュール)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│          Step Functions (オーケストレーション)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 収集     │→ │ AI分析   │→ │ 資産照合 │→ │ 報告生成 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────┬────────────┬────────────┬────────────┬────────────┘
         │            │            │            │
         ▼            ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ Lambda  │  │ Lambda  │  │ Lambda  │  │ Lambda  │
    │ 収集    │  │ AI分析  │  │ 資産照合│  │ 報告    │
    └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
         │            │            │            │
         │            ▼            │            │
         │       ┌─────────┐      │            │
         │       │ Bedrock │      │            │
         │       │ Claude  │      │            │
         │       └─────────┘      │            │
         │                        │            │
         ▼                        ▼            ▼
    ┌──────────────────────────────────────────────┐
    │         DynamoDB Tables                       │
    │  ┌─────────────┐    ┌──────────────┐        │
    │  │Vulnerabilities│    │  IT_Assets  │        │
    │  └─────────────┘    └──────────────┘        │
    └──────────────────────────────────────────────┘
                        │
                        ▼
                   ┌────────┐
                   │   S3   │
                   │ Reports│
                   └────────┘
```

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| クラウド | AWS（Lambda, DynamoDB, S3, EventBridge, Step Functions, Bedrock） |
| IaC | AWS CDK (Python) |
| 言語 | Python 3.12 |
| AI | Amazon Bedrock (Claude 3.5 Sonnet) |
| リージョン | ap-northeast-1 (東京) |

---

## 前提条件

### 必須

1. **AWSアカウント**
   - 管理者権限またはCDKデプロイに必要な権限

2. **AWS CLI**
   ```bash
   aws --version
   # aws-cli/2.x.x 以上
   ```

3. **Python 3.12以上**
   ```bash
   python3 --version
   # Python 3.12.x
   ```

4. **Node.js 18以上**（CDK用）
   ```bash
   node --version
   # v18.x.x 以上
   ```

5. **AWS CDK Toolkit**
   ```bash
   npm install -g aws-cdk
   cdk --version
   # 2.150.0 以上
   ```

### Amazon Bedrock の有効化

1. AWS コンソールで Amazon Bedrock にアクセス
2. 東京リージョン (ap-northeast-1) を選択
3. Model access メニューから Claude 3.5 Sonnet v2 を有効化

---

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd vulnerability-management-system
```

### 2. Python 仮想環境の作成

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
# CDK依存関係
pip install -r requirements.txt

# Lambda依存関係（各関数ごと）
pip install -r lambda/collect_vulnerabilities/requirements.txt
pip install -r lambda/analyze_vulnerabilities/requirements.txt
pip install -r lambda/match_assets/requirements.txt
pip install -r lambda/collect_vendor_info/requirements.txt
pip install -r lambda/generate_report/requirements.txt
```

### 4. AWS CLI の設定

```bash
aws configure
# AWS Access Key ID を入力
# AWS Secret Access Key を入力
# Default region name: ap-northeast-1
# Default output format: json
```

### 5. AWS認証情報の確認

```bash
aws sts get-caller-identity
```

---

## デプロイ

### 1. CDK ブートストラップ（初回のみ）

```bash
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1
```

`ACCOUNT-ID` は実際のAWSアカウントIDに置き換えてください。

### 2. CDK のシンセサイズ（確認）

```bash
cdk synth
```

生成されるCloudFormationテンプレートを確認できます。

### 3. デプロイの実行

```bash
# 全スタックをデプロイ
cdk deploy --all

# または個別にデプロイ
cdk deploy VulnMgmt-Database
cdk deploy VulnMgmt-Lambda
cdk deploy VulnMgmt-EventBridge
```

デプロイには5-10分程度かかります。

### 4. デプロイ結果の確認

デプロイが完了すると、以下の出力が表示されます:

```
VulnMgmt-Database
  Outputs:
    VulnerabilitiesTableName = VulnMgmt-Database-VulnerabilitiesTable...
    AssetsTableName = VulnMgmt-Database-ITAssetsTable...
    ReportsBucketName = vulnmgmt-database-reportsbucket...

VulnMgmt-EventBridge
  Outputs:
    StateMachineArn = arn:aws:states:ap-northeast-1:...
```

これらの値をメモしておいてください。

### 5. サンプル資産データの投入

```bash
# テーブル名を環境変数から取得するか、直接指定
export ASSETS_TABLE_NAME="VulnMgmt-Database-ITAssetsTable..."

python scripts/setup_sample_data.py $ASSETS_TABLE_NAME
```

20件のサンプル資産（Windows、Linux、Apache、MySQL等）が投入されます。

---

## 使用方法

### 自動実行

システムは毎週月曜日 09:00 JST（00:00 UTC）に自動実行されます。

実行内容:
1. JVNから過去7日分の脆弱性情報を収集
2. AI分析を実行
3. 社内資産との照合
4. ベンダー情報を収集
5. 報告書を生成してS3に保存

### 手動実行

Step Functions を手動でトリガーする場合:

```bash
# State Machine ARNを指定
python scripts/manual_trigger.py arn:aws:states:ap-northeast-1:ACCOUNT-ID:stateMachine:VulnMgmt-EventBridge-VulnerabilityManagement...
```

または、AWS コンソールから:
1. Step Functions コンソールを開く
2. "VulnMgmt-EventBridge-VulnerabilityManagementWorkflow" を選択
3. "実行を開始" をクリック

### 実行状況の確認

#### Step Functions コンソール

1. AWS コンソール → Step Functions
2. 実行履歴からステータスを確認
3. 各ステップの入出力を確認可能

#### CloudWatch Logs

各Lambda関数のログを確認:

```bash
aws logs tail /aws/lambda/VulnMgmt-Lambda-CollectVulnerabilitiesFunction --follow
```

### 報告書の取得

#### S3から直接ダウンロード

```bash
aws s3 ls s3://BUCKET-NAME/reports/

aws s3 cp s3://BUCKET-NAME/reports/20241103_100000_executive_summary.md ./
aws s3 cp s3://BUCKET-NAME/reports/20241103_100000_technical_detail.md ./
```

#### AWS コンソールから

1. S3 コンソールを開く
2. レポートバケットを選択
3. `reports/` フォルダ内のMarkdownファイルをダウンロード

---

## カスタマイズ

### 1. 実行スケジュールの変更

`cdk/stacks/eventbridge_stack.py` を編集:

```python
# 毎週月曜日 9:00 JST → 毎日 9:00 JST に変更
rule = events.Rule(
    self,
    "DailyScheduleRule",
    schedule=events.Schedule.cron(
        minute="0",
        hour="0",  # UTC 00:00 = JST 09:00
        week_day="*",  # 毎日
        month="*",
        year="*"
    ),
    description="脆弱性管理システムを毎日実行"
)
```

変更後、再デプロイ:
```bash
cdk deploy VulnMgmt-EventBridge
```

### 2. 脆弱性情報源の追加

Phase 2で実装予定の機能を有効化する場合:

1. `lambda/collect_vulnerabilities/sources/` に新しい収集クラスを追加
2. `lambda/collect_vulnerabilities/handler.py` で呼び出しを追加
3. `config/sources.json` に設定を追加

### 3. 資産データの追加

#### スクリプトで一括追加

`scripts/setup_sample_data.py` の `SAMPLE_ASSETS` リストに追加してスクリプトを実行。

#### AWS CLI で個別追加

```bash
aws dynamodb put-item \
    --table-name ASSETS_TABLE_NAME \
    --item '{
        "PK": {"S": "ASSET-021"},
        "asset_type": {"S": "software"},
        "name": {"S": "新しい製品"},
        "version": {"S": "1.0"},
        "vendor": {"S": "ベンダー名"},
        "location": {"S": "配置場所"},
        "responsible_person": {"S": "担当者"},
        "last_updated": {"S": "2024-11-03T00:00:00"}
    }'
```

### 4. AI分析のカスタマイズ

`lambda/common/bedrock_client.py` の `analyze_vulnerability` メソッドのプロンプトを編集:

```python
system_prompt = """あなたは情報セキュリティの専門家です。
<カスタマイズ内容をここに追加>
"""
```

変更後、再デプロイ:
```bash
cdk deploy VulnMgmt-Lambda
```

---

## トラブルシューティング

### デプロイエラー

#### エラー: "Stack with id ... does not exist"

**原因**: CDKブートストラップが未実行

**解決策**:
```bash
cdk bootstrap aws://ACCOUNT-ID/ap-northeast-1
```

#### エラー: "Access Denied" (Bedrock関連)

**原因**: Bedrockモデルへのアクセス権限が未設定

**解決策**:
1. AWS コンソール → Bedrock
2. Model access で Claude 3.5 Sonnet v2 を有効化

### 実行時エラー

#### Lambda タイムアウト

**症状**: Lambda関数が制限時間内に完了しない

**解決策**:
- `cdk/stacks/lambda_stack.py` でタイムアウトを延長
- データ収集期間を短縮（`days_back` を減らす）

#### Bedrock API エラー "ThrottlingException"

**症状**: Bedrock呼び出しが頻繁に失敗

**解決策**:
- リトライロジックが自動で動作します
- それでも失敗する場合は、処理を分散（並列度を下げる）

#### DynamoDB エラー "ConditionalCheckFailedException"

**症状**: 脆弱性の保存時にエラー

**原因**: 既に同じ脆弱性が存在（正常な動作）

**対処**: ログで確認。重複は自動でスキップされます。

### ログの確認方法

```bash
# 特定のLambda関数のログを確認
aws logs tail /aws/lambda/FUNCTION-NAME --follow

# Step Functionsの実行履歴を確認
aws stepfunctions list-executions \
    --state-machine-arn STATE_MACHINE_ARN \
    --max-results 10
```

### デバッグモード

Lambda関数で詳細ログを有効化:

```bash
# 環境変数を追加して再デプロイ
# cdk/stacks/lambda_stack.py
environment={
    ...
    "LOG_LEVEL": "DEBUG"
}
```

---

## コスト見積もり

### 月次コスト（想定）

| サービス | 使用量 | 月額（USD） |
|---------|--------|------------|
| Lambda | 週1回 × 5関数 × 4週 | $1-2 |
| DynamoDB | オンデマンド、小規模 | $1-3 |
| S3 | 報告書保存（数MB/週） | $0.10 |
| Bedrock | Claude 3.5 Sonnet | $5-10 |
| Step Functions | 週1回実行 | $0.10 |
| EventBridge | スケジュール実行 | $0.01 |
| **合計** | | **$10-20** |

### コスト削減のヒント

- 脆弱性収集期間を短縮（7日 → 3日）
- AI分析対象を Critical/High のみに絞る
- DynamoDB のTTL設定で古いデータを自動削除
- S3 ライフサイクルポリシーで古いレポートをアーカイブ

---

## テスト

### ユニットテストの実行

```bash
# テスト用依存関係をインストール
pip install -r tests/requirements.txt

# 全テストを実行
pytest tests/unit/ -v

# カバレッジレポート付き
pytest tests/unit/ --cov=lambda --cov-report=html
```

### 統合テスト

```bash
# 手動トリガーでシステム全体をテスト
python scripts/manual_trigger.py STATE_MACHINE_ARN
```

---

## ロードマップ

### Phase 2（次期バージョン）

- [ ] IPA、JPCERT/CC、NVD からの脆弱性収集
- [ ] 高度な資産照合（Bedrock 曖昧マッチング）
- [ ] ベンダー情報の自動収集（Webスクレイピング）
- [ ] 詳細な影響分析

### Phase 3（将来バージョン）

- [ ] SNS/メール通知機能
- [ ] Amazon QuickSight ダッシュボード
- [ ] 過去データのトレンド分析
- [ ] CVSS v4.0 対応
- [ ] Slack/Teams 連携

---

## プロジェクト構造

```
vulnerability-management-system/
├── README.md                          # このファイル
├── app.py                             # CDK アプリエントリーポイント
├── cdk.json                           # CDK 設定
├── requirements.txt                   # CDK 依存関係
├── .gitignore
│
├── cdk/                               # CDK スタック
│   ├── __init__.py
│   └── stacks/
│       ├── __init__.py
│       ├── database_stack.py          # DynamoDB + S3
│       ├── lambda_stack.py            # Lambda 関数
│       └── eventbridge_stack.py       # EventBridge + Step Functions
│
├── lambda/                            # Lambda 関数
│   ├── common/                        # 共通ライブラリ
│   │   ├── logger.py
│   │   ├── bedrock_client.py
│   │   └── dynamodb_client.py
│   ├── collect_vulnerabilities/       # 脆弱性収集
│   │   ├── handler.py
│   │   ├── sources/
│   │   │   ├── jvn.py
│   │   │   ├── ipa.py (Phase 2)
│   │   │   ├── jpcert.py (Phase 2)
│   │   │   └── nvd.py (Phase 2)
│   │   └── requirements.txt
│   ├── analyze_vulnerabilities/       # AI分析
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── match_assets/                  # 資産照合
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── collect_vendor_info/           # ベンダー情報収集
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── generate_report/               # 報告書生成
│       ├── handler.py
│       ├── templates/
│       │   ├── executive_summary.md
│       │   └── technical_detail.md
│       └── requirements.txt
│
├── config/                            # 設定ファイル
│   ├── sources.json                   # 脆弱性情報源
│   └── vendors.json                   # ベンダー情報
│
├── scripts/                           # ユーティリティスクリプト
│   ├── setup_sample_data.py           # サンプルデータ投入
│   └── manual_trigger.py              # 手動実行
│
└── tests/                             # テスト
    ├── unit/
    │   ├── test_jvn_collector.py
    │   └── test_bedrock_client.py
    └── requirements.txt
```

---

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

---

## 貢献

バグ報告や機能リクエストは、GitHubのIssueでお願いします。

---

## サポート

質問やサポートが必要な場合は、以下にお問い合わせください:

- GitHub Issues: [リポジトリURL]/issues
- Email: support@example.com

---

## 変更履歴

### v1.0.0 (Phase 1) - 2024-11-03

- 初回リリース
- JVN からの脆弱性情報収集
- Amazon Bedrock による AI分析
- 基本的な報告書生成
- Step Functions による自動ワークフロー
- 週次スケジュール実行

---

**開発者**: 情報システム部
**最終更新**: 2024年11月3日
