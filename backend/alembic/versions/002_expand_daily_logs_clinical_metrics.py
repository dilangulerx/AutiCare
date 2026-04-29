"""expand daily_logs with clinical metrics and ABC fields

Revision ID: 002
Revises: 001
Create Date: 2026-04-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = [c["name"] for c in inspector.get_columns(table_name)]
    return column_name in cols


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _column_exists(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    _add_column_if_missing("daily_logs", sa.Column("sleep_start_time", sa.String(length=5), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("sleep_end_time", sa.String(length=5), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("sleep_interruptions", sa.Integer(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("eye_contact_frequency", sa.Integer(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("eye_contact_duration_seconds", sa.Float(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("eye_contact_context", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("aggression_frequency", sa.Integer(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("aggression_duration_minutes", sa.Float(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("aggression_trigger", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("communication_mode", sa.String(length=20), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("communication_function", sa.String(length=50), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("communication_effectiveness", sa.Integer(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("antecedent", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("behavior", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("consequence", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("sensory_trigger", sa.Text(), nullable=True))
    _add_column_if_missing("daily_logs", sa.Column("gi_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    # Safe downgrade for new optional columns only.
    for column_name in [
        "gi_notes",
        "sensory_trigger",
        "consequence",
        "behavior",
        "antecedent",
        "communication_effectiveness",
        "communication_function",
        "communication_mode",
        "aggression_trigger",
        "aggression_duration_minutes",
        "aggression_frequency",
        "eye_contact_context",
        "eye_contact_duration_seconds",
        "eye_contact_frequency",
        "sleep_interruptions",
        "sleep_end_time",
        "sleep_start_time",
    ]:
        if _column_exists("daily_logs", column_name):
            op.drop_column("daily_logs", column_name)
