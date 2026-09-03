from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CategoryRecord(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    filament: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    color_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color_hex: Mapped[str] = mapped_column(String(16), nullable=False, default="#0077CC")
    color_bg: Mapped[str] = mapped_column(String(16), nullable=False, default="#E6F3FA")
    prefix: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    parts: Mapped[List["PartRecord"]] = relationship("PartRecord", back_populates="category", cascade="all, delete-orphan")


class PartRecord(Base):
    __tablename__ = "parts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category_id: Mapped[str] = mapped_column(String(64), ForeignKey("categories.id"), nullable=False)
    size: Mapped[str] = mapped_column(String(32), nullable=False)
    length: Mapped[str] = mapped_column(String(32), nullable=False)
    head: Mapped[str] = mapped_column(String(32), nullable=False)
    drive: Mapped[str] = mapped_column(String(32), nullable=False)
    comp_type: Mapped[str] = mapped_column(String(32), nullable=False, default="bolt")
    material: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tool_key: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    tap_drill: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    clearance_drill: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    pitch: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    extra_note: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    category: Mapped["CategoryRecord"] = relationship("CategoryRecord", back_populates="parts")
    compartments: Mapped[List["BinCompartmentRecord"]] = relationship("BinCompartmentRecord", back_populates="part")


class StorageLocationRecord(Base):
    __tablename__ = "storage_locations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location_type: Mapped[str] = mapped_column(String(64), nullable=False, default="DRAWER")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    carriers: Mapped[List["CarrierRecord"]] = relationship("CarrierRecord", back_populates="location", cascade="all, delete-orphan")


class CarrierRecord(Base):
    __tablename__ = "carriers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_id: Mapped[str] = mapped_column(String(64), ForeignKey("storage_locations.id"), nullable=False)
    layout: Mapped[str] = mapped_column(String(32), nullable=False, default="3x4")
    height_u: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    position_row: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    position_col: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    location: Mapped["StorageLocationRecord"] = relationship("StorageLocationRecord", back_populates="carriers")
    bins: Mapped[List["BinRecord"]] = relationship("BinRecord", back_populates="carrier")


class BinRecord(Base):
    """Represents a physical small-parts cassette in the workshop with 1, 2, or 3 internal compartments."""
    __tablename__ = "bins"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. BIN-001
    carrier_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("carriers.id"), nullable=True)
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    compartment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1, 2, or 3
    cassette_type: Mapped[str] = mapped_column(String(64), nullable=False, default="single")  # single, divided_2, divided_3
    label_title: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    qr_code_payload: Mapped[str] = mapped_column(String(256), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    carrier: Mapped[Optional["CarrierRecord"]] = relationship("CarrierRecord", back_populates="bins")
    compartments: Mapped[List["BinCompartmentRecord"]] = relationship("BinCompartmentRecord", back_populates="bin", cascade="all, delete-orphan", order_by="BinCompartmentRecord.compartment_index")


class BinCompartmentRecord(Base):
    """Represents a single compartment (slot 1, 2, or 3) inside a physical bin cassette."""
    __tablename__ = "bin_compartments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # e.g. BIN-001-C1
    bin_id: Mapped[str] = mapped_column(String(64), ForeignKey("bins.id"), nullable=False)
    compartment_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1, 2, or 3
    part_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("parts.id"), nullable=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    notes: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    bin: Mapped["BinRecord"] = relationship("BinRecord", back_populates="compartments")
    part: Mapped[Optional["PartRecord"]] = relationship("PartRecord", back_populates="compartments")
