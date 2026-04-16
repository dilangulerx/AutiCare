"""initial schema with human_reviews table

Revision ID: 001
Revises: 
Create Date: 2026-04-16

Bu migration mevcut tabloları "stamp" eder ve human_reviews tablosunu ekler.
Eğer tablolar zaten varsa (create_all ile oluşturulduysa) hata vermeden geçer.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Tablonun zaten var olup olmadığını kontrol et."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Mevcut tablolar create_all ile oluşturulmuş olabilir.
    # Sadece yoksa oluştur.

    if not table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("role", sa.Enum("user", "admin", name="userrole"), default="user"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("phone", sa.String(20), nullable=True),
        )

    if not table_exists("children"):
        op.create_table(
            "children",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("parent_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("birth_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not table_exists("daily_logs"):
        op.create_table(
            "daily_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("eye_contact", sa.Integer(), nullable=True),
            sa.Column("communication_score", sa.Integer(), nullable=True),
            sa.Column("aggression_level", sa.Integer(), nullable=True),
            sa.Column("sleep_hours", sa.Float(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not table_exists("weekly_reports"):
        op.create_table(
            "weekly_reports",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=False),
            sa.Column("report_text", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not table_exists("reminders"):
        op.create_table(
            "reminders",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("reminder_type", sa.String(50), nullable=True),
            sa.Column("remind_at", sa.DateTime(), nullable=True),
            sa.Column("recur_type", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    # ── YENİ TABLO: human_reviews (HITL) ──
    if not table_exists("human_reviews"):
        op.create_table(
            "human_reviews",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("workflow_id", sa.String(100), nullable=False, index=True),
            sa.Column("child_id", sa.Integer(), sa.ForeignKey("children.id"), nullable=False),
            sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("task_type", sa.String(50), nullable=False),
            sa.Column("ai_output", sa.Text(), nullable=False),
            sa.Column("confidence_score", sa.Float(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("reviewer_notes", sa.Text(), nullable=True),
            sa.Column("modified_output", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("human_reviews")
    # Diğer tabloları downgrade'de silmiyoruz — mevcut veri kaybolur
