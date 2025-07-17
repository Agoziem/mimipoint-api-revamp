"""table recreate

Revision ID: 37b44b27fd99
Revises: 7b7e47a86d2c
Create Date: 2025-06-25 19:24:24.299702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37b44b27fd99'
down_revision: Union[str, None] = '7b7e47a86d2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the enums first
    billing_cycle_enum = sa.Enum('TERMLY', 'MONTHLY', 'SESSIONAL', name='billingcycleenum')
    billing_category_enum = sa.Enum('STANDARD', 'PREMIUM', name='billingcategoryenum')

    billing_cycle_enum.create(op.get_bind(), checkfirst=True)
    billing_category_enum.create(op.get_bind(), checkfirst=True)

    # Then add the columns using those enums
    op.add_column('easybuy_plans', sa.Column('billing_cycle', billing_cycle_enum, nullable=False))
    op.add_column('easybuy_plans', sa.Column('billing_category', billing_category_enum, nullable=False))

    # Remove the old column
    op.drop_column('easybuy_plans', 'duration')



def downgrade() -> None:
    op.add_column('easybuy_plans', sa.Column('duration', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_column('easybuy_plans', 'billing_category')
    op.drop_column('easybuy_plans', 'billing_cycle')

    # Drop enums after dropping the columns that used them
    billing_cycle_enum = sa.Enum('TERMLY', 'MONTHLY', 'SESSIONAL', name='billingcycleenum')
    billing_category_enum = sa.Enum('STANDARD', 'PREMIUM', name='billingcategoryenum')

    billing_category_enum.drop(op.get_bind(), checkfirst=True)
    billing_cycle_enum.drop(op.get_bind(), checkfirst=True)

