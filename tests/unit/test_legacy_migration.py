from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from agent_test_hub_domain.models import AgentModel, WorkspaceModel
from scripts.migrate_sqlite_to_postgres import migrate_legacy_data


def test_legacy_sqlite_migration(tmp_path: Path):
    """验证 E1-13: 旧 SQLite 数据平滑迁移到新关系型架构"""
    legacy_file = tmp_path / "legacy.db"
    target_file = tmp_path / "target.db"
    target_url = f"sqlite:///{target_file.as_posix()}"

    # 创建旧库并写入旧版数据
    conn = sqlite3.connect(legacy_file)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE workspaces (id TEXT PRIMARY KEY, name TEXT);
    """)
    c.execute("""
    CREATE TABLE registered_agents (id TEXT PRIMARY KEY, workspace_id TEXT, name TEXT, agent_type TEXT, model_name TEXT);
    """)
    c.execute("INSERT INTO workspaces VALUES ('ws_old_1', 'Legacy Workspace');")
    c.execute("INSERT INTO registered_agents VALUES ('agent_old_1', 'ws_old_1', 'Legacy Agent', 'smolagents', 'GLM-5.3');")
    conn.commit()
    conn.close()

    # 1. 验证 dry-run 模式
    res_dry = migrate_legacy_data(legacy_file.as_posix(), target_url, dry_run=True)
    assert res_dry["status"] == "success"
    assert res_dry["counts"]["workspaces"] == 1
    assert res_dry["counts"]["agents"] == 1

    engine = create_engine(target_url)
    with Session(engine) as session:
        # dry_run 下应当被 rollback，没有实际记录
        assert session.get(WorkspaceModel, "ws_old_1") is None

    # 2. 真实执行迁移
    res_real = migrate_legacy_data(legacy_file.as_posix(), target_url, dry_run=False)
    assert res_real["status"] == "success"

    with Session(engine) as session:
        ws = session.get(WorkspaceModel, "ws_old_1")
        assert ws is not None
        assert ws.name == "Legacy Workspace"

        agent = session.get(AgentModel, "agent_old_1")
        assert agent is not None
        assert agent.name == "Legacy Agent"
        assert len(agent.versions) == 1

    engine.dispose()
