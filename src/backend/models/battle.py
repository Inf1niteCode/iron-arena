# Iron Arena — Battle SQLAlchemy Model
# Created by: engineering-backend-architect
# Purpose: ORM model for battles table (PvP match records and rewards)

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.models.database import Base


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player1_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    player2_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    winner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=True
    )
    # Battle mode: 'random' (matchmaking) or 'duel' (direct challenge)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="random")
    # Rewards for the winner
    xp_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gold_gained: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    player1: Mapped["Player"] = relationship(
        "Player", foreign_keys=[player1_id], back_populates="battles_as_p1"
    )
    player2: Mapped["Player"] = relationship(
        "Player", foreign_keys=[player2_id], back_populates="battles_as_p2"
    )
    winner: Mapped["Player | None"] = relationship("Player", foreign_keys=[winner_id])
