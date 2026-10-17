from __future__ import annotations

import datetime
import json
import os
import uuid
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import db

Role = Literal["user_simulator", "red_team_attacker", "business_judge", "safety_judge", "moderator"]


class TeamMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role
    model: str = Field(min_length=1, max_length=200)
    api_base: str = Field(min_length=1, max_length=500)
    api_key: str = Field(default="", max_length=4096)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_endpoint(self):
        parts = urlsplit(self.api_base)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError("API Base must be an HTTP(S) URL")
        if parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("API Base must not contain credentials, query or fragment")
        self.model = self.model.strip()
        if not self.model:
            raise ValueError("Model is required")
        return self


class TeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_id: str
    name: str = Field(min_length=1, max_length=100)
    members: list[TeamMember] = Field(min_length=4, max_length=5)
    max_turns: int = Field(default=4, ge=2, le=12)
    timeout_seconds: int = Field(default=30, ge=5, le=120)
    max_calls: int = Field(default=30, ge=5, le=100)

    @model_validator(mode="after")
    def validate_roles(self):
        roles = [member.role for member in self.members]
        if len(set(roles)) != len(roles):
            raise ValueError("Duplicate team roles")
        enabled = {member.role for member in self.members if member.enabled}
        required = {"user_simulator", "business_judge", "safety_judge", "moderator"}
        if not required.issubset(enabled):
            raise ValueError("User simulator, both judges and moderator are required")
        return self


def _cipher() -> Fernet:
    configured = os.environ.get("AGENT_TEST_HUB_ENCRYPTION_KEY")
    if configured:
        return Fernet(configured.encode())
    # Local deployments keep the master key separate from the database.
    path = Path(str(db.DB_PATH) + ".key")
    try:
        with path.open("xb") as file:
            os.chmod(path, 0o600)
            file.write(Fernet.generate_key())
    except FileExistsError:
        pass
    return Fernet(path.read_bytes())


def stored_config(req: TeamRequest, previous: dict | None = None) -> dict:
    config = req.model_dump(exclude={"workspace_id", "name"})
    previous_keys = {
        member["role"]: member.get("api_key", "")
        for member in (previous or {}).get("members", [])
    }
    for member in config["members"]:
        if member["api_key"]:
            member["api_key"] = _cipher().encrypt(member["api_key"].encode()).decode()
        else:
            member["api_key"] = previous_keys.get(member["role"], "")
    return config


def load_team(team_id: str, workspace_id: str, conn, decrypt: bool = False) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM evaluation_teams WHERE id = ? AND workspace_id = ?",
        (team_id, workspace_id),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="评测团队不存在")
    team = dict(row)
    config = json.loads(team.pop("config_json"))
    for member in config["members"]:
        if decrypt:
            if member.get("api_key"):
                member["api_key"] = _cipher().decrypt(member["api_key"].encode()).decode()
        else:
            member["api_key_configured"] = bool(member.pop("api_key", ""))
    return {**team, **config}


def team_router(request_user, require_workspace) -> APIRouter:
    router = APIRouter(prefix="/api/v1/evaluation-teams")

    @router.get("")
    def list_teams(workspace_id: str, authorization: str | None = Header(default=None)):
        require_workspace(request_user(authorization), workspace_id)
        with db.get_db_connection() as conn:
            ids = conn.execute(
                "SELECT id FROM evaluation_teams WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,),
            ).fetchall()
            result = [load_team(row["id"], workspace_id, conn) for row in ids]
        conn.close()
        return result

    @router.post("", status_code=201)
    def create_team(req: TeamRequest, authorization: str | None = Header(default=None)):
        require_workspace(request_user(authorization), req.workspace_id, write=True)
        team_id = f"team_{uuid.uuid4().hex[:12]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        config = stored_config(req)
        with db.get_db_connection() as conn:
            conn.execute(
                "INSERT INTO evaluation_teams VALUES (?, ?, ?, ?, ?, ?)",
                (team_id, req.workspace_id, req.name, json.dumps(config), now, now),
            )
            conn.commit()
        conn.close()
        return {"team_id": team_id}

    @router.put("/{team_id}")
    def update_team(team_id: str, req: TeamRequest, authorization: str | None = Header(default=None)):
        require_workspace(request_user(authorization), req.workspace_id, write=True)
        with db.get_db_connection() as conn:
            load_team(team_id, req.workspace_id, conn, decrypt=True)
            raw = conn.execute(
                "SELECT config_json FROM evaluation_teams WHERE id = ?", (team_id,)
            ).fetchone()
            config = stored_config(req, json.loads(raw["config_json"]))
            conn.execute(
                "UPDATE evaluation_teams SET name = ?, config_json = ?, updated_at = ? WHERE id = ?",
                (req.name, json.dumps(config), datetime.datetime.now(datetime.timezone.utc).isoformat(), team_id),
            )
            conn.commit()
        conn.close()
        return {"team_id": team_id}

    @router.delete("/{team_id}")
    def delete_team(team_id: str, workspace_id: str, authorization: str | None = Header(default=None)):
        require_workspace(request_user(authorization), workspace_id, write=True)
        with db.get_db_connection() as conn:
            load_team(team_id, workspace_id, conn)
            conn.execute("DELETE FROM evaluation_teams WHERE id = ?", (team_id,))
            conn.commit()
        conn.close()
        return {"team_id": team_id, "status": "deleted"}

    return router
