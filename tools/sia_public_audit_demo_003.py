#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sia_public_audit_demo_003.py

目的:
  「ログが無いせいで責任が確定できない」を、公開情報だけでも“数値”で示す。

基本思想:
  - 原因断定ツールではない（推測はしない）。
  - 公開情報から「答えられる問い / 答えられない問い」を定量化する。
  - とくに「責任（blame/attribution）の確定」に効くログを “Critical” として別スコア化する。

入力:
  - 001/002テンプレ形式の public minimal log JSON

出力:
  - <case_id>_sia_minimal.json（入力の再保存＝整形）
  - <case_id>_sia_audit_report.md（定量スコア＋欠損一覧）

主なスコア:
  1) Auditability Score (A-score): 全ユニットの平均（OK=1 / Partial=0.5 / Missing=0）
  2) Accountability-Critical Score (C-score): 責任確定に直結する重要ユニットの平均
     - planning.choice_timeline
     - control.command_timeline
     - software.version_manifest
     - integrity.tamper_evidence
  3) Responsibility Determinability (core): 供給網を除いた“現場責任”の切り分け可能性
  4) Supply-chain Determinability: OEM/運用/更新の責任切り分け可能性（version + integrity）
  5) Unanswerable Questions: 主要7問いのうち「答えられない」数

使い方:
  python sia_public_audit_demo_003.py --input your_case.json --out_dir out_demo
  python sia_public_audit_demo_003.py --sample uber_atg_ntsb_2018 --out_dir out_demo

注意:
  - この003は「説明不能性」を“数で見せる”ことに特化している。
  - 解析精度より、監査論点の固定化（欠損の明示）を優先する。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCHEMA_VERSION = "sia_audit_minimal_v0_public"

STATUS_SCORE = {"missing": 0.0, "partial": 0.5, "ok": 1.0}
STATUS_ICON = {"missing": "❌", "partial": "⚠️", "ok": "✅"}

# =========================
# データ構造
# =========================

@dataclass(frozen=True)
class SourceRef:
    ref: str
    note: str = ""
    confidence: str = "high"  # high/medium/low

@dataclass
class Event:
    t_rel_s: Optional[float]
    type: str
    actor: str
    data: Dict[str, Any]
    source: Optional[SourceRef] = None


def _utc_tz() -> _dt.tzinfo:
    if hasattr(_dt, "UTC"):
        return _dt.UTC  # type: ignore[attr-defined]
    return _dt.timezone.utc

def _iso_now() -> str:
    now = _dt.datetime.now(_utc_tz()).replace(microsecond=0)
    return now.isoformat().replace("+00:00", "Z")

