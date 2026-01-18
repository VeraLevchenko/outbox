from sqlalchemy import Column, Integer, String, Date, LargeBinary, DateTime
from sqlalchemy.sql import func
from app.models.database import Base


class OutboxJournal(Base):
    """Модель журнала исходящих документов"""
    __tablename__ = "outbox_journal"

    id = Column(Integer, primary_key=True, index=True)
    outgoing_no = Column(Integer, unique=True, nullable=False, index=True)
    outgoing_date = Column(Date, nullable=False)
    to_whom = Column(String, nullable=True)
    executor = Column(String, nullable=True)
    file_blob = Column(LargeBinary, nullable=True)  # PDF письма
    folder_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OutboxJournal(outgoing_no={self.outgoing_no}, date={self.outgoing_date})>"
