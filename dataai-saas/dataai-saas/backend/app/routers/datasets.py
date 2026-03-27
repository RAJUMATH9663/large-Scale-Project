import os, shutil, uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Dataset, User
from app.utils.auth import get_current_user
from app.config import get_settings
import pandas as pd

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])
settings = get_settings()

ALLOWED_TYPES = {"text/csv", "application/pdf", "application/vnd.ms-excel",
                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


@router.post("/upload", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(400, f"File too large. Max {settings.MAX_FILE_SIZE_MB}MB")

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse CSV metadata
    rows, cols, meta = 0, 0, {}
    file_type = "csv" if file.filename.endswith(".csv") else "pdf"
    if file_type == "csv":
        try:
            df = pd.read_csv(file_path, nrows=5)
            df_full = pd.read_csv(file_path)
            rows, cols = df_full.shape
            meta = {
                "columns": df_full.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df_full.dtypes.items()},
                "preview": df.to_dict(orient="records"),
                "missing": df_full.isnull().sum().to_dict(),
            }
        except Exception as e:
            meta = {"error": str(e)}

    dataset = Dataset(
        name=file.filename,
        filename=unique_name,
        file_path=file_path,
        file_type=file_type,
        rows=rows,
        columns=cols,
        size_bytes=len(content),
        meta=meta,
        owner_id=current_user.id,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    return {
        "id": dataset.id,
        "name": dataset.name,
        "rows": dataset.rows,
        "columns": dataset.columns,
        "file_type": dataset.file_type,
        "size_bytes": dataset.size_bytes,
        "meta": dataset.meta,
        "created_at": dataset.created_at,
    }


@router.get("/")
async def list_datasets(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Dataset).where(Dataset.owner_id == current_user.id).order_by(Dataset.created_at.desc()))
    datasets = result.scalars().all()
    return [
        {"id": d.id, "name": d.name, "rows": d.rows, "columns": d.columns,
         "file_type": d.file_type, "status": d.status, "created_at": d.created_at}
        for d in datasets
    ]


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    return {
        "id": dataset.id, "name": dataset.name, "rows": dataset.rows,
        "columns": dataset.columns, "file_type": dataset.file_type,
        "status": dataset.status, "meta": dataset.meta,
        "created_at": dataset.created_at, "version": dataset.version,
    }


@router.get("/{dataset_id}/stats")
async def dataset_stats(dataset_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    if dataset.file_type != "csv":
        raise HTTPException(400, "Stats only available for CSV datasets")
    try:
        df = pd.read_csv(dataset.file_path)
        desc = df.describe(include="all").fillna("").to_dict()
        return {
            "shape": {"rows": df.shape[0], "cols": df.shape[1]},
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing": df.isnull().sum().to_dict(),
            "describe": desc,
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    await db.delete(dataset)
    await db.commit()