def _float_or_none(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


# =========================
# 監査ユニット
# =========================

EVIDENCE_UNITS: Dict[str, Dict[str, str]] = {
    "time.base": {"title": "時間基準", "why": "イベント順序と遅延を議論するために必須（タイムラインの一貫性）。"},
    "authority.mode_timeline": {"title": "モード/責任境界タイムライン", "why": "事故時に「誰が最終権限を持っていたか」を確定するために必須。"},
    "perception.object_timeline": {"title": "認識: 物体検出/分類タイムライン", "why": "『見えていたのに止まらない』と『そもそも見えていない』を切り分ける。"},
    "prediction.risk_timeline": {"title": "予測: 未来軌道/TTC/リスクの推移", "why": "『認識はしたが危険と判断しなかった』かを検証する。"},
    "planning.choice_timeline": {"title": "計画: 候補プランと選択理由", "why": "安全制約が破れたのか、候補が存在しなかったのかを切り分ける。"},
    "control.command_timeline": {"title": "制御: コマンドと実応答", "why": "『止めようとして止まれなかった』か『止める要求が出ていない』かを切り分ける。"},
    "human.input_attention": {"title": "人間: 入力/注意(視線)・介入", "why": "接管・監視義務違反・インタフェース不連続などの議論に必要。"},
    "software.version_manifest": {"title": "版数/更新履歴", "why": "再現性と責任範囲（供給者/運用者/更新）を確定する。"},
    "integrity.tamper_evidence": {"title": "改竄耐性", "why": "“都合の良い切り出し”で議論が崩壊するのを防ぐ。"},
}

CRITICAL_UNITS = [
    "planning.choice_timeline",
    "control.command_timeline",
    "software.version_manifest",
    "integrity.tamper_evidence",
]

CORE_WEIGHTS = {
    # 現場責任（誰が何をしたか）に直結する重み
    "time.base": 0.15,
    "authority.mode_timeline": 0.25,
    "perception.object_timeline": 0.15,
    "prediction.risk_timeline": 0.10,
    "planning.choice_timeline": 0.15,
    "control.command_timeline": 0.15,
    "human.input_attention": 0.05,
    # 供給網は除外（別スコアで見る）
}

SUPPLY_WEIGHTS = {
    "software.version_manifest": 0.70,
    "integrity.tamper_evidence": 0.30,
}


# =========================
# サンプル（Uber）
# =========================

def sample_uber_atg_ntsb_2018() -> Dict[str, Any]:
    case_id = "uber_atg_tempe_2018_ntsb_public"
    src = SourceRef(
        ref="NTSB HWY18MH010 summary (public)",
        note="Summary: ADS detected pedestrian 5.6s before impact; never classified as pedestrian; never predicted path; emergency braking precluded; operator gaze; steering at -0.02s; speed 39 mph at impact.",
        confidence="high",
    )
    events: List[Event] = [
        Event(None, "time.base", "system", {"time_reference": "t_rel_s (impact=0)", "impact_definition": "first contact with pedestrian", "t_abs_iso_if_known": None, "notes": "Public summary only."}, src),
        Event(None, "authority.mode", "ads", {"mode": "autonomous_active", "notes": "ADS controlled at crash time."}, src),
        Event(None, "vehicle.state", "ads", {"speed_mph_near_collision_site": 45.0, "lane": "right lane", "notes": "Approached at 45 mph (exact t not disclosed)."}, src),
        Event(-5.6, "perception.detect", "ads", {"object": {"type": "pedestrian_with_bicycle", "id": "obj1"}, "detected": True, "distance_m": None, "notes": "Detected 5.6 s before impact."}, src),
        Event(None, "perception.classification", "ads", {"object_id": "obj1", "classified_as": "unstable", "confidence": None, "notes": "Never accurately classified as pedestrian."}, src),
        Event(None, "prediction.path", "ads", {"object_id": "obj1", "predicted_path_available": False, "ttc_s": None, "notes": "Never predicted her path."}, src),
        Event(None, "risk.collision_imminent", "ads", {"imminent_determined": True, "ttc_s": None, "notes": "Timing not disclosed."}, src),
        Event(None, "control.aeb_policy", "ads", {"aeb_armed": None, "aeb_triggered": None, "emergency_braking_precluded_by_design": True, "notes": "Design precluded emergency braking."}, src),
        Event(-1.0, "human.attention", "operator", {"gaze_to_road": True, "hands_on_wheel": None, "notes": "Gaze to road about 1 s before impact."}, src),
        Event(-0.02, "human.control_input", "operator", {"steering": "left", "brake": None, "throttle": None, "notes": "Steering left 0.02 s before impact."}, src),
        Event(0.0, "impact", "vehicle", {"impact_with": "pedestrian", "speed_mph": 39.0, "speed_kmh": None, "notes": "Impact speed 39 mph."}, src),
    ]
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": _iso_now(),
        "case": {
            "case_id": case_id,
            "title": "Uber ATG Tempe 2018 (public summary based minimal log)",
            "jurisdiction": "USA (Arizona)",
            "odds": {"system_level": "developmental ADS test (operator present)", "public_mode": "autonomous mode"},
            "public_sources": [{"ref": src.ref, "note": src.note, "confidence": src.confidence}],
        },
        "events": [event_to_dict(e) for e in events],
    }


