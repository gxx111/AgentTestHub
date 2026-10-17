"""initial core domain tables

Revision ID: 3db3b725c44a
Revises: 
Create Date: 2026-10-18 02:51:55.302072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3db3b725c44a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - creates complete domain schema from empty DB."""
    # 1. workspaces
    op.create_table(
        'workspaces',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('plan', sa.String(length=32), nullable=False, server_default='team'),
        sa.Column('region', sa.String(length=32), nullable=False, server_default='cn'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 2. projects
    op.create_table(
        'projects',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.String(length=64), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_projects_workspace_id', 'projects', ['workspace_id'], unique=False)

    # 3. agents
    op.create_table(
        'agents',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False, server_default='smolagents'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_agents_project_id', 'agents', ['project_id'], unique=False)

    # 4. agent_versions
    op.create_table(
        'agent_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('agent_id', sa.String(length=64), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_num', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('model', sa.String(length=128), nullable=False, server_default='GLM-5.3'),
        sa.Column('tools_json', sa.Text(), nullable=True),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_agent_version_unique', 'agent_versions', ['agent_id', 'version_num'], unique=True)
    op.create_index('ix_agent_versions_agent_id', 'agent_versions', ['agent_id'], unique=False)

    # 5. datasets
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_datasets_project_id', 'datasets', ['project_id'], unique=False)

    # 6. dataset_versions
    op.create_table(
        'dataset_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('dataset_id', sa.String(length=64), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_num', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_dataset_version_unique', 'dataset_versions', ['dataset_id', 'version_num'], unique=True)
    op.create_index('ix_dataset_versions_dataset_id', 'dataset_versions', ['dataset_id'], unique=False)

    # 7. cases
    op.create_table(
        'cases',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('dataset_version_id', sa.String(length=64), sa.ForeignKey('dataset_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('environment_spec_json', sa.Text(), nullable=True),
        sa.Column('expected_state_json', sa.Text(), nullable=True),
        sa.Column('rubric_set_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_cases_dataset_version_id', 'cases', ['dataset_version_id'], unique=False)

    # 8. experiments
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_experiments_project_id', 'experiments', ['project_id'], unique=False)

    # 9. runs
    op.create_table(
        'runs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('experiment_id', sa.String(length=64), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_version_id', sa.String(length=64), sa.ForeignKey('agent_versions.id'), nullable=True),
        sa.Column('dataset_version_id', sa.String(length=64), sa.ForeignKey('dataset_versions.id'), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('pass_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_runs_experiment_id', 'runs', ['experiment_id'], unique=False)

    # 10. samples
    op.create_table(
        'samples',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('run_id', sa.String(length=64), sa.ForeignKey('runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_id', sa.String(length=64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sample_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sample_key', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('is_passed', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('error_code', sa.String(length=64), nullable=True),
        sa.Column('trace_json', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_sample_idempotent', 'samples', ['sample_key'], unique=True)
    op.create_index('ix_samples_run_id', 'samples', ['run_id'], unique=False)
    op.create_index('ix_samples_case_id', 'samples', ['case_id'], unique=False)

    # 11. verdicts
    op.create_table(
        'verdicts',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('sample_id', sa.String(length=64), sa.ForeignKey('samples.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rubric_id', sa.String(length=64), nullable=False),
        sa.Column('judge_role', sa.String(length=64), nullable=False),
        sa.Column('verdict', sa.String(length=16), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('evidence_span_ids', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_verdicts_sample_id', 'verdicts', ['sample_id'], unique=False)

    # 12. gate_policies
    op.create_table(
        'gate_policies',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('project_id', sa.String(length=64), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('policy_json', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_gate_policies_project_id', 'gate_policies', ['project_id'], unique=False)

    # 13. release_decisions
    op.create_table(
        'release_decisions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('gate_policy_id', sa.String(length=64), sa.ForeignKey('gate_policies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('experiment_id', sa.String(length=64), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('decision', sa.String(length=32), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_release_decisions_experiment_id', 'release_decisions', ['experiment_id'], unique=False)
    op.create_index('ix_release_decisions_gate_policy_id', 'release_decisions', ['gate_policy_id'], unique=False)

    # 14. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('workspace_id', sa.String(length=64), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=False),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_logs_workspace_id', 'audit_logs', ['workspace_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema in reverse dependency order."""
    op.drop_table('audit_logs')
    op.drop_table('release_decisions')
    op.drop_table('gate_policies')
    op.drop_table('verdicts')
    op.drop_table('samples')
    op.drop_table('runs')
    op.drop_table('experiments')
    op.drop_table('cases')
    op.drop_table('dataset_versions')
    op.drop_table('datasets')
    op.drop_table('agent_versions')
    op.drop_table('agents')
    op.drop_table('projects')
    op.drop_table('workspaces')
