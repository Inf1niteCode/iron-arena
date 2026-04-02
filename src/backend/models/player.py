# Iron Arena — Player SQLAlchemy Model
# Created by: engineering-backend-architect
# Purpose: ORM model for players table (character stats, resources, tracking)

from datetime import datetime, timezone
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.models.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)

    # Progression
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Base stats (stat points allocated by player)
    health_points: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    stamina: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    agility: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Current resource values (regenerate over time)
    current_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    current_stamina: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Battle stats
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_fight_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    items: Mapped[list["Item"]] = relationship("Item", back_populates="player", lazy="select")
    battles_as_p1: Mapped[list["Battle"]] = relationship(
        "Battle", foreign_keys="Battle.player1_id", back_populates="player1"
    )
    battles_as_p2: Mapped[list["Battle"]] = relationship(
        "Battle", foreign_keys="Battle.player2_id", back_populates="player2"
    )

    @property
    def max_hp(self) -> int:
        """Max HP = healthPoints * 10 (exact formula from spec)."""
        return self.health_points * 10

    @property
    def max_stamina(self) -> int:
        """Max stamina = stamina stat * 10."""
        return self.stamina * 10

    @property
    def xp_to_next_level(self) -> int:
        """XP needed for next level = level * 100 (exact formula from spec)."""
        return self.level * 100

    @property
    def dodge_chance(self) -> float:
        """Dodge chance = agility * 1.5, max 40% (exact formula from spec)."""
        return min(self.agility * 1.5, 40.0)