def event_to_dict(e: Event) -> Dict[str, Any]:
    d: Dict[str, Any] = {"t_rel_s": e.t_rel_s, "type": e.type, "actor": e.actor, "data": e.data}
    if e.source is not None:
        d["source"] = {"ref": e.source.ref, "note": e.source.note, "confidence": e.source.confidence}
    return d


def dict_to_events(log: Dict[str, Any]) -> List[Event]:
    out: List[Event] = []
    for raw in log.get("events", []):
        src = None
        if isinstance(raw.get("source"), dict):
            src = SourceRef(
                ref=str(raw["source"].get("ref", "")),
                note=str(raw["source"].get("note", "")),
                confidence=str(raw["source"].get("confidence", "high")),
            )
        out.append(
            Event(
                t_rel_s=_float_or_none(raw.get("t_rel_s")),
                type=str(raw.get("type", "")),
                actor=str(raw.get("actor", "")),
                data=dict(raw.get("data", {})),
                source=src,
            )
        )
    return out


# =========================
# ユーティリティ
# =========================

def _has_event(events: Iterable[Event], prefix: str) -> bool:
    return any(e.type.startswith(prefix) for e in events)

def _has_event_type(events: Iterable[Event], event_type: str) -> bool:
    return any(e.type == event_type for e in events)

def _has_timed_event(events: Iterable[Event], prefix: str) -> bool:
    return any(e.type.startswith(prefix) and e.t_rel_s is not None for e in events)

def _count_timed_events(events: Iterable[Event]) -> int:
    return sum(1 for e in events if e.t_rel_s is not None)

def _find_earliest_time(events: Iterable[Event], prefix: str) -> Optional[float]:
    ts = [e.t_rel_s for e in events if e.type.startswith(prefix) and e.t_rel_s is not None]
    return min(ts) if ts else None

def _find_event(events: Iterable[Event], event_type: str) -> Optional[Event]:
    for e in events:
        if e.type == event_type:
            return e
    return None


# =========================
# カバレッジ判定（002互換 + 少し保守的）
# =========================

def compute_evidence_coverage(events: List[Event]) -> Dict[str, Dict[str, Any]]:
    cov: Dict[str, Dict[str, Any]] = {}

    def mark(key: str, status: str, evidence: str) -> None:
        if status not in STATUS_SCORE:
            raise ValueError(status)
        cov[key] = {
            "status": status,
            "score": STATUS_SCORE[status],
            "icon": STATUS_ICON[status],
            "evidence": evidence,
            "title": EVIDENCE_UNITS[key]["title"],
            "why": EVIDENCE_UNITS[key]["why"],
        }

    # time.base
    has_impact = _has_event_type(events, "impact")
    timed_count = _count_timed_events(events)
    if has_impact and timed_count >= 2:
        mark("time.base", "ok", f"impact + timed events ({timed_count}) present")
    elif has_impact:
        mark("time.base", "partial", "impact present but almost no timed context")
    else:
        mark("time.base", "missing", "impact missing")

    # authority.mode_timeline
    if _has_timed_event(events, "authority.mode"):
        mark("authority.mode_timeline", "ok", "authority.mode with timestamp present")
    elif _has_event(events, "authority.mode"):
        mark("authority.mode_timeline", "partial", "authority.mode present (no timestamp)")
    else:
        mark("authority.mode_timeline", "missing", "missing")

    # perception.object_timeline
    has_detect = _has_event(events, "perception.detect")
    has_class = _has_event(events, "perception.classification")
    has_detect_t = _has_timed_event(events, "perception.detect")
    if has_detect and has_class and has_detect_t:
        mark("perception.object_timeline", "ok", "detect(timed) + classification present")
    elif has_detect or has_class:
        mark("perception.object_timeline", "partial", "perception present but incomplete timeline")
    else:
        mark("perception.object_timeline", "missing", "missing")

    # prediction.risk_timeline
    has_pred_or_risk = _has_event(events, "prediction.") or _has_event(events, "risk.")
    has_timed = _has_timed_event(events, "prediction.") or _has_timed_event(events, "risk.")
    if has_pred_or_risk and has_timed:
        mark("prediction.risk_timeline", "ok", "prediction/risk with timestamp present")
    elif has_pred_or_risk:
        mark("prediction.risk_timeline", "partial", "prediction/risk present (no timestamp)")
    else:
        mark("prediction.risk_timeline", "missing", "missing")

    # planning.choice_timeline
    if _has_event(events, "planning."):
        if _has_timed_event(events, "planning."):
            mark("planning.choice_timeline", "ok", "planning.* with timestamp present")
        else:
            mark("planning.choice_timeline", "partial", "planning.* present (no timestamp)")
    else:
        mark("planning.choice_timeline", "missing", "missing")

    # control.command_timeline
    control_cmd_prefixes = (
        "control.command",
        "control.brake",
        "control.steer",
        "control.longitudinal",
        "control.lateral",
        "control.actuator",
        "control.response",
    )
    has_cmd = any(e.type.startswith(control_cmd_prefixes) for e in events)
    has_cmd_t = any(e.type.startswith(control_cmd_prefixes) and e.t_rel_s is not None for e in events)
    has_policy = _has_event_type(events, "control.aeb_policy")
    if has_cmd and has_cmd_t:
        mark("control.command_timeline", "ok", "control commands/responses (timed) present")
    elif has_cmd or has_policy or _has_event(events, "control."):
        mark("control.command_timeline", "partial", "control present but no timed command/response timeline")
    else:
        mark("control.command_timeline", "missing", "missing")

    # human.input_attention
    has_human = _has_event(events, "human.")
    has_human_t = _has_timed_event(events, "human.")
    if has_human and has_human_t:
        mark("human.input_attention", "ok", "human.* timed events present")
    elif has_human:
        mark("human.input_attention", "partial", "human.* present (no timestamp)")
    else:
        mark("human.input_attention", "missing", "missing")

    # software.version_manifest
    if _has_event(events, "software.version"):
        mark("software.version_manifest", "ok", "software.version present")
    else:
        mark("software.version_manifest", "missing", "missing")

    # integrity.tamper_evidence
    if _has_event(events, "integrity."):
        mark("integrity.tamper_evidence", "ok", "integrity.* present")
    else:
        mark("integrity.tamper_evidence", "missing", "missing")

    return cov


