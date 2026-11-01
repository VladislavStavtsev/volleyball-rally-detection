import enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VideoStatus(str, enum.Enum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    completed = "completed"
    error = "error"


class JobStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    error = "error"


class ServeSide(str, enum.Enum):
    unknown = "unknown"
    near = "near"
    far = "far"


# ---------- Таблицы ----------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    duration: Mapped[float | None]
    fps: Mapped[float | None]
    width: Mapped[int | None]
    height: Mapped[int | None]
    status: Mapped[VideoStatus] = mapped_column(default=VideoStatus.uploaded)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    status: Mapped[JobStatus] = mapped_column(default=JobStatus.queued)
    progress: Mapped[int] = mapped_column(default=0)
    ball_csv_path: Mapped[str | None] = mapped_column(String(500))
    error_message: Mapped[str | None]
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]


class Rally(Base):
    __tablename__ = "rallies"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"))
    number: Mapped[int]
    start_time: Mapped[float]
    end_time: Mapped[float]
    start_frame: Mapped[int]
    end_frame: Mapped[int]
    serve_side: Mapped[ServeSide] = mapped_column(default=ServeSide.unknown)