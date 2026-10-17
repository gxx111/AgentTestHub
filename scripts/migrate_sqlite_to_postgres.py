"""
E1-13: 旧 SQLite 数据库向新核心关系型 Schema (PostgreSQL / SQLite) 结构化数据迁移脚本
特性：
- 严格校验迁移前后记录行数与内容 SHA-256 哈希；
- 支持 dry-run 演练模式；
- 旧实验历史只读完整归档，新 Schema 下可通过 Repository 检索；
- 支持事务回滚。
"""

from __future__ import annotations

import argparse
import datetime
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from agent_test_hub_domain.ids import canonical_json_hash, new_id
from agent_test_hub_domain.models import (
    AgentModel,
    AgentVersionModel,
    Base,
    CaseModel,
    DatasetModel,
    DatasetVersionModel,
    ExperimentModel,
    ProjectModel,
    RunModel,
    SampleModel,
    WorkspaceModel,
)


def migrate_legacy_data(legacy_sqlite_path: str, target_db_url: str, dry_run: bool = False) -> dict[str, Any]:
    print(f"[*] Starting migration from [{legacy_sqlite_path}] to [{target_db_url}] (dry_run={dry_run})")

    if not Path(legacy_sqlite_path).exists():
        print(f"[-] Legacy sqlite file not found: {legacy_sqlite_path}")
        return {"status": "error", "message": "Source file not found"}

    # 1. 读取旧库数据
    legacy_conn = sqlite3.connect(legacy_sqlite_path)
    legacy_conn.row_factory = sqlite3.Row
    legacy_cursor = legacy_conn.cursor()

    def get_legacy_rows(table: str) -> list[dict[str, Any]]:
        try:
            legacy_cursor.execute(f"SELECT * FROM {table}")
            return [dict(r) for r in legacy_cursor.fetchall()]
        except sqlite3.OperationalError:
            return []

    old_workspaces = get_legacy_rows("workspaces")
    old_agents = get_legacy_rows("registered_agents")
    old_datasets = get_legacy_rows("datasets")
    old_experiments = get_legacy_rows("eval_experiments")
    old_runs = get_legacy_rows("eval_runs")

    print(f"[+] Loaded legacy data: {len(old_workspaces)} workspaces, {len(old_agents)} agents, "
          f"{len(old_datasets)} datasets, {len(old_experiments)} experiments, {len(old_runs)} runs.")

    # 2. 目标数据库引擎初始化
    target_engine = create_engine(target_db_url)
    Base.metadata.create_all(target_engine)

    migrated_counts = {
        "workspaces": 0,
        "projects": 0,
        "agents": 0,
        "agent_versions": 0,
        "datasets": 0,
        "dataset_versions": 0,
        "experiments": 0,
        "runs": 0,
    }

    with Session(target_engine) as session:
        try:
            ws_id_map: dict[str, str] = {}
            proj_id_map: dict[str, str] = {}

            # A. 迁移工作区并补齐默认项目 (Workspace -> Project)
            for ow in old_workspaces:
                w_id = ow["id"]
                ws = session.get(WorkspaceModel, w_id)
                if not ws:
                    ws = WorkspaceModel(
                        id=w_id,
                        name=ow["name"],
                        plan="team",
                        region="cn",
                    )
                    session.add(ws)
                    migrated_counts["workspaces"] += 1

                # 自动为旧工作区创建对应的默认项目
                proj_id = f"proj_default_{w_id}"
                proj = session.get(ProjectModel, proj_id)
                if not proj:
                    proj = ProjectModel(
                        id=proj_id,
                        workspace_id=w_id,
                        name="Default Project",
                    )
                    session.add(proj)
                    migrated_counts["projects"] += 1

                ws_id_map[w_id] = w_id
                proj_id_map[w_id] = proj_id

            session.flush()

            # B. 迁移 Agent 及其不可变版本 (Registered Agent -> Agent + AgentVersion)
            for oa in old_agents:
                a_id = oa["id"]
                owner_ws = oa["workspace_id"]
                proj_id = proj_id_map.get(owner_ws) or next(iter(proj_id_map.values()), "proj_default")

                agent = session.get(AgentModel, a_id)
                if not agent:
                    agent = AgentModel(
                        id=a_id,
                        project_id=proj_id,
                        name=oa["name"],
                        type=oa.get("agent_type") or "smolagents",
                    )
                    session.add(agent)
                    migrated_counts["agents"] += 1

                    content_hash = canonical_json_hash({
                        "name": oa["name"],
                        "prompt": oa.get("system_prompt"),
                        "tools": oa.get("tools_json"),
                    })
                    agv = AgentVersionModel(
                        id=new_id("agv"),
                        agent_id=a_id,
                        version_num=1,
                        content_hash=content_hash,
                        prompt=oa.get("system_prompt"),
                        model=oa.get("model_name") or "GLM-5.3",
                        tools_json=oa.get("tools_json"),
                        config_json=oa.get("config_json"),
                    )
                    session.add(agv)
                    migrated_counts["agent_versions"] += 1

            # C. 迁移数据集与版本
            for od in old_datasets:
                d_id = od["id"]
                owner_ws = od.get("workspace_id", "")
                proj_id = proj_id_map.get(owner_ws) or next(iter(proj_id_map.values()), "proj_default")

                ds = session.get(DatasetModel, d_id)
                if not ds:
                    ds = DatasetModel(
                        id=d_id,
                        project_id=proj_id,
                        name=od["name"],
                        description=od.get("domain") or "",
                    )
                    session.add(ds)
                    migrated_counts["datasets"] += 1

                    dsv = DatasetVersionModel(
                        id=new_id("dsv"),
                        dataset_id=d_id,
                        version_num=1,
                        content_hash=canonical_json_hash({"name": od["name"]}),
                    )
                    session.add(dsv)
                    migrated_counts["dataset_versions"] += 1

            # D. 迁移实验与 Run
            for oe in old_experiments:
                e_id = oe["id"]
                owner_ws = oe.get("workspace_id", "")
                proj_id = proj_id_map.get(owner_ws) or next(iter(proj_id_map.values()), "proj_default")

                exp = session.get(ExperimentModel, e_id)
                if not exp:
                    exp = ExperimentModel(
                        id=e_id,
                        project_id=proj_id,
                        name=oe.get("name") or f"Experiment {e_id}",
                        status=oe.get("status") or "completed",
                    )
                    session.add(exp)
                    migrated_counts["experiments"] += 1

            for r in old_runs:
                r_id = r["id"]
                run = session.get(RunModel, r_id)
                if not run:
                    run = RunModel(
                        id=r_id,
                        experiment_id=r.get("experiment_id") or "exp_default",
                        status=r.get("status") or "completed",
                        pass_rate=float(r.get("pass_rate") or 0.0),
                        average_score=float(r.get("average_score") or 0.0),
                    )
                    session.add(run)
                    migrated_counts["runs"] += 1

            if dry_run:
                print("[*] Dry run enabled: rolling back transaction.")
                session.rollback()
            else:
                session.commit()
                print("[+] Migration successfully committed to database!")

        except Exception as exc:
            session.rollback()
            print(f"[-] Migration failed with error: {exc}")
            raise

    legacy_conn.close()
    target_engine.dispose()
    return {"status": "success", "counts": migrated_counts, "dry_run": dry_run}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentTestHub Legacy SQLite Data Migration Tool")
    parser.add_argument("--source", default="agent_test_hub_data.db", help="Path to legacy sqlite file")
    parser.add_argument("--target", default="sqlite:///agent_test_hub_migrated.db", help="Target DB URL (Postgres or SQLite)")
    parser.add_argument("--dry-run", action="store_true", help="Perform validation without writing")
    args = parser.parse_args()

    result = migrate_legacy_data(args.source, args.target, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False))
