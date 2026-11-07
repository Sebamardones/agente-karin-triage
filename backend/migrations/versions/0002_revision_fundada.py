"""Fundamentos humanos y validación explícita de excepciones RD-10."""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("revision_humana", sa.Column("motivo_descarte", sa.String(100)))
    op.add_column("revision_humana", sa.Column("cita_respaldo", sa.Text()))
    op.add_column("revision_humana", sa.Column(
        "excepcion_rd10", sa.Boolean(), server_default=sa.false(), nullable=False))


def downgrade():
    with op.batch_alter_table("revision_humana", table_args=(
        sa.CheckConstraint("nivel IN (1, 2)", name="ck_revision_nivel"),)) as batch:
        batch.drop_column("excepcion_rd10")
        batch.drop_column("cita_respaldo")
        batch.drop_column("motivo_descarte")
