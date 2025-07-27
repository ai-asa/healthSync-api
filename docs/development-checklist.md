# 開発チェックリスト

## MVP実装時の標準チェックリスト

### 1. TDD開始前
- [ ] 設計書（docs/design.md）の該当箇所を確認
- [ ] 必要なディレクトリ構造が存在することを確認
- [ ] 依存関係が requirements.txt に含まれているか確認

### 2. テスト作成（Red Phase）
- [ ] テストファイルを適切な場所に作成
- [ ] 失敗するテストを書く（最低3ケース）
  - [ ] 正常系
  - [ ] 異常系
  - [ ] エッジケース
- [ ] テストが失敗することを確認

### 3. 実装（Green Phase）
- [ ] 最小限の実装でテストをパス
- [ ] 型ヒントを追加
- [ ] docstringを記述（Google Style）

### 4. リファクタリング（Refactor Phase）
- [ ] コードの重複を除去
- [ ] 命名を改善
- [ ] 設計パターンを適用（必要に応じて）

### 5. 品質チェック
- [ ] `make test` - 全テストがパス
- [ ] `make lint` - リントエラーなし
- [ ] `make format` - コードフォーマット
- [ ] `make type-check` - 型エラーなし
- [ ] カバレッジ80%以上

### 6. 統合確認
- [ ] 開発サーバーで動作確認
- [ ] ログ出力の確認
- [ ] エラーハンドリングの確認

### 7. ドキュメント更新
- [ ] development-progress.md を更新
- [ ] 必要に応じてREADMEを更新
- [ ] APIドキュメント（自動生成）の確認

## コードレビューチェックリスト

### セキュリティ
- [ ] 秘密情報がハードコードされていない
- [ ] 入力値の検証が適切
- [ ] SQLインジェクション対策
- [ ] 認証・認可が適切

### パフォーマンス
- [ ] N+1問題がない
- [ ] 適切なインデックスが設定されている
- [ ] 不要なクエリがない
- [ ] キャッシュの活用

### 保守性
- [ ] 単一責任の原則
- [ ] DRY原則
- [ ] 適切な抽象化
- [ ] テストが書きやすい設計

## トラブルシューティング

### よくある問題と解決法

1. **ModuleNotFoundError: No module named 'core'**
   ```bash
   PYTHONPATH=src uvicorn src.main:app --reload
   ```

2. **Address already in use**
   ```bash
   # プロセスを確認
   lsof -i :8000
   # または別ポートを使用
   uvicorn src.main:app --port 8001
   ```

3. **仮想環境の問題**
   ```bash
   # 再作成
   rm -rf .venv
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements-dev.txt
   ```

4. **テストのStringIO問題**
   - `patch("sys.stdout", output)` は `configure_logging()` の前に実行

## Git コミットメッセージ規約

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
perf: パフォーマンス改善
test: テスト追加・修正
chore: ビルド・補助ツール
```

例:
```
feat: add measurement entity with validation
test: add unit tests for measurement entity
docs: update development progress for MVP3
```