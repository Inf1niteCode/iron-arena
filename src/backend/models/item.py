# Iron Arena — Item SQLAlchemy Model
# Created by: engineering-backend-architect
# Purpose: ORM model for items table (equipment, crystals, inventory)

from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.models.database import Base

VALID_TYPES = {"helmet", "chest", "bracers", "boots", "crystal"}
VALID_SLOTS = {"head", "chest", "waist", "legs", "crystal"}
VALID_COLORS = {"red", "blue", "green"}
VALID_BONUS_STATS = {"strength", "agility", "health_points", "stamina"}

# Armor slot mapping: item type -> attack zone it defends
ARMOR_ZONE_MAP = {
    "helmet": "head",
    "chest": "chest",
    "bracers": "waist",
    "boots": "legs",
}


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    slot: Mapped[str] = mapped_column(String(20), nullable=False)
    color: Mapped[str] = mapped_column(String(10), nullable=False)
    bonus_stat: Mapped[str] = mapped_column(String(20), nullable=False)
    bonus_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    armor_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_equipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_broken: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enchant_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="items")
    auction_lot: Mapped["AuctionLot | None"] = relationship(
        "AuctionLot", back_populates="item", uselist=False
    )

    @property
    def defends_zone(self) -> str | None:
        """Which attack zone this armor piece defends."""
        return ARMOR_ZONE_MAP.get(self.type)
