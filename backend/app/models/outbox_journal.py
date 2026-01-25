from sqlalchemy import Column, Integer, String, Date, LargeBinary, DateTime
from sqlalchemy.sql import func
from app.models.database import Base


class OutboxJournal(Base):
    """Модель журнала исходящих документов"""
    __tablename__ = "outbox_journal"

    id = Column(Integer, primary_key=True, index=True)
    outgoing_no = Column(String, unique=True, nullable=False, index=True)  # Форматированный номер (например, "178-01")
    outgoing_date = Column(Date, nullable=False)
    to_whom = Column(String, nullable=True)
    executor = Column(String, nullable=True)
    content = Column(String, nullable=True)  # Краткое содержание
    kaiten_card_url = Column(String, nullable=True)  # Ссылка на карточку Kaiten
    file_blob = Column(LargeBinary, nullable=True)  # PDF письма
    sig_blob = Column(LargeBinary, nullable=True)  # Файл подписи .sig
    attachments_blob = Column(LargeBinary, nullable=True)  # Приложения (архив)
    folder_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OutboxJournal(outgoing_no={self.outgoing_no}, date={self.outgoing_date})>"
