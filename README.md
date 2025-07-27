# HealthSync API

iOS HealthKitと連携するヘルスケアデータ収集・分析APIシステム

## 開発環境セットアップ

### 前提条件
- Python 3.11+ (推奨: 3.11.9)
- Docker Desktop
- uv (高速パッケージマネージャー)

### クイックスタート

1. **uvのインストール**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **仮想環境の作成と有効化**
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **依存関係のインストール**
```bash
uv pip install -r requirements-dev.txt
```

4. **環境変数の設定**
```bash
cp .env.example .env
# .envファイルを編集
```

5. **MySQLの起動**
```bash
make db-up
# または: docker-compose up -d mysql
```

6. **テストの実行**
```bash
make test
```

7. **開発サーバーの起動**
```bash
make run-dev
# または: uvicorn src.main:app --reload
```

APIドキュメント: http://localhost:8000/docs

## 開発コマンド

```bash
make help           # 利用可能なコマンド一覧
make test-unit      # ユニットテストのみ実行
make lint           # コードの静的解析
make format         # コードフォーマット
make type-check     # 型チェック
```

## プロジェクト構造とドキュメント

### 設計・仕様
- `docs/design.md` - 詳細設計書（アーキテクチャ、ディレクトリ構造、技術仕様）

### 開発管理
- `docs/development-progress.md` - 開発進捗管理（MVP別の実装状況）
- `docs/development-checklist.md` - 開発チェックリスト（標準手順）
- `docs/development-tips.md` - 開発のヒントとベストプラクティス

### LLM向け
- `CLAUDE.md` - Claude向けプロジェクト固有の指示
- `AI_INSTRUCTIONS.md` - AI開発支援の注意事項