# =========================
# スコアリング
# =========================

def score_simple_average(coverage: Dict[str, Dict[str, Any]], keys: List[str]) -> float:
    if not keys:
        return 0.0
    return sum(coverage[k]["score"] for k in keys) / len(keys)

def score_weighted(coverage: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> float:
    if not weights:
        return 0.0
    s = 0.0
    wsum = 0.0
    for k, w in weights.items():
        if k not in coverage:
            continue
        s += coverage[k]["score"] * float(w)
        wsum += float(w)
    return (s / wsum) if wsum > 0 else 0.0


def derive_metrics(events: List[Event]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    t_detect = _find_earliest_time(events, "perception.detect")
    t_gaze = _find_earliest_time(events, "human.attention")
    t_steer = _find_earliest_time(events, "human.control_input")
    metrics["lead_time_detection_s"] = t_detect
    metrics["lead_time_operator_gaze_to_road_s"] = t_gaze
    metrics["lead_time_operator_steer_s"] = t_steer

    if t_detect is not None and t_gaze is not None:
        metrics["gap_detect_to_gaze_s"] = float(t_gaze - t_detect)
    if t_gaze is not None and t_steer is not None:
        metrics["gap_gaze_to_steer_s"] = float(t_steer - t_gaze)

    impact = _find_event(events, "impact")
    if impact:
        metrics["impact_speed_mph"] = impact.data.get("speed_mph")
        metrics["impact_speed_kmh"] = impact.data.get("speed_kmh")
    return metrics


def unanswerable_questions(coverage: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    “責任確定”のための主要7問いを列挙し、答えられない（status != ok）ものを返す。
    """
    questions = [
        ("Q1", "誰が最終権限を持っていたか", "authority.mode_timeline"),
        ("Q2", "システムは対象を検知・追跡していたか", "perception.object_timeline"),
        ("Q3", "システムは危険（衝突）を評価していたか", "prediction.risk_timeline"),
        ("Q4", "システムは何を“選択”したか（候補と理由）", "planning.choice_timeline"),
        ("Q5", "システムは制動/回避のコマンドを出し、車は応答したか", "control.command_timeline"),
        ("Q6", "どの版数・更新履歴で起きたか（再現性/供給責任）", "software.version_manifest"),
        ("Q7", "ログは改竄不能か（完全性）", "integrity.tamper_evidence"),
    ]
    out: List[Dict[str, Any]] = []
    for qid, qtext, unit in questions:
        st = coverage[unit]["status"]
        if st != "ok":
            out.append({"id": qid, "question": qtext, "unit": unit, "status": st, "evidence": coverage[unit]["evidence"]})
    return out


def render_report_md(log: Dict[str, Any], events: List[Event]) -> str:
    case = log.get("case", {})
    case_id = case.get("case_id", "unknown_case")

    coverage = compute_evidence_coverage(events)

    # Scores
    all_keys = list(EVIDENCE_UNITS.keys())
    a_score = score_simple_average(coverage, all_keys)
    c_score = score_simple_average(coverage, CRITICAL_UNITS)
    r_core = score_weighted(coverage, CORE_WEIGHTS)
    r_supply = score_weighted(coverage, SUPPLY_WEIGHTS)
    q_missing = unanswerable_questions(coverage)
    metrics = derive_metrics(events)

    # Pretty percent
    def pct(x: float) -> str:
        return f"{x*100:.0f}%"

    lines: List[str] = []
    lines.append(f"# SIA Public Audit Report (Quant): {case_id}")
    lines.append("")
    lines.append(f"- Generated at: {log.get('generated_at', _iso_now())}")
    lines.append(f"- Schema: {log.get('schema', '')}")
    lines.append("")
    lines.append("## 1. Quantifying “cannot determine responsibility due to missing logs”")
    lines.append("")
    lines.append(f"- **Auditability Score (A-score)**: {pct(a_score)}  (all 9 units, OK=1 / Partial=0.5 / Missing=0)")
    lines.append(f"- **Accountability-Critical Score (C-score)**: {pct(c_score)}  (planning + control + version + integrity)")
    lines.append(f"- **Responsibility Determinability (core)**: {pct(r_core)}  (authority/perception/prediction/planning/control/human)")
    lines.append(f"- **Supply-chain Determinability**: {pct(r_supply)}  (version + integrity)")
    lines.append(f"- **Unanswerable key questions**: {len(q_missing)}/7")
    lines.append("")
    lines.append("Interpretation guide (practical, conservative):")
    lines.append("- ≥80%: likely determinable (assuming integrity is OK)")
    lines.append("- 50–79%: partially determinable (multiple narratives remain plausible)")
    lines.append("- <50%: not determinable (responsibility attribution will be disputed)")
    lines.append("")
    lines.append("## 2. Missing questions (what you cannot answer today)")
    lines.append("")
    if not q_missing:
        lines.append("- None (all key questions are answerable)")
    else:
        for q in q_missing:
            lines.append(f"- {q['id']} [{q['status']}]: {q['question']}  (unit={q['unit']}, evidence={q['evidence']})")
    lines.append("")
    lines.append("## 3. Evidence coverage by unit")
    lines.append("")
    lines.append("| Unit | Status | Evidence | Why it matters |")
    lines.append("|---|---:|---|---|")
    for key in EVIDENCE_UNITS.keys():
        v = coverage[key]
        lines.append(f"| {v['title']} (`{key}`) | {v['icon']} {v['status']} | {v['evidence']} | {v['why']} |")
    lines.append("")
    lines.append("## 4. Derived metrics (only from available public evidence)")
    lines.append("")
    for k, v in metrics.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## 5. What to request next (minimal additions that raise C-score fastest)")
    lines.append("")
    lines.append("To raise Accountability-Critical Score (C-score), you typically need:")
    lines.append("- planning: candidate plans + chosen plan + rationale (even a compact reason code helps)")
    lines.append("- control: brake/steer commands AND actuator response (actual decel / speed trace)")
    lines.append("- version: stack/map/model versions + update history around the incident")
    lines.append("- integrity: tamper-evident hash/signature for the extracted log segment")
    lines.append("")
    lines.append("> Note: This report does not assign blame. It quantifies what cannot be determined without missing logs.")
    lines.append("")
    return "\n".join(lines)


def print_console_summary(log: Dict[str, Any], events: List[Event]) -> None:
    case = log.get("case", {})
    case_id = case.get("case_id", "unknown_case")
    title = case.get("title", "")

    coverage = compute_evidence_coverage(events)
    a_score = score_simple_average(coverage, list(EVIDENCE_UNITS.keys()))
    c_score = score_simple_average(coverage, CRITICAL_UNITS)
    r_core = score_weighted(coverage, CORE_WEIGHTS)
    r_supply = score_weighted(coverage, SUPPLY_WEIGHTS)
    q_missing = unanswerable_questions(coverage)

    print("=" * 80)
    print(f"SIA Public Audit Demo (Quant) [{SCHEMA_VERSION}] [003]")
    print(f"CASE: {case_id}")
    if title:
        print(f"TITLE: {title}")
    print("=" * 80)
    print(f"[Scores] A-score={a_score*100:.0f}% | C-score={c_score*100:.0f}% | core={r_core*100:.0f}% | supply={r_supply*100:.0f}% | unanswerable={len(q_missing)}/7")
    print("")
    for key in EVIDENCE_UNITS.keys():
        v = coverage[key]
        print(f"  - {v['icon']} {v['status']:7s} {key}: {v['evidence']}")
    if q_missing:
        print("\n[Unanswerable questions]")
        for q in q_missing:
            print(f"  - {q['id']} {q['status']}: {q['question']} (unit={q['unit']})")
    print("=" * 80)


# =========================
# I/O
# =========================

SAMPLES = {"uber_atg_ntsb_2018": sample_uber_atg_ntsb_2018}

def load_log(input_path: Optional[Path], sample: Optional[str]) -> Dict[str, Any]:
    if input_path:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Input JSON must be an object.")
        return raw
    if sample:
        if sample not in SAMPLES:
            raise ValueError(f"Unknown sample '{sample}'. Available: {', '.join(SAMPLES.keys())}")
        return SAMPLES[sample]()
    return sample_uber_atg_ntsb_2018()

def write_outputs(log: Dict[str, Any], report_md: str, out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    case_id = log.get("case", {}).get("case_id", "unknown_case")
    json_path = out_dir / f"{case_id}_sia_minimal.json"
    md_path = out_dir / f"{case_id}_sia_audit_report.md"
    json_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_md, encoding="utf-8")
    return json_path, md_path

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="sia_public_audit_demo_003.py",
        formatter_class=argparse.RawTextHelpFormatter,
        description=textwrap.dedent(
            """
            公開ログから「責任が確定できない」を定量化して見せる（003版）。

            例:
              python sia_public_audit_demo_003.py --sample uber_atg_ntsb_2018 --out_dir out_demo
              python sia_public_audit_demo_003.py --input your_case.json --out_dir out_demo
            """
        ).strip(),
    )
    ap.add_argument("--input", type=str, default="", help="Input JSON path (public minimal log)")
    ap.add_argument("--sample", type=str, default="", help=f"Built-in sample: {', '.join(SAMPLES.keys())}")
    ap.add_argument("--out_dir", type=str, default=".", help="Output directory")
    ap.add_argument("--no_files", action="store_true", help="Do not write output files (console only)")
    args = ap.parse_args()

    input_path = Path(args.input) if args.input else None
    out_dir = Path(args.out_dir)

    log = load_log(input_path=input_path, sample=args.sample if args.sample else None)
    events = dict_to_events(log)

    print_console_summary(log, events)
    report_md = render_report_md(log, events)

    if not args.no_files:
        json_path, md_path = write_outputs(log, report_md, out_dir)
        print(f"\n[Wrote] {json_path}")
        print(f"[Wrote] {md_path}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

