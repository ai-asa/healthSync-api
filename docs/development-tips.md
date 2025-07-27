# 開発のヒントとベストプラクティス

## TDD（テスト駆動開発）のコツ

### 1. 小さく始める
最初は最もシンプルなテストケースから始めて、徐々に複雑なケースを追加していく。

```python
# ❌ 最初から複雑
def test_measurement_with_all_validations_and_edge_cases():
    # 100行のテスト...

# ✅ シンプルに始める
def test_measurement_creation_with_valid_data():
    measurement = Measurement(
        metric_type="heart_rate",
        value=72.0,
        measured_at=datetime.now()
    )
    assert measurement.metric_type == "heart_rate"
```

### 2. AAA パターン
```python
def test_example():
    # Arrange（準備）
    data = {"value": 72.0}
    
    # Act（実行）
    result = process_measurement(data)
    
    # Assert（検証）
    assert result.is_valid
```

### 3. テストの命名
- `test_` で始める
- 何をテストしているか明確に
- 期待される結果を含める

```python
# ❌ 不明確
def test_measurement():
    pass

# ✅ 明確
def test_measurement_creation_fails_with_negative_heart_rate():
    pass
```

## Pydantic モデルの設計

### 1. バリデーションの活用
```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class Measurement(BaseModel):
    metric_type: str = Field(..., regex="^(heart_rate|blood_pressure|weight)$")
    value: float = Field(..., gt=0, description="測定値")
    measured_at: datetime
    unit: Optional[str] = None
    
    @validator('measured_at')
    def validate_not_future(cls, v):
        if v > datetime.now():
            raise ValueError('測定日時は未来にできません')
        return v
```

### 2. Config クラスの活用
```python
class Measurement(BaseModel):
    # ...fields...
    
    class Config:
        # JSON Schema用の例を提供
        schema_extra = {
            "example": {
                "metric_type": "heart_rate",
                "value": 72.0,
                "measured_at": "2024-01-01T12:00:00Z",
                "unit": "bpm"
            }
        }
        # フィールド名の検証を厳格に
        extra = "forbid"
```

## 構造化ロギングの活用

### 1. コンテキスト情報の追加
```python
logger = get_logger(__name__)

# リクエスト処理の開始時
logger = logger.bind(
    request_id=str(uuid.uuid4()),
    user_id=current_user.id,
    endpoint=request.url.path
)

# 処理中
logger.info("Processing measurement", 
    metric_type=measurement.metric_type,
    value=measurement.value)
```

### 2. エラーログの書き方
```python
try:
    result = process_measurement(data)
except ValidationError as e:
    logger.error("Validation failed",
        error_type=type(e).__name__,
        error_details=e.errors(),
        input_data=data)
    raise
```

## FastAPI のベストプラクティス

### 1. 依存性注入の活用
```python
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # ユーザー取得ロジック
    return user

@app.post("/measurements")
async def create_measurement(
    measurement: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user と db が自動的に注入される
    pass
```

### 2. レスポンスモデルの分離
```python
# リクエスト用
class MeasurementCreate(BaseModel):
    metric_type: str
    value: float
    measured_at: datetime

# レスポンス用
class MeasurementResponse(MeasurementCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemyモデルから変換
```

## パフォーマンスのヒント

### 1. 非同期処理の活用
```python
# ❌ 同期的に処理
def get_user_stats(user_id: int):
    measurements = get_measurements(user_id)  # ブロッキング
    goals = get_goals(user_id)  # ブロッキング
    return calculate_stats(measurements, goals)

# ✅ 非同期で並列処理
async def get_user_stats(user_id: int):
    measurements, goals = await asyncio.gather(
        get_measurements_async(user_id),
        get_goals_async(user_id)
    )
    return calculate_stats(measurements, goals)
```

### 2. バルク操作の活用
```python
# ❌ N+1問題
for data in measurements_data:
    measurement = Measurement(**data)
    db.add(measurement)
    db.commit()  # 毎回コミット

# ✅ バルクインサート
measurements = [Measurement(**data) for data in measurements_data]
db.add_all(measurements)
db.commit()  # 一度だけコミット
```

## デバッグのヒント

### 1. ログを活用した問題追跡
```python
# 処理の開始と終了をログ
logger.info("Starting bulk measurement import", count=len(data))
try:
    result = import_measurements(data)
    logger.info("Bulk import completed", 
        success_count=result.success_count,
        error_count=result.error_count,
        duration_ms=elapsed_ms)
except Exception as e:
    logger.exception("Bulk import failed")
    raise
```

### 2. pytest でのデバッグ
```bash
# 特定のテストのみ実行
pytest tests/unit/domain/test_measurement_entity.py::test_specific_case -v

# print文を表示
pytest -s

# 失敗時にpdbを起動
pytest --pdb

# 最初の失敗で停止
pytest -x
```

## よくあるパターン

### Repository パターン
```python
class MeasurementRepository:
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, measurement: MeasurementCreate) -> Measurement:
        db_measurement = MeasurementModel(**measurement.dict())
        self.db.add(db_measurement)
        await self.db.commit()
        await self.db.refresh(db_measurement)
        return Measurement.from_orm(db_measurement)
    
    async def get_by_user_id(self, user_id: int) -> List[Measurement]:
        query = select(MeasurementModel).where(
            MeasurementModel.user_id == user_id
        )
        result = await self.db.execute(query)
        return [Measurement.from_orm(m) for m in result.scalars()]
```

### Service レイヤー
```python
class MeasurementService:
    def __init__(self, repository: MeasurementRepository):
        self.repository = repository
        self.logger = get_logger(__name__)
    
    async def create_measurement(
        self, 
        data: MeasurementCreate,
        user_id: int
    ) -> MeasurementResponse:
        self.logger.info("Creating measurement", 
            user_id=user_id,
            metric_type=data.metric_type)
        
        # ビジネスロジック
        if not self._is_valid_measurement(data):
            raise ValidationError("Invalid measurement")
        
        # リポジトリを通じて保存
        measurement = await self.repository.create(data)
        
        # イベント発行など
        await self._publish_measurement_created(measurement)
        
        return MeasurementResponse.from_orm(measurement)
```