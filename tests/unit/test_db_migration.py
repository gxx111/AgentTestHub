from __future__ import annotations

import os
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_and_downgrade_on_empty_db(tmp_path: Path):
    """验证 E1-03: alembic upgrade head 可在空库创建全部表，且可干净回滚"""
    db_file = tmp_path / "test_empty_migration.db"
    db_url = f"sqlite:///{db_file.as_posix()}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. 验证正向迁移创建所有表
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "workspaces",
        "projects",
        "agents",
        "agent_versions",
        "datasets",
        "dataset_versions",
        "cases",
        "experiments",
        "runs",
        "samples",
        "verdicts",
        "gate_policies",
        "release_decisions",
        "audit_logs",
    }

    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"

    # 2. 验证逆向回滚 downgrade base
    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    remaining_tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
    assert len(remaining_tables) == 0, f"Tables remained after downgrade: {remaining_tables}"

    # 3. 再次正向迁移验证可重复升级
    command.upgrade(alembic_cfg, "head")
    inspector = inspect(engine)
    assert expected_tables.issubset(set(inspector.get_table_names()))
    engine.dispose()
