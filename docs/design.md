# HealthSync API 詳細設計書

## 1. プロジェクト概要

iOS HealthKitと連携し、ヘルスケアデータを収集・分析・可視化するバックエンドAPIシステム。
テスト駆動開発（TDD）アプローチで、MVPから段階的に機能を拡張していく。

### アーキテクチャ選択
- **MVP (Phase 1-3)**: API Gateway + Lambda + RDS Proxy + Aurora MySQL Serverless v2
- **将来拡張**: Fargate移行オプション（トラフィック増大時）

## 2. ディレクトリ構成と責務範囲

### 現在の実装済み構成（MVP1-6完了時点）

```
healthsync-api/
├── src/                        # アプリケーションソースコード
│   ├── api/                    # APIレイヤー（FastAPI）
│   │   └── v1/                 # APIバージョン1
│   │       ├── dependencies/   # 依存性注入
│   │       │   └── auth.py     # JWT認証・認可（HTTPBearer401含む）
│   │       └── endpoints/      # エンドポイント定義
│   │           └── measurements.py    # 測定データAPI（認証付き）
│   ├── core/                   # アプリケーション設定・共通機能
│   │   ├── __init__.py
│   │   ├── logging.py          # ロギング設定（structlog）
│   │   └── security.py         # セキュリティ設定（JWT設定）
│   ├── domain/                 # ビジネスロジック層
│   │   └── entities/           # ドメインエンティティ（Pydantic）
│   │       ├── __init__.py
│   │       ├── measurement.py  # 測定データエンティティ
│   │       └── user.py         # ユーザーエンティティ（UserInToken）
│   ├── schemas/                # APIスキーマ（Pydantic）
│   │   ├── requests/           # リクエストスキーマ
│   │   │   └── measurement.py
│   │   └── responses/          # レスポンススキーマ
│   │       └── measurement.py
│   └── main.py                 # アプリケーションエントリポイント
├── tests/                      # テストコード
│   ├── unit/                   # ユニットテスト
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── test_health.py         # ヘルスチェックテスト
│   │   │   ├── test_measurements_api.py # 測定APIテスト（認証含む）
│   │   │   └── test_auth.py           # JWT認証テスト
│   │   ├── core/
│   │   │   └── test_logging.py        # ロギング設定テスト
│   │   └── domain/
│   │       └── test_measurement_entity.py # エンティティテスト
│   ├── integration/            # 統合テスト
│   │   ├── __init__.py
│   │   └── test_api_auth_integration.py  # 認証フロー統合テスト
│   └── conftest.py             # pytest設定

### 将来の拡張予定構成

├── src/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── goals.py          # ゴール設定API（Phase 3）
│   │   │   ├── webhooks.py       # Webhook API（将来）
│   │   │   └── users.py          # ユーザー管理API（将来）
│   │   ├── dependencies/
│   │   │   └── database.py       # DB接続（MVP7）
│   │   └── middleware/           # ミドルウェア（将来）
│   │       ├── logging.py        # ロギング/トレーシング
│   │       └── error_handler.py  # 例外ハンドラ
│   ├── core/
│   │   ├── config.py             # 環境設定管理（MVP7）
│   │   └── exceptions.py         # カスタム例外定義（将来）
│   ├── domain/
│   │   ├── entities/
│   │   │   └── goal.py           # ゴールエンティティ（Phase 3）
│   │   ├── services/             # ドメインサービス（Phase 2-3）
│   │   └── ports/                # インターフェース定義（Phase 2-3）
│   ├── infrastructure/           # 技術的実装層（MVP7以降）
│   │   ├── database/             # データベース関連
│   │   └── adapters/             # 外部サービスアダプター（Phase 4）
│   └── schemas/
│       └── common.py             # 共通スキーマ（将来）
├── scripts/                    # ユーティリティスクリプト
│   ├── db_init.py
│   ├── seed_data.py
│   ├── analyze_slow_query.py  # MySQL slow query分析
│   └── performance_test.py
├── iac/                        # Infrastructure as Code
│   ├── terraform/              # Terraform設定
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── modules/
│   │       ├── network/        # VPC, Subnet, Security Group
│   │       ├── api_gateway/
│   │       ├── lambda/
│   │       ├── rds_proxy/
│   │       └── aurora_mysql/
│   └── docker/                 # Docker設定
│       ├── Dockerfile          # マルチステージビルド
│       └── docker-compose.yml  # MySQL 8.0含む
├── .github/                    # GitHub Actions
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── codeql.yml
├── docs/                       # ドキュメント
│   ├── api/                    # API仕様書
│   ├── architecture/           # アーキテクチャ図
│   ├── performance/            # パフォーマンスガイド
│   │   └── mysql_tuning.md    # MySQLチューニング詳細
│   └── development/            # 開発ガイド
├── .env.example                # 環境変数サンプル
├── .gitignore
├── .python-version            # Python 3.11.9を指定
├── requirements.txt            # 本番用依存関係（pip freeze形式）
├── requirements-dev.txt        # 開発用依存関係
├── Makefile                    # タスクランナー
└── README.md

```

