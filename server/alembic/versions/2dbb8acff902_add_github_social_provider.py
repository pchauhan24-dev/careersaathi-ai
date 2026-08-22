"""Add GitHub social provider.

Revision ID: 2dbb8acff902
Revises: 5f4fd32ed826
Create Date: 2026-08-21 09:57:19.278359
"""

from typing import Sequence, Union

from alembic import op

# Revision identifiers used by Alembic.
revision: str = "2dbb8acff902"
down_revision: Union[str, Sequence[str], None] = "5f4fd32ed826"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow GitHub as a social authentication provider."""
    op.drop_constraint(
        "ck_social_accounts_provider",
        "social_accounts",
        type_="check",
    )

    op.create_check_constraint(
        "ck_social_accounts_provider",
        "social_accounts",
        "provider IN ('google', 'github', 'linkedin')",
    )


def downgrade() -> None:
    """Remove GitHub from the supported social providers."""
    op.drop_constraint(
        "ck_social_accounts_provider",
        "social_accounts",
        type_="check",
    )

    op.create_check_constraint(
        "ck_social_accounts_provider",
        "social_accounts",
        "provider IN ('google', 'linkedin')",
    )
