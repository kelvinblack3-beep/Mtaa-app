"""Initial schema: users, sessions, ledger, payments, tokens, social, audit

Revision ID: 001
Revises:
Create Date: 2026-10-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True)

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("balance_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("balance_cents >= 0", name="ck_account_balance_non_negative"),
    )
    op.create_index("ix_accounts_code", "accounts", ["code"], unique=True)
    op.create_index("ix_accounts_account_type", "accounts", ["account_type"])
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"])

    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference", sa.String(64), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("entry_type", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reversed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id"), nullable=True),
    )
    op.create_index("ix_journal_entries_reference", "journal_entries", ["reference"], unique=True)
    op.create_index("ix_journal_entries_entry_type", "journal_entries", ["entry_type"])
    op.create_index("ix_journal_entries_idempotency_key", "journal_entries", ["idempotency_key"], unique=True)
    op.create_index("ix_journal_entries_related_user_id", "journal_entries", ["related_user_id"])

    op.create_table(
        "journal_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("side", sa.String(6), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("memo", sa.String(255), nullable=True),
        sa.CheckConstraint("amount_cents > 0", name="ck_journal_line_positive_amount"),
        sa.CheckConstraint("side IN ('debit', 'credit')", name="ck_journal_line_side"),
    )
    op.create_index("ix_journal_lines_entry_id", "journal_lines", ["entry_id"])
    op.create_index("ix_journal_lines_account_id", "journal_lines", ["account_id"])

    op.create_table(
        "payment_intents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="KES"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_reference", sa.String(64), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("journal_entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id"), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_payment_intents_user_id", "payment_intents", ["user_id"])
    op.create_index("ix_payment_intents_status", "payment_intents", ["status"])
    op.create_index("ix_payment_intents_external_reference", "payment_intents", ["external_reference"], unique=True)
    op.create_index("ix_payment_intents_idempotency_key", "payment_intents", ["idempotency_key"], unique=True)

    op.create_table(
        "payment_callbacks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("payment_intents.id"), nullable=True),
        sa.Column("external_reference", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("processing_result", sa.String(50), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payment_callbacks_payment_intent_id", "payment_callbacks", ["payment_intent_id"])
    op.create_index("ix_payment_callbacks_external_reference", "payment_callbacks", ["external_reference"])

    op.create_table(
        "tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mint_address", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("decimals", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("total_supply", sa.BigInteger(), nullable=False),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("virtual_sol_reserves", sa.BigInteger(), nullable=False),
        sa.Column("virtual_token_reserves", sa.BigInteger(), nullable=False),
        sa.Column("real_token_reserves", sa.BigInteger(), nullable=False),
        sa.Column("real_sol_reserves", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_verified_onchain", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("network", sa.String(16), nullable=False, server_default="devnet"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
    )
    op.create_index("ix_tokens_mint_address", "tokens", ["mint_address"], unique=True)
    op.create_index("ix_tokens_symbol", "tokens", ["symbol"])
    op.create_index("ix_tokens_creator_id", "tokens", ["creator_id"])

    op.create_table(
        "token_holdings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("avg_cost_lamports", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_token_holdings_user_id", "token_holdings", ["user_id"])
    op.create_index("ix_token_holdings_token_id", "token_holdings", ["token_id"])

    op.create_table(
        "trade_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tokens.id"), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("token_amount", sa.BigInteger(), nullable=False),
        sa.Column("sol_amount_lamports", sa.BigInteger(), nullable=False),
        sa.Column("price_per_token", sa.Float(), nullable=False),
        sa.Column("slippage_bps", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(20), nullable=False, server_default="filled"),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trade_orders_user_id", "trade_orders", ["user_id"])
    op.create_index("ix_trade_orders_token_id", "trade_orders", ["token_id"])

    op.create_table(
        "communities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("banner_url", sa.String(500), nullable=True),
        sa.Column("creator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_communities_slug", "communities", ["slug"], unique=True)

    op.create_table(
        "community_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("community_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("community_id", "user_id", name="uq_community_member"),
    )

    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("community_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_removed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_posts_author_id", "posts", ["author_id"])

    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_removed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])

    op.create_table(
        "likes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "post_id", name="uq_like"),
    )

    op.create_table(
        "follows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("follower_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("following_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("follower_id", "following_id", name="uq_follow"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reporter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("follows")
    op.drop_table("likes")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("community_members")
    op.drop_table("communities")
    op.drop_table("trade_orders")
    op.drop_table("token_holdings")
    op.drop_table("tokens")
    op.drop_table("payment_callbacks")
    op.drop_table("payment_intents")
    op.drop_table("journal_lines")
    op.drop_table("journal_entries")
    op.drop_table("accounts")
    op.drop_table("sessions")
    op.drop_table("users")
