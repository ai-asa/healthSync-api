# CLAUDE.md - HealthSync API プロジェクトガイド

このドキュメントはClaude専用のプロジェクト固有の指示書です。

## プロジェクト概要

HealthSync APIは、iOS HealthKitと連携するヘルスケアデータ収集・分析APIシステムです。

## 重要な開発ルール

### 1. 開発方針
- **TDD（テスト駆動開発）**: 必ずテストを先に書く
- **MVP単位**: 1会話あたり2ファイル程度（テスト+実装）
- **構造化ロギング**: すべての重要な処理でstructlogを使用
- **型安全**: 型ヒントとmypy strictモードを使用

### 2. 開発手順
1. 必ず`docs/development-progress.md`で現在の進捗を確認
2. TodoWriteツールで作業中のタスクを管理
3. テストファーストで実装
4. カバレッジ80%以上を維持

### 3. 実行コマンド
```bash
# 仮想環境の有効化（必須）
source .venv/bin/activate

# テスト実行
pytest                          # 全テスト
pytest tests/unit/api -v       # 特定ディレクトリ
pytest --cov=src               # カバレッジ付き

# 開発サーバー（PYTHONPATHの設定が必要）
PYTHONPATH=src uvicorn src.main:app --reload --port 8000

# コード品質
make lint                      # 静的解析
make format                    # フォーマット
make type-check               # 型チェック
```

### 4. エラー対処
- **ModuleNotFoundError**: `PYTHONPATH=src`を設定
- **Address already in use**: 別ポート使用または既存プロセスを停止
- **仮想環境の問題**: `.venv`を削除して再作成

### 5. 進捗管理
MVP完了時に必ず更新：
- `docs/development-progress.md` - 進捗とチェックリスト
- TodoWriteツール - タスクのステータス

### 6. コミット・プッシュ・PR作成

**GitHub操作の手順：**
1. ブランチ作成: `git checkout -b feature/mvp-name`
2. 変更をステージング: `git add .`
3. コミット: `git commit -m "feat: add measurement entity"`
4. リモートURL設定: `git remote set-url origin https://ai-asa:$GH_TOKEN@github.com/ai-asa/healthSync-api.git`
5. プッシュ: `git push -u origin feature/mvp-name`
6. PR作成: `export GH_TOKEN="$(cat .env.local | grep GH_TOKEN | cut -d'=' -f2)" && gh pr create --base main --title "MVP3: Measurement entity" --body "..."`
7. セキュリティのため元に戻す: `git remote set-url origin https://github.com/ai-asa/healthSync-api.git`

**注意：** GH_TOKENは`.env.local`に保存されています。

**コミットメッセージ規約:**
- feat: 新機能
- fix: バグ修正
- test: テスト追加
- docs: ドキュメント更新
- refactor: リファクタリング