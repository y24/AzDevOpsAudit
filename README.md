# Azure DevOps 監査ツール

このツールは、Azure DevOpsのWorkItemとPull Requestの情報を収集し、ソース変更差分を計測するための情報を収集します。

## 機能

- WorkItemの階層関係に基づく関連チケットの収集
- Pull Request情報の収集と集計
- リポジトリ、ブランチ、コミット情報のサマリー生成
- レビュワー情報の収集

## 必要条件

- Python 3.7以上
- Azure DevOps Personal Access Token（PAT）
  - 必要な権限：
    - Work Items (Read)
    - Pull Requests (Read)
    - Code (Read)

## インストール

1. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
- `DEVOPS_PAT`: Azure DevOpsのPersonal Access Token
  - 環境変数が設定されていない場合は、実行時に入力を求められます

## 設定ファイル

`configs`ディレクトリに、以下の形式のJSONファイルを配置します：

```json
{
    "parent_feature_ids": "12345,12346",
    "backlog_ids": "23456,23457",
    "ignore_ids": "34567",
    "is_only_completed_item": true
}
```

- `parent_feature_ids`: 親となるFeatureのID（カンマ区切りで複数指定可能）
- `backlog_ids`: 処理対象とするProductBacklogItemのID（カンマ区切りで複数指定可能）
- `ignore_ids`: 無視するWorkItemのID（カンマ区切りで複数指定可能）
- `is_only_completed_item`: ステータスが完了のWorkItemのみを対象とするフラグ

## 使用方法

1. スクリプトを実行:
```bash
python src/main.py
```

2. プロンプトに従って以下の情報を入力:
- Azure DevOps組織名
- プロジェクト名
- Personal Access Token（環境変数未設定の場合）
- 使用する設定ファイル

## 出力

- `results`ディレクトリ:
  - `summary_[timestamp].json`: リポジトリ、ブランチ、コミット情報のサマリー
  - `pr_details_[timestamp].json`: 収集したすべてのPull Requestの詳細情報

- `logs`ディレクトリ:
  - `audit_[timestamp].log`: 実行ログ

## エラー処理

- APIリクエストエラー、認証エラーなどは適切にログに記録されます
- 処理は可能な限り継続され、エラーが発生した項目はスキップされます 