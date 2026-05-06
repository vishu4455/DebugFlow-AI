"""Add feedback_entries table and error_type/severity columns to debug_results

Revision ID: 002_feedback_and_graph
Revises: 001_initial
Create Date: 2025-04-29
"""
from alembic import op
import sqlalchemy as sa

revision = "002_feedback_and_graph"
down_revision = None   # set to your first migration ID if you have one
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexed columns to debug_results for quick filtering
    with op.batch_alter_table("debug_results") as batch_op:
        batch_op.add_column(sa.Column("error_type", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("severity",   sa.String(50),  nullable=True))
        batch_op.create_index("ix_debug_results_error_type", ["error_type"])

    # Create feedback_entries table
    op.create_table(
        "feedback_entries",
        sa.Column("id",                     sa.Integer,     primary_key=True),
        sa.Column("pipeline_id",            sa.String(255), nullable=False, index=True),
        sa.Column("session_id",             sa.String(255), nullable=True,  index=True),
        sa.Column("username",               sa.String(255), nullable=False),
        sa.Column("classification_correct", sa.Boolean,     nullable=True),
        sa.Column("fix_useful",             sa.Boolean,     nullable=True),
        sa.Column("actual_error_type",      sa.String(100), nullable=True),
        sa.Column("comment",                sa.Text,        nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("feedback_entries")
    with op.batch_alter_table("debug_results") as batch_op:
        batch_op.drop_index("ix_debug_results_error_type")
        batch_op.drop_column("error_type")
        batch_op.drop_column("severity")
