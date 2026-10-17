from __future__ import annotations

import json
import re
import time
from typing import Any

from agent_test_hub.schemas import ExecutionTrace, TraceEvent, TraceEventType


def sanitize_sensitive_data(text: str) -> str:
    """脱敏：对常见密钥、身份证、手机号、密码执行掩码处理 (E11-05)"""
    if not text or not isinstance(text, str):
        return text

    # 1. 掩码 Bearer Token 与 API Key (保留前4后4)
    text = re.sub(
        r"(Bearer\s+)([a-zA-Z0-9_\-\.]{8,})",
        lambda m: f"{m.group(1)}{m.group(2)[:4]}...{m.group(2)[-4:]}",
        text,
    )
    text = re.sub(
        r"\b(sk-[a-zA-Z0-9]{8,})\b",
        lambda m: f"{m.group(1)[:7]}...{m.group(1)[-4:]}",
        text,
    )

    # 2. 掩码手机号
    text = re.sub(r"\b(1[3-9]\d)\d{4}(\d{4})\b", r"\1****\2", text)

    # 3. 掩码身份证
    text = re.sub(r"\b([1-9]\d{5})\d{8}(\d{3}[\dXx])\b", r"\1********\2", text)

    # 4. 掩码密码字段
    text = re.sub(r'("password"\s*:\s*)"[^"]+"', r'\1"******"', text)

    return text


class OTelGenAISpanExporter:
    """OpenTelemetry GenAI 与 OpenInference 语义标准 Trace 导出器 (E11-01 ~ E11-05)"""

    @classmethod
    def to_otlp_resource_spans(cls, trace: ExecutionTrace) -> dict[str, Any]:
        """将内部 ExecutionTrace 转换为标准 OTLP/HTTP JSON 格式"""
        trace_id_raw = trace.trace_id.replace("trc_", "").replace("-", "")
        # OTel 要求 32 字符 hex 作为 trace_id
        trace_id_hex = (trace_id_raw * 2)[:32].ljust(32, "0")

        spans_payload = []
        for event in trace.events:
            span_id_raw = event.span_id.replace("spn_", "").replace("-", "")
            span_id_hex = (span_id_raw * 2)[:16].ljust(16, "0")

            start_time_ns = int(event.timestamp.timestamp() * 1e9)
            duration_ms = 10.0
            if event.tool_observation and event.tool_observation.duration_ms:
                duration_ms = event.tool_observation.duration_ms
            end_time_ns = start_time_ns + int(duration_ms * 1e6)

            # 语义化属性映射 (OTel GenAI Semantic Conventions)
            attributes = [
                {"key": "agent_test_hub.task_id", "value": {"stringValue": trace.task_id}},
                {"key": "agent_test_hub.turn_index", "value": {"intValue": str(event.turn_index)}},
                {"key": "agent_test_hub.actor_role", "value": {"stringValue": event.actor_role.value}},
            ]

            span_name = f"gen_ai.{event.event_type.value}"

            if event.event_type == TraceEventType.AGENT_MESSAGE:
                span_name = "gen_ai.chat"
                attributes.append({
                    "key": "gen_ai.prompt",
                    "value": {"stringValue": sanitize_sensitive_data(event.content)},
                })
                if event.thought:
                    attributes.append({
                        "key": "gen_ai.thought",
                        "value": {"stringValue": sanitize_sensitive_data(event.thought)},
                    })

            elif event.event_type == TraceEventType.TOOL_CALL_REQUEST and event.tool_observation:
                span_name = f"gen_ai.tool_call.{event.tool_observation.tool_name}"
                attributes.extend([
                    {"key": "gen_ai.tool.name", "value": {"stringValue": event.tool_observation.tool_name}},
                    {
                        "key": "gen_ai.tool.arguments",
                        "value": {
                            "stringValue": sanitize_sensitive_data(
                                json.dumps(event.tool_observation.arguments, ensure_ascii=False)
                            )
                        },
                    },
                    {
                        "key": "gen_ai.tool.is_error",
                        "value": {"boolValue": event.tool_observation.is_error},
                    },
                ])

            spans_payload.append({
                "traceId": trace_id_hex,
                "spanId": span_id_hex,
                "name": span_name,
                "kind": 3,  # SPAN_KIND_CLIENT
                "startTimeUnixNano": str(start_time_ns),
                "endTimeUnixNano": str(end_time_ns),
                "attributes": attributes,
                "status": {"code": 1},  # STATUS_CODE_OK
            })

        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "agent-test-hub"}},
                            {"key": "service.version", "value": {"stringValue": "0.1.0"}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "agent_test_hub.runner", "version": "1.0.0"},
                            "spans": spans_payload,
                        }
                    ],
                }
            ]
        }

    @classmethod
    def export_to_file(cls, trace: ExecutionTrace, output_path: str) -> None:
        """保存 OTLP 标准格式 JSON 文件供 Jaeger/Tempo 导入"""
        data = cls.to_otlp_resource_spans(trace)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