## 3. 各ディレクトリの責務

### src/api/
- **責務**: HTTPリクエスト/レスポンスの処理、ルーティング、認証・認可、ロギング・エラーハンドリング
- **依存**: domain層、schemas、FastAPI
- **テスト方針**: エンドポイントごとのリクエスト/レスポンステスト、エラーケーステスト

### src/core/
- **責務**: アプリケーション設定、ロギング設定、共通例外定義、セキュリティユーティリティ
- **依存**: 最小限の外部ライブラリ（pydantic-settings、structlog等）
- **テスト方針**: ユニットテストで100%カバレッジ（auto-generated除く）

### src/domain/
- **責務**: ビジネスロジック、ドメインルール、ポート（インターフェース）定義
- **依存**: なし（Pure Python + Pydanticエンティティ）
- **テスト方針**: ビジネスロジックの境界値テスト、異常系テスト、TDDによる実装

### src/infrastructure/
- **責務**: 技術的実装（DB接続、外部API連携）、ポートの実装
- **依存**: SQLAlchemy 2.0+、boto3、httpx等
- **テスト方針**: testcontainersを使用した統合テスト、LocalStackでのAWS連携テスト

### src/schemas/
- **責務**: APIリクエスト/レスポンスのバリデーション、シリアライゼーション
- **依存**: Pydantic v2
- **テスト方針**: バリデーションルールのテスト、エッジケーステスト

## 4. MVP開発フロー

### Phase 1: 基本API（Week 1）
```
実装済みMVP:
MVP1: ヘルスチェックAPI
- GET /health エンドポイント
- ステータス、タイムスタンプ、バージョン情報を返却

MVP2: 構造化ロギング基盤
- structlogによるJSON形式のロギング
- タイムスタンプ、ログレベル、コンテキスト情報の付与

MVP3: Measurementエンティティ定義
- Pydantic v2によるドメインモデル
- 10種類のヘルスメトリック（心拍数、血圧、体重等）
- 値の範囲検証、単位検証、未来日時の拒否

MVP4: 測定データ一括登録API（認証なし）
- POST /v1/measurements/bulk エンドポイント
- 2段階バリデーション方式（生データ→Pydantic→ドメイン）
- 207 Multi-Statusによる部分成功のサポート
- エラーの詳細情報を含むレスポンス

MVP5: JWT認証基盤
- src/api/v1/dependencies/auth.py: JWT生成・検証関数
- src/core/security.py: セキュリティ設定（SECRET_KEY、ALGORITHM）
- src/domain/entities/user.py: UserInTokenモデル（user_id、email）
- 有効期限のカスタマイズ対応（デフォルト30分）

MVP6: 認証付きAPI統合
- 測定データAPIにJWT認証を統合
- HTTPBearer401クラスで403→401エラーに統一
- get_current_user依存関数による保護
- 統合テストでフルフローを検証

実装上の変更点:
- 当初の想定より細かくMVPを分割（1→6）
- UserInTokenモデルで'sub'ではなく'user_id'フィールドを使用
- 認証なしの403エラーを401に変換するカスタムHTTPBearerクラスを追加
- 2段階バリデーション方式で柔軟なエラーハンドリングを実現
```

