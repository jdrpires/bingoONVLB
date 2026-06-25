from datetime import datetime, timezone
from uuid import uuid4

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    bingos = db.relationship(
        "Bingo",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Bingo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    public_id = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid4()),
    )
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    owner = db.relationship("User", back_populates="bingos")
    rounds = db.relationship(
        "BingoRound",
        back_populates="bingo",
        cascade="all, delete-orphan",
        order_by="BingoRound.number.desc()",
        lazy="selectin",
    )

    @property
    def active_round(self):
        return next((round_ for round_ in self.rounds if round_.status != "finished"), None)


class BingoRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    bingo_id = db.Column(db.Integer, db.ForeignKey("bingo.id"), nullable=False, index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at = db.Column(db.DateTime(timezone=True))

    bingo = db.relationship("Bingo", back_populates="rounds")
    draws = db.relationship(
        "Draw",
        back_populates="round",
        cascade="all, delete-orphan",
        order_by="Draw.position",
        lazy="selectin",
    )
    events = db.relationship(
        "RoundEvent",
        back_populates="round",
        cascade="all, delete-orphan",
        order_by="RoundEvent.created_at",
        lazy="selectin",
    )

    __table_args__ = (
        db.UniqueConstraint("bingo_id", "number", name="uq_round_number_per_bingo"),
    )

    @property
    def drawn_numbers(self):
        return [draw.number for draw in self.draws]

    @property
    def last_number(self):
        return self.draws[-1].number if self.draws else None


class Draw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey("bingo_round.id"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    round = db.relationship("BingoRound", back_populates="draws")

    @property
    def letter(self):
        return bingo_letter(self.number)

    __table_args__ = (
        db.UniqueConstraint("round_id", "number", name="uq_draw_number_per_round"),
        db.UniqueConstraint("round_id", "position", name="uq_draw_position_per_round"),
    )


class RoundEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    round_id = db.Column(
        db.Integer,
        db.ForeignKey("bingo_round.id"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    round = db.relationship("BingoRound", back_populates="events")


def bingo_letter(number):
    if number <= 15:
        return "B"
    if number <= 30:
        return "I"
    if number <= 45:
        return "N"
    if number <= 60:
        return "G"
    return "O"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
