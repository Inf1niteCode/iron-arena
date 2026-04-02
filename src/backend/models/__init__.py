# Iron Arena — Models Package
# Created by: engineering-backend-architect
# Purpose: Export all ORM models so they register with SQLAlchemy metadata

from src.backend.models.database import Base
from src.backend.models.player import Player
from src.backend.models.item import Item
from src.backend.models.auction import AuctionLot, AuctionBid
from src.backend.models.battle import Battle
from src.backend.models.shop import ShopItem

__all__ = ["Base", "Player", "Item", "AuctionLot", "AuctionBid", "Battle", "ShopItem"]
