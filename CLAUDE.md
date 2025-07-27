# CLAUDE.md - Mobile AI Assistant  プロジェクトガイド

このドキュメントはClaude専用のプロジェクト固有の指示書です。

## プロジェクト概要

Mobile AI Assistantは、AndroidとローカルPC場で動作するAIアシスタントです。

## 重要な開発ルール

### 1. コミット・プッシュ・PR作成

**GitHub操作の手順：**
1. ブランチ作成: `git checkout -b ブランチ名`
2. 変更をステージング: `git add .`
3. コミット: `git commit -m "コミットメッセージ"`
4. リモートURL設定: `git remote set-url origin https://ai-asa:$GH_TOKEN@github.com/ai-asa/mobile-ai-assistant.git`
5. プッシュ: `git push -u origin ブランチ名`
6. PR作成: `export GH_TOKEN="..." && gh pr create --base main --title "..." --body "..."`
7. セキュリティのため元に戻す: `git remote set-url origin https://github.com/ai-asa/mobile-ai-assistant.git`

**注意：** GH_TOKENは`.env.local`に保存されています。