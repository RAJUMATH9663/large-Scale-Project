from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.models import Dataset, Prediction, User
from app.utils.auth import get_current_user
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

router = APIRouter(prefix="/api/predict", tags=["Predictions"])


class PredictRequest(BaseModel):
    dataset_id: int
    target_column: str
    model_type: str = "random_forest"  # linear | random_forest | gradient_boost
    feature_columns: Optional[List[str]] = None
    test_size: float = 0.2


@router.post("/train")
async def train_model(
    payload: PredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)

    if payload.target_column not in df.columns:
        raise HTTPException(400, f"Target column '{payload.target_column}' not found")

    # Feature selection
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = payload.feature_columns or [c for c in numeric_cols if c != payload.target_column]
    feature_cols = [c for c in feature_cols if c in df.columns and c != payload.target_column]

    if not feature_cols:
        raise HTTPException(400, "No valid feature columns found")

    df_clean = df[feature_cols + [payload.target_column]].dropna()
    X = df_clean[feature_cols]
    y = df_clean[payload.target_column]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=payload.test_size, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model_map = {
        "linear": LinearRegression(),
        "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "gradient_boost": GradientBoostingRegressor(n_estimators=100, random_state=42),
    }
    model = model_map.get(payload.model_type, model_map["random_forest"])
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    metrics = {
        "r2_score": round(float(r2_score(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }

    # Feature importance
    feature_importance = {}
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
        feature_importance = dict(sorted(
            {col: round(float(imp), 4) for col, imp in zip(feature_cols, importance)}.items(),
            key=lambda x: x[1], reverse=True
        ))

    # Forecast data (actual vs predicted)
    forecast_data = {
        "actual": y_test.tolist()[:50],
        "predicted": y_pred.tolist()[:50],
    }

    prediction = Prediction(
        dataset_id=payload.dataset_id,
        target_column=payload.target_column,
        model_type=payload.model_type,
        metrics=metrics,
        feature_importance=feature_importance,
        forecast_data=forecast_data,
    )
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)

    return {
        "prediction_id": prediction.id,
        "model_type": payload.model_type,
        "target_column": payload.target_column,
        "feature_columns": feature_cols,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "forecast_data": forecast_data,
    }


@router.get("/{dataset_id}")
async def list_predictions(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Prediction).where(Prediction.dataset_id == dataset_id))
    predictions = result.scalars().all()
    return [
        {"id": p.id, "target_column": p.target_column, "model_type": p.model_type,
         "metrics": p.metrics, "created_at": p.created_at}
        for p in predictions
    ]
