"""record bounded food-image upload metadata

Revision ID: 20260904_24
Revises: 20260903_23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260904_24"
down_revision = "20260903_23"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("food_images", sa.Column("size_bytes", sa.Integer(), nullable=True), schema="nutrition")
    op.add_column("food_images", sa.Column("object_generation", sa.BigInteger(), nullable=True), schema="nutrition")
    op.execute("UPDATE nutrition.food_images SET size_bytes = 0 WHERE size_bytes IS NULL")
    op.alter_column("food_images", "size_bytes", nullable=False, schema="nutrition")
    op.create_check_constraint("ck_food_images_size_bytes", "food_images", "size_bytes >= 0 AND size_bytes <= 20971520", schema="nutrition")


def downgrade() -> None:
    op.drop_constraint("ck_food_images_size_bytes", "food_images", schema="nutrition", type_="check")
    op.drop_column("food_images", "object_generation", schema="nutrition")
    op.drop_column("food_images", "size_bytes", schema="nutrition")
