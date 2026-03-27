from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")  # user | admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    datasets = relationship("Dataset", back_populates="owner")
    queries = relationship("QueryHistory", back_populates="user")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)  # csv | pdf
    rows = Column(Integer, default=0)
    columns = Column(Integer, default=0)
    size_bytes = Column(Integer, default=0)
    version = Column(Integer, default=1)
    status = Column(String, default="ready")  # uploading | processing | ready | error
    meta = Column(JSON, default={})
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="datasets")
    predictions = relationship("Prediction", back_populates="dataset")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dataset_id = Column(Integer, nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text)
    model_used = Column(String)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0)
    accuracy_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="queries")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    target_column = Column(String)
    model_type = Column(String)  # linear | random_forest | gradient_boost
    metrics = Column(JSON, default={})
    feature_importance = Column(JSON, default={})
    forecast_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="predictions")


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, nullable=True)
    variables = Column(JSON, default={})
    results = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("query_history.id"), nullable=True)
    context_recall = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    raw_scores = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class MonitoringLog(Base):
    __tablename__ = "monitoring_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String)
    method = Column(String)
    status_code = Column(Integer)
    latency_ms = Column(Float)
    user_id = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
