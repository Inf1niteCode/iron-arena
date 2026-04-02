# Iron Arena — Auction SQLAlchemy Models
# Created by: engineering-backend-architect
# Purpose: ORM models for auction_lots and auction_bids tables

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.backend.models.database import Base

AUCTION_PLATFORM_FEE = 0.05  # 5% fee on final sale price


class AuctionLot(Base):
    __tablename__ = "auction_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("items.id"), nullable=False
    )
    start_price: Mapped[int] = mapped_column(Integer, nullable=False)
    current_price: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=True
    )
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    seller: Mapped["Player"] = relationship("Player", foreign_keys=[seller_id])
    winner: Mapped["Player | None"] = relationship("Player", foreign_keys=[winner_id])
    item: Mapped["Item"] = relationship("Item", back_populates="auction_lot")
    bids: Mapped[list["AuctionBid"]] = relationship(
        "AuctionBid", back_populates="lot", order_by="AuctionBid.created_at.desc()"
    )

    @property
    def seller_payout(self) -> int:
        """Amount seller receives after 5% platform fee."""
        return int(self.current_price * (1 - AUCTION_PLATFORM_FEE))


class AuctionBid(Base):
    __tablename__ = "auction_bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("auction_lots.id"), nullable=False, index=True
    )
    bidder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    lot: Mapped["AuctionLot"] = relationship("AuctionLot", back_populates="bids")
    bidder: Mapped["Player"] = relationship("Player")
