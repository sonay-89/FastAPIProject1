from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

app = FastAPI(title="Incidents API", version="0.1.0")


# Database setup (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./incidents.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class IncidentStatus(str, PyEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


# Schemas
class IncidentCreate(BaseModel):
    description: str
    source: str
    status: Optional[IncidentStatus] = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    description: str
    status: IncidentStatus
    source: str
    created_at: datetime


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


# Incidents API
@app.post(
    "/incidents",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an incident",
)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    new_incident = Incident(
        description=payload.description,
        source=payload.source,
        status=(payload.status or IncidentStatus.open).value,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return IncidentRead.model_validate(new_incident)


@app.get(
    "/incidents",
    response_model=List[IncidentRead],
    summary="List incidents with optional status filter",
)
def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(
        default=None,
        alias="status",
        description="Filter by status: open, in_progress, resolved, closed",
    ),
    db: Session = Depends(get_db),
) -> List[IncidentRead]:
    stmt = select(Incident)
    if status_filter is not None:
        stmt = stmt.where(Incident.status == status_filter.value)
    stmt = stmt.order_by(Incident.created_at.desc(), Incident.id.desc())
    incidents = db.execute(stmt).scalars().all()
    return [IncidentRead.model_validate(i) for i in incidents]


@app.patch(
    "/incidents/{incident_id}/status",
    response_model=IncidentRead,
    summary="Update incident status by id",
)
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
) -> IncidentRead:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    incident.status = payload.status.value
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return IncidentRead.model_validate(incident)


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentRead,
    summary="Get incident by id",
)
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> IncidentRead:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return IncidentRead.model_validate(incident)