### Phase 2: データ取得と集計（Week 2）
```
MVP機能:
- 期間指定でのデータ取得（GET /v1/measurements/summary）
- MySQL最適化（インデックス設計）
- レスポンスキャッシュ

TDD手順:
1. 集計ロジックの失敗テスト: tests/unit/domain/test_measurement_service.py
2. ドメインサービス実装
3. MySQLクエリ最適化: EXPLAIN分析、複合インデックス追加
4. パフォーマンステスト: tests/performance/test_mysql_queries.py
   - 10万件データでのクエリ実行時間測定
   - slow_query_log分析
```

### Phase 3: ゴール機能（Week 3）
```
MVP機能:
- ゴール設定/更新（PUT /v1/goals/{goal_id}）
- ゴール達成判定ロジック
- 達成通知（モック実装）

TDD手順:
1. ゴールビジネスルールテスト: tests/unit/domain/test_goal_service.py
2. ドメインイベント実装（GoalAchievedEvent）
3. 通知サービスのポート定義とモック実装
4. E2Eシナリオテスト追加
```

### Phase 4: Lambda統合とAWS連携（Week 4）
```
MVP機能:
- Lambda + RDS Proxy設定
- S3へのデータアーカイブ
- SQS経由の非同期処理
- CloudWatch Logsへの構造化ログ

TDD手順:
1. LocalStackを使った統合テスト環境構築
2. アダプターテスト: tests/integration/test_aws_adapters.py
3. Lambda用requirements最適化（Lambda Layers活用）
4. Terraformでのインフラ構築
5. GitHub ActionsでのCI/CD完成
```

## 5. テスト戦略

### テストピラミッド
```
         /\
        /E2E\        15% - ユーザーシナリオ、非同期フロー
       /------\
      /統合テスト\    25% - API統合、DB接続、AWS連携
     /----------\
    /ユニットテスト\  60% - ビジネスロジック、ユーティリティ
   /--------------\
```

### テストツールとライブラリ

**requirements-dev.txt:**
```
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
factory-boy==3.3.0
freezegun==1.2.2
httpx==0.25.2
testcontainers==3.7.1
localstack==3.0.0
mutmut==2.4.4

# Linting and formatting
ruff==0.1.9
black==23.12.1
mypy==1.7.1
isort==5.13.2

# Development tools
ipython==8.19.0
watchdog==3.0.0
```

### テスト実行コマンド
```bash
# ユニットテストのみ
make test-unit

# 統合テスト（MySQL コンテナ起動込み）
make test-integration

# パフォーマンステスト
make test-performance

# カバレッジレポート付き（目標: 85%）
make test-coverage

# Mutation testing
make test-mutation

# 特定のマーカーでテスト
pytest -m "not slow"
```

### テストデータ管理
- Factory Boyによる一貫性のあるテストデータ生成
- 各テストはpytest-xdistで並列実行可能
- テストごとに独立したDBトランザクション（pytest-asyncio）
- パフォーマンステスト用の大量データ生成スクリプト

## 6. CI/CDパイプライン

### GitHub Actions ワークフロー
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: 
  push:
    branches: [main, develop]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install Poetry
        uses: snok/install-poetry@v1
      - name: Lint (ruff + black + mypy)
        run: |
          make lint
      - name: Security scan (bandit + safety)
        run: |
          make security-check
      - name: Unit tests
        run: |
          make test-unit
      - name: Integration tests
        run: |
          make test-integration
      - name: Coverage report
        run: |
          make test-coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: |
          make docker-build
      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
      - name: Push to ECR
        if: github.ref == 'refs/heads/main'
        run: |
          make docker-push
