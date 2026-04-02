# Iron Arena — ShopItem SQLAlchemy Model
# Created by: engineering-backend-architect
# Purpose: ORM model for shop_items table (rotating shop catalog with stock tracking)

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.models.database import Base


class ShopItem(Base):
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)        # helmet|chest|bracers|boots|crystal
    color: Mapped[str] = mapped_column(String(10), nullable=False)       # red|blue|green
    bonus_stat: Mapped[str] = mapped_column(String(20), nullable=False)  # strength|agility|health_points|stamina
    bonus_value: Mapped[int] = mapped_column(Integer, nullable=False)
    armor_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    # When this shop rotation expires and new items appear
    refreshes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
