"""table recreate

Revision ID: daabdccb13d9
Revises: 36e31c961192
Create Date: 2025-06-25 19:38:41.484221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'daabdccb13d9'
down_revision: Union[str, None] = '36e31c961192'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Step 1: Create the new enum type
    new_enum = sa.Enum('MONTHLY', 'ANNUALLY', name='billingcycleenum_new')
    new_enum.create(op.get_bind(), checkfirst=True)

    # Step 2: Alter column to use new enum type
    op.execute("ALTER TABLE easybuy_plans ALTER COLUMN billing_cycle TYPE billingcycleenum_new USING billing_cycle::text::billingcycleenum_new")

    # Step 3: Drop old enum type
    op.execute("DROP TYPE billingcycleenum")

    # Step 4: Rename new enum to the original name
    op.execute("ALTER TYPE billingcycleenum_new RENAME TO billingcycleenum")


def downgrade():
    # Step 1: Create the old enum again
    old_enum = sa.Enum('TERMLY', 'MONTHLY', 'SESSIONAL', name='billingcycleenum_old')
    old_enum.create(op.get_bind(), checkfirst=True)

    # Step 2: Alter the column back to the old enum type
    op.execute(
        "ALTER TABLE easybuy_plans ALTER COLUMN billing_cycle TYPE billingcycleenum_old USING billing_cycle::text::billingcycleenum_old"
    )

    # Step 3: Drop the new enum
    op.execute("DROP TYPE billingcycleenum")

    # Step 4: Rename old enum back to the original name
    op.execute("ALTER TYPE billingcycleenum_old RENAME TO billingcycleenum")