```

### デプロイメントフロー
```
feature/* → develop → staging → main
   ↓          ↓         ↓         ↓
  Local     Dev/QA   Staging   Production
  Docker    Lambda   Lambda    Lambda+RDS Proxy
```

## 7. 開発規約

### コーディング規約
- PEP 8準拠（Ruff + Black使用）
- 型ヒント必須（mypy strict mode）
- docstring（Google Style）必須
- 最大行長: 88文字（Black準拠）
- インポート順序: isortで自動整形

### 依存関係管理（uv使用）

**requirements.txt（本番用）:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
alembic==1.12.1
pydantic==2.5.2
pydantic-settings==2.1.0
boto3==1.34.14
structlog==23.2.0
httpx==0.25.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiomysql==0.2.0
pymysql==1.1.0
```

**pyproject.toml（ツール設定のみ）:**
```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W", "B", "C90", "UP"]
ignore = ["E501"]
target-version = "py311"

[tool.mypy]
strict = true
python_version = "3.11"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### ブランチ戦略
```
main            - 本番環境
develop         - 開発統合ブランチ
feature/*       - 機能開発
bugfix/*        - バグ修正
hotfix/*        - 緊急修正
```

### コミットメッセージ（Conventional Commits準拠）
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

## 8. パフォーマンス目標

### APIレスポンスタイム（負荷条件: 100同時接続、平均ペイロード1KB）
- 95パーセンタイル: < 200ms
- 99パーセンタイル: < 500ms
- エラー率: < 0.1%

### スループット
- 目標: 1000 requests/second
- Lambda同時実行数: 100（予約済み同時実行）
- RDS Proxy接続プール: 最大100

### MySQL パフォーマンス基準
- 単純SELECT: < 10ms
- 集計クエリ（1週間分、10万レコード）: < 100ms
- バルクINSERT（1000件）: < 50ms
- インデックス使用率: 95%以上（EXPLAIN確認）

### 負荷テストシナリオ（k6使用）
```javascript
// tests/performance/load_test.k6.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },  // ramp-up
    { duration: '5m', target: 100 },  // stay
    { duration: '2m', target: 0 },    // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.001'],
  },
};
```

## 9. セキュリティ要件

### 認証・認可
- JWT Bearer Token
- リフレッシュトークン実装
- Rate Limiting（100 requests/minute/user）

### データ保護
- 保存時暗号化（RDS暗号化）
- 転送時暗号化（TLS 1.2以上）
- PII（個人識別情報）のマスキング

### 監査
- 全APIアクセスログ
- 変更履歴の保持
- GDPR/HIPAA準拠を想定した設計

## 10. ロギング・監視設計

### 構造化ログ設定
```python
# src/core/logging.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.dict_tracebacks,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### CloudWatch Logs Insights クエリ例
```sql
fields @timestamp, correlation_id, user_id, duration_ms, status_code
| filter @message like /API Request/
| stats avg(duration_ms), pct(duration_ms, 95), pct(duration_ms, 99) by bin(5m)
```

## 11. MySQLパフォーマンスチューニング

### インデックス設計指針
```sql
-- 複合インデックス例（測定データの期間検索用）
CREATE INDEX idx_measurements_user_date ON measurements(user_id, measured_at DESC);

-- カバリングインデックス（集計クエリ高速化）
CREATE INDEX idx_measurements_summary ON measurements(
    user_id, 
    measured_at, 
    metric_type, 
    value,
    id  -- MySQLでは最後に含める
);

-- パーティショニング（月単位）
ALTER TABLE measurements
PARTITION BY RANGE (YEAR(measured_at) * 100 + MONTH(measured_at)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    -- ...
);
```

### slow_query_log分析手順
1. 有効化: `SET GLOBAL slow_query_log = 'ON';`
2. 閾値設定: `SET GLOBAL long_query_time = 0.1;`
3. 分析ツール: `pt-query-digest`使用
4. 改善前後のEXPLAIN比較をドキュメント化

### クエリ最適化例
```python
# Before（N+1問題）
users = await session.execute(select(User))
for user in users:
    goals = await session.execute(
        select(Goal).where(Goal.user_id == user.id)
    )

# After（JOINで一括取得）
result = await session.execute(
    select(User, Goal)
    .join(Goal, User.id == Goal.user_id)
    .options(selectinload(User.goals))
)
```

## 12. ドメインエンティティ詳細仕様

### Measurementエンティティ

#### MetricType（測定タイプ）
```python
class MetricType(str, Enum):
    HEART_RATE = "heart_rate"                    # 心拍数
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic"   # 収縮期血圧
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic" # 拡張期血圧
    BODY_WEIGHT = "body_weight"                  # 体重
    BODY_TEMPERATURE = "body_temperature"        # 体温
    BLOOD_GLUCOSE = "blood_glucose"              # 血糖値
    OXYGEN_SATURATION = "oxygen_saturation"      # 血中酸素飽和度
    STEPS = "steps"                              # 歩数
    DISTANCE = "distance"                        # 移動距離
    CALORIES_BURNED = "calories_burned"          # 消費カロリー
```

#### バリデーションルール

**値の範囲（VALUE_RANGES）:**
| メトリックタイプ | 最小値 | 最大値 | 単位例 |
|-----------------|-------|--------|--------|
| HEART_RATE | 20.0 | 250.0 | bpm |
| BLOOD_PRESSURE_SYSTOLIC | 50.0 | 250.0 | mmHg |
| BLOOD_PRESSURE_DIASTOLIC | 30.0 | 150.0 | mmHg |
| BODY_WEIGHT | 0.1 | 500.0 | kg, lb |
| BODY_TEMPERATURE | 25.0 | 45.0 | °C, °F |
| BLOOD_GLUCOSE | 20.0 | 600.0 | mg/dL, mmol/L |
| OXYGEN_SATURATION | 50.0 | 100.0 | % |
| STEPS | 0.0 | 100000.0 | steps |
| DISTANCE | 0.0 | 1000000.0 | m, km, mi |
| CALORIES_BURNED | 0.0 | 10000.0 | kcal, cal |

**有効な単位（VALID_UNITS）:**
```python
VALID_UNITS = {
    MetricType.HEART_RATE: {"bpm", "beats/min"},
    MetricType.BLOOD_PRESSURE_SYSTOLIC: {"mmHg"},
    MetricType.BLOOD_PRESSURE_DIASTOLIC: {"mmHg"},
    MetricType.BODY_WEIGHT: {"kg", "lb"},
    MetricType.BODY_TEMPERATURE: {"°C", "°F"},
    MetricType.BLOOD_GLUCOSE: {"mg/dL", "mmol/L"},
    MetricType.OXYGEN_SATURATION: {"%"},
    MetricType.STEPS: {"steps"},
    MetricType.DISTANCE: {"m", "km", "mi"},
    MetricType.CALORIES_BURNED: {"kcal", "cal"},
}
```

#### エンティティフィールド
```python
class Measurement(BaseModel):
    metric_type: MetricType          # 測定タイプ（必須）
    value: float                     # 測定値（必須、正の数）
    unit: str                        # 単位（必須、メトリックタイプに応じた検証）
    measured_at: datetime            # 測定日時（必須、未来の日時は不可）
    device_id: Optional[str]         # 測定デバイスID
    metadata: Optional[Dict[str, Any]]  # 追加メタデータ
    notes: Optional[str]             # メモ
```

#### 技術的実装
- Pydantic v2使用（ConfigDict、field_validator、model_validator）
- JSON出力時のみdatetimeをISO形式にシリアライズ（field_serializer）
- 厳密な型チェックとバリデーション
- エラーメッセージの明確化（特に心拍数の範囲エラー）

## 13. 例外処理とエラーハンドリング

### 共通例外定義
```python
# src/core/exceptions.py
class HealthSyncException(Exception):
    """Base exception for all application errors"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class NotFoundError(HealthSyncException):
    """Resource not found"""
    def __init__(self, resource: str, id: str):
        super().__init__(
            message=f"{resource} with id {id} not found",
            error_code="RESOURCE_NOT_FOUND"
        )

class ValidationError(HealthSyncException):
    """Business rule validation error"""
    pass

class AuthenticationError(HealthSyncException):
    """Authentication failed"""
    pass
```

### グローバルエラーハンドラ
```python
# src/api/v1/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

async def error_handler(request: Request, exc: Exception):
    correlation_id = request.state.correlation_id
    
    if isinstance(exc, NotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            correlation_id=correlation_id,
            path=request.url.path
        )
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": getattr(exc, "error_code", "INTERNAL_ERROR"),
                "message": getattr(exc, "message", "Internal server error"),
                "correlation_id": correlation_id
            }
        }
    )
```

## 14. APIバリデーション戦略

### 測定データ一括登録API（/v1/measurements/bulk）

#### 2段階バリデーション方式
MVP4の実装で採用した方式：

1. **リクエストレベル**: 生のDict配列を受け取る
   ```python
   measurements_data: List[Dict[str, Any]] = Body(...)
   ```
   - FastAPIの自動バリデーションを回避
   - すべてのエラーを収集可能

2. **アプリケーションレベル**: 個別にバリデーション
   - Pydanticモデル（MeasurementCreateRequest）でスキーマ検証
   - ドメインエンティティ（Measurement）でビジネスルール検証

#### レスポンス戦略
```python
# 成功時（201 Created）
{
    "success_count": 3,
    "failed_count": 0,
    "measurements": [
        {
            "id": "uuid",
            "metric_type": "heart_rate",
            "value": 72.0,
            "unit": "bpm",
            "measured_at": "2025-01-01T12:00:00Z",
            "created_at": "2025-01-01T12:00:01Z"
        }
    ]
}

# 一部失敗時（207 Multi-Status）
{
    "success_count": 2,
    "failed_count": 1,
    "measurements": [...],
    "errors": [
        {
            "index": 1,
            "message": "Heart rate value 300.0 is out of range",
            "field": "value"
        }
    ]
}

# 全失敗時（422 Unprocessable Entity）
{
    "detail": [
        {
            "index": 0,
            "message": "Invalid metric type",
            "field": "metric_type"
        }
    ]
}
```

## 15. 開発環境セットアップ

### 開発環境戦略
本プロジェクトではハイブリッドアプローチを採用：
- **ローカル開発**: uv + 仮想環境（高速な開発イテレーション）
- **データベース**: Docker Compose（MySQLコンテナ）
- **統合テスト/本番**: 完全Docker化（再現性の確保）

## 16. 実装上の主要な変更点（2025-07-27時点）

### 設計からの変更内容

1. **MVP分割の細分化**
   - 当初想定: Phase 1で認証含む全機能実装
   - 実際: MVP1-6に細分化し、段階的に実装
   - 理由: TDDアプローチの徹底とリスク軽減

2. **ディレクトリ構成の簡素化**
   - 当初設計: 完全なクリーンアーキテクチャ
   - 実際: 最小限の構成からスタート
   - 理由: YAGNIの原則に従い、必要に応じて拡張

3. **認証実装の変更**
   - HTTPBearer401クラスの追加（403→401変換）
   - UserInTokenモデルで`user_id`フィールドを使用（`sub`ではなく）
   - 理由: FastAPIのデフォルト動作との整合性

4. **バリデーション戦略**
   - 2段階バリデーション方式の採用
   - 生データ→Pydanticスキーマ→ドメインエンティティ
   - 理由: 柔軟なエラーハンドリングと部分成功のサポート

### 今後の実装計画

**MVP7: Docker/MySQL統合**
- MySQLコンテナのセットアップ
- SQLAlchemyモデルの実装
- データベース接続管理

**Phase 2以降**
- データ取得・集計API
- ゴール機能
- AWS Lambda統合
- パフォーマンスチューニング

### 前提条件
- Python 3.11+（pyenvで3.11.9推奨）
- Docker Desktop
- AWS CLI設定済み
- uv（高速パッケージマネージャー）

### 初期セットアップ
```bash
# リポジトリクローン
git clone https://github.com/your-org/healthsync-api.git
cd healthsync-api

# uv インストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python 3.11.9 セットアップ（pyenv使用時）
pyenv install 3.11.9
pyenv local 3.11.9

# 仮想環境作成と依存関係インストール
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt -r requirements-dev.txt

# 環境変数設定
cp .env.example .env
# .envを編集

# MySQL起動（Docker Compose）
docker-compose up -d mysql

# データベース初期化
alembic upgrade head
python scripts/seed_data.py

# 開発サーバー起動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 開発用コマンド（Makefile）
```bash
make test          # 全テスト実行
make lint          # Ruff + Black + mypy
make format        # コードフォーマット
make run-dev       # 開発サーバー起動
make db-migrate    # Alembicマイグレーション作成
make docker-build  # マルチステージDockerビルド
make docs          # OpenAPIドキュメント生成
make perf-test     # k6パフォーマンステスト
```