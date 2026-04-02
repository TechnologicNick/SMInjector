from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RESULTS_ROOT = SCRIPT_DIR / "benchmark_results"
DEFAULT_OUTPUT_DIRNAME = "graphs"
TARGET_GPU_NAME = "NVIDIA GeForce RTX 5090"
ANNOTATED_THREAD_COUNTS = {1, 4, 32}
DEFAULT_PLOTS = ("energy", "power", "fps", "usage")
DEFAULT_SAVE_DISPLAY_NAMES = {
    "creative_flat": "Creative Flat",
    "creative_terrain": "Creative Terrain",
    "survival": "Survival",
}


@dataclass(frozen=True)
class RunMetrics:
    save: str
    settings_config_name: str
    settings_config_path: str | None
    settings_snapshot_path: str | None
    thread_count: int
    measure_seconds: float
    sample_count: int
    gpu_slot: int
    gpu_name: str
    avg_fps: float
    fps_1pct_low: float
    avg_cpu_usage_pct: float
    avg_gpu_usage_pct: float
    avg_cpu_power_w: float
    avg_gpu_power_w: float
    cpu_energy_j: float
    gpu_energy_j: float
    total_energy_j: float
    run_dir: Path
    session_dir: Path
    session_name: str


class HmlParseError(RuntimeError):
    pass


@dataclass(frozen=True)
class GpuMapping:
    slot: int
    name: str


@dataclass(frozen=True)
class SessionFallback:
    gpu_mapping: GpuMapping | None
    metric_names: tuple[str, ...] | None


@dataclass(frozen=True)
class SessionMetadata:
    description: str
    save_display_names: dict[str, str]
    settings_configs: list[dict[str, str]]
    settings_config_name: str | None
    settings_config_path: str | None
    settings_snapshot_path: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate graphs from Scraptifine benchmark results."
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=DEFAULT_RESULTS_ROOT,
        help="Root directory containing benchmark session folders.",
    )
    parser.add_argument(
        "--session",
        type=Path,
        action="append",
        help="Benchmark session folder to graph. Repeat to merge multiple sessions. Defaults to the newest session under benchmark_results.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for generated graphs and summary CSV. Defaults to <session>/graphs.",
    )
    parser.add_argument(
        "--save",
        action="append",
        help="Only graph the specified save name. Repeat to keep multiple saves.",
    )
    parser.add_argument(
        "--description",
        help="Override the session description used in graph titles, for example '2160p'.",
    )
    parser.add_argument(
        "--save-display-name",
        action="append",
        nargs=2,
        metavar=("SAVE", "LABEL"),
        help="Override the display name for a save, for example --save-display-name creative_flat 'Creative Flat'.",
    )
    parser.add_argument(
        "--min-line-ratio",
        type=float,
        default=0.95,
        help="Reject 80-rows shorter than this fraction of the median line length of the last valid samples.",
    )
    parser.add_argument(
        "--tail-sample-count",
        type=int,
        default=50,
        help="Number of trailing valid sample rows used to determine the expected long line length.",
    )
    parser.add_argument(
        "--plots",
        nargs="+",
        choices=DEFAULT_PLOTS,
        default=list(DEFAULT_PLOTS),
        help="Which plots to include in each dashboard. Defaults to: energy power fps usage.",
    )
    return parser.parse_args()


def resolve_session_paths(results_root: Path, requested: list[Path] | None) -> list[Path]:
    if requested:
        resolved: list[Path] = []
        for item in requested:
            if item.exists():
                resolved.append(item.resolve())
                continue
            candidate = (results_root / item).resolve()
            if candidate.exists():
                resolved.append(candidate)
                continue
            raise FileNotFoundError(f"Benchmark session not found: {item}")
        return resolved

    sessions = [path for path in results_root.iterdir() if path.is_dir()]
    if not sessions:
        raise FileNotFoundError(f"No benchmark sessions found under {results_root}")
    return [max(sessions, key=lambda path: path.stat().st_mtime)]


def load_session_metadata(session_dir: Path) -> SessionMetadata:
    metadata_path = session_dir / "metadata.json"
    description = ""
    save_display_names = dict(DEFAULT_SAVE_DISPLAY_NAMES)
    settings_configs: list[dict[str, str]] = []
    settings_config_name = None
    settings_config_path = None
    settings_snapshot_path = None

    if metadata_path.exists():
        raw = json.loads(metadata_path.read_text(encoding="utf-8"))
        description = str(raw.get("description", ""))
        for save_name, label in raw.get("save_display_names", {}).items():
            save_display_names[str(save_name)] = str(label)
        for item in raw.get("settings_configs", []):
            if not isinstance(item, dict):
                continue
            settings_configs.append({str(key): str(value) for key, value in item.items()})
        if raw.get("settings_config_name") is not None:
            settings_config_name = str(raw.get("settings_config_name"))
        if raw.get("settings_config_path") is not None:
            settings_config_path = str(raw.get("settings_config_path"))
        if raw.get("settings_snapshot_path") is not None:
            settings_snapshot_path = str(raw.get("settings_snapshot_path"))

    return SessionMetadata(
        description=description,
        save_display_names=save_display_names,
        settings_configs=settings_configs,
        settings_config_name=settings_config_name,
        settings_config_path=settings_config_path,
        settings_snapshot_path=settings_snapshot_path,
    )


def apply_session_metadata_overrides(
    session_metadata: SessionMetadata,
    description_override: str | None,
    save_display_name_overrides: list[list[str]] | None,
) -> SessionMetadata:
    description = session_metadata.description if description_override is None else description_override
    save_display_names = dict(session_metadata.save_display_names)

    if save_display_name_overrides:
        for save_name, label in save_display_name_overrides:
            save_display_names[save_name] = label

    return SessionMetadata(
        description=description,
        save_display_names=save_display_names,
        settings_configs=session_metadata.settings_configs,
        settings_config_name=session_metadata.settings_config_name,
        settings_config_path=session_metadata.settings_config_path,
        settings_snapshot_path=session_metadata.settings_snapshot_path,
    )


def write_session_metadata(session_dir: Path, session_metadata: SessionMetadata) -> None:
    metadata = {
        "description": session_metadata.description,
        "save_display_names": session_metadata.save_display_names,
    }
    if session_metadata.settings_configs:
        metadata["settings_configs"] = session_metadata.settings_configs
    if session_metadata.settings_config_name is not None:
        metadata["settings_config_name"] = session_metadata.settings_config_name
    if session_metadata.settings_config_path is not None:
        metadata["settings_config_path"] = session_metadata.settings_config_path
    if session_metadata.settings_snapshot_path is not None:
        metadata["settings_snapshot_path"] = session_metadata.settings_snapshot_path
    (session_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=4) + "\n",
        encoding="utf-8",
    )


def parse_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped or stripped == "N/A":
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def mean_or_fail(values: list[float], metric_name: str, hml_path: Path) -> float:
    if not values:
        raise HmlParseError(f"{hml_path}: no numeric samples for {metric_name}")
    return statistics.fmean(values)


def compute_1pct_low(fps_values: list[float], hml_path: Path) -> float:
    if not fps_values:
        raise HmlParseError(f"{hml_path}: no numeric framerate samples")
    sorted_values = sorted(fps_values)
    bucket_size = max(1, math.ceil(len(sorted_values) * 0.01))
    return statistics.fmean(sorted_values[:bucket_size])


def find_row(rows_with_lines: list[tuple[str, list[str]]], row_type: str) -> list[str]:
    for _, row in rows_with_lines:
        if row and row[0].strip() == row_type:
            return row
    raise HmlParseError(f"Missing required HML row type {row_type}")


def find_optional_row(
    rows_with_lines: list[tuple[str, list[str]]], row_type: str
) -> list[str] | None:
    for _, row in rows_with_lines:
        if row and row[0].strip() == row_type:
            return row
    return None


def extract_target_gpu_mapping(
    rows_with_lines: list[tuple[str, list[str]]], hml_path: Path
) -> GpuMapping | None:
    gpu_row = find_optional_row(rows_with_lines, "01")
    if gpu_row is None:
        return None

    gpu_names = [value.strip() for value in gpu_row[2:] if value.strip()]
    if not gpu_names:
        raise HmlParseError(f"{hml_path}: no GPU names found in row 01")

    matches: list[GpuMapping] = []
    for idx, name in enumerate(gpu_names, start=1):
        if TARGET_GPU_NAME in name:
            matches.append(GpuMapping(slot=idx, name=name))

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise HmlParseError(
            f"{hml_path}: target GPU '{TARGET_GPU_NAME}' appeared multiple times in row 01"
        )

    raise HmlParseError(
        f"{hml_path}: target GPU '{TARGET_GPU_NAME}' was not found in {gpu_names}"
    )


def parse_hml_metrics(
    hml_path: Path,
    measure_seconds: float,
    min_line_ratio: float,
    tail_sample_count: int,
    session_fallback: SessionFallback,
) -> tuple[int, str, int, float, float, float, float, float, float, float]:
    with hml_path.open("r", encoding="cp1251", errors="replace", newline="") as handle:
        raw_lines = handle.read().splitlines()

    rows = list(csv.reader(raw_lines))
    rows_with_lines = list(zip(raw_lines, rows))

    header_row = find_optional_row(rows_with_lines, "02")
    if header_row is None:
        if session_fallback.metric_names is None:
            raise HmlParseError("Missing required HML row type 02")
        metric_names = list(session_fallback.metric_names)
    else:
        metric_names = [value.strip() for value in header_row[2:]]
        if not metric_names:
            raise HmlParseError(f"{hml_path}: no metric names found in row 02")

    expected_fields = len(metric_names) + 2

    try:
        gpu_mapping = extract_target_gpu_mapping(rows_with_lines, hml_path)
    except HmlParseError as exc:
        if session_fallback.gpu_mapping is None:
            raise
        message = str(exc)
        if TARGET_GPU_NAME not in message and "row 01" not in message:
            raise
        gpu_mapping = session_fallback.gpu_mapping

    if gpu_mapping is None:
        if session_fallback.gpu_mapping is None:
            raise HmlParseError("Missing required HML row type 01")
        gpu_mapping = session_fallback.gpu_mapping

    target_gpu_slot = gpu_mapping.slot
    target_gpu_name = gpu_mapping.name

    def metric_index(metric_name: str) -> int:
        try:
            return metric_names.index(metric_name)
        except ValueError as exc:
            raise HmlParseError(f"{hml_path}: missing metric column '{metric_name}'") from exc

    fps_idx = metric_index("Framerate")
    cpu_usage_idx = metric_index("CPU usage")
    cpu_power_idx = metric_index("CPU power")
    gpu_usage_idx = metric_index(f"GPU{target_gpu_slot} usage")
    gpu_power_idx = metric_index(f"GPU{target_gpu_slot} power")

    candidate_rows: list[tuple[str, list[str]]] = []
    for raw_line, row in rows_with_lines:
        if not row or row[0].strip() != "80":
            continue
        if len(row) < expected_fields:
            continue
        candidate_rows.append((raw_line, row))

    if not candidate_rows:
        raise HmlParseError(f"{hml_path}: no valid 80 sample rows found")

    tail_lengths = [len(raw_line) for raw_line, _ in candidate_rows[-tail_sample_count:]]
    median_tail_length = statistics.median(tail_lengths)
    min_allowed_length = median_tail_length * min_line_ratio

    filtered_rows = [
        row for raw_line, row in candidate_rows if len(raw_line) >= min_allowed_length
    ]
    if not filtered_rows:
        raise HmlParseError(
            f"{hml_path}: all sample rows were rejected by the line-length filter"
        )

    fps_values: list[float] = []
    cpu_usage_values: list[float] = []
    gpu_usage_values: list[float] = []
    cpu_power_values: list[float] = []
    gpu_power_values: list[float] = []

    for row in filtered_rows:
        values = row[2:]
        fps = parse_float(values[fps_idx])
        cpu_usage = parse_float(values[cpu_usage_idx])
        gpu_usage = parse_float(values[gpu_usage_idx])
        cpu_power = parse_float(values[cpu_power_idx])
        gpu_power = parse_float(values[gpu_power_idx])

        if fps is not None:
            fps_values.append(fps)
        if cpu_usage is not None:
            cpu_usage_values.append(cpu_usage)
        if gpu_usage is not None:
            gpu_usage_values.append(gpu_usage)
        if cpu_power is not None:
            cpu_power_values.append(cpu_power)
        if gpu_power is not None:
            gpu_power_values.append(gpu_power)

    avg_fps = mean_or_fail(fps_values, "Framerate", hml_path)
    fps_1pct_low = compute_1pct_low(fps_values, hml_path)
    avg_cpu_usage_pct = mean_or_fail(cpu_usage_values, "CPU usage", hml_path)
    avg_gpu_usage_pct = mean_or_fail(gpu_usage_values, f"GPU{target_gpu_slot} usage", hml_path)
    avg_cpu_power_w = mean_or_fail(cpu_power_values, "CPU power", hml_path)
    avg_gpu_power_w = mean_or_fail(gpu_power_values, f"GPU{target_gpu_slot} power", hml_path)

    cpu_energy_j = avg_cpu_power_w * measure_seconds
    gpu_energy_j = avg_gpu_power_w * measure_seconds
    total_energy_j = cpu_energy_j + gpu_energy_j

    return (
        target_gpu_slot,
        target_gpu_name,
        len(filtered_rows),
        avg_fps,
        fps_1pct_low,
        avg_cpu_usage_pct,
        avg_gpu_usage_pct,
        avg_cpu_power_w,
        avg_gpu_power_w,
        total_energy_j,
    )


def load_run_metrics(
    run_dir: Path,
    session_dir: Path,
    min_line_ratio: float,
    tail_sample_count: int,
    session_fallback: SessionFallback,
) -> RunMetrics:
    metadata_path = run_dir / "metadata.json"
    hml_path = run_dir / "HardwareMonitoring.hml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"{run_dir}: metadata.json is missing")
    if not hml_path.exists():
        raise FileNotFoundError(f"{run_dir}: HardwareMonitoring.hml is missing")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    measure_seconds = float(metadata["measure_seconds"])
    thread_count = int(metadata["thread_count"])
    save = str(metadata["save"])
    settings_config_name = str(metadata.get("settings_config_name", "default"))
    settings_config_path = (
        str(metadata["settings_config_path"])
        if metadata.get("settings_config_path") is not None
        else None
    )
    settings_snapshot_path = (
        str(metadata["settings_snapshot_path"])
        if metadata.get("settings_snapshot_path") is not None
        else None
    )

    (
        gpu_slot,
        gpu_name,
        sample_count,
        avg_fps,
        fps_1pct_low,
        avg_cpu_usage_pct,
        avg_gpu_usage_pct,
        avg_cpu_power_w,
        avg_gpu_power_w,
        total_energy_j,
    ) = parse_hml_metrics(
        hml_path=hml_path,
        measure_seconds=measure_seconds,
        min_line_ratio=min_line_ratio,
        tail_sample_count=tail_sample_count,
        session_fallback=session_fallback,
    )

    cpu_energy_j = avg_cpu_power_w * measure_seconds
    gpu_energy_j = avg_gpu_power_w * measure_seconds

    return RunMetrics(
        save=save,
        settings_config_name=settings_config_name,
        settings_config_path=settings_config_path,
        settings_snapshot_path=settings_snapshot_path,
        thread_count=thread_count,
        measure_seconds=measure_seconds,
        sample_count=sample_count,
        gpu_slot=gpu_slot,
        gpu_name=gpu_name,
        avg_fps=avg_fps,
        fps_1pct_low=fps_1pct_low,
        avg_cpu_usage_pct=avg_cpu_usage_pct,
        avg_gpu_usage_pct=avg_gpu_usage_pct,
        avg_cpu_power_w=avg_cpu_power_w,
        avg_gpu_power_w=avg_gpu_power_w,
        cpu_energy_j=cpu_energy_j,
        gpu_energy_j=gpu_energy_j,
        total_energy_j=total_energy_j,
        run_dir=run_dir,
        session_dir=session_dir,
        session_name=session_dir.name,
    )


def iter_run_dirs(session_dir: Path) -> Iterable[Path]:
    return sorted(
        path
        for path in session_dir.iterdir()
        if path.is_dir() and not path.name.startswith(DEFAULT_OUTPUT_DIRNAME)
    )


def infer_session_gpu_mapping(session_dir: Path) -> GpuMapping | None:
    observed_mappings: set[GpuMapping] = set()

    for run_dir in iter_run_dirs(session_dir):
        hml_path = run_dir / "HardwareMonitoring.hml"
        if not hml_path.exists():
            continue

        with hml_path.open("r", encoding="cp1251", errors="replace", newline="") as handle:
            raw_lines = handle.read().splitlines()
        rows = list(csv.reader(raw_lines))
        rows_with_lines = list(zip(raw_lines, rows))

        try:
            mapping = extract_target_gpu_mapping(rows_with_lines, hml_path)
        except HmlParseError:
            continue

        if mapping is not None:
            observed_mappings.add(mapping)

    if not observed_mappings:
        return None

    if len(observed_mappings) != 1:
        formatted = ", ".join(
            f"GPU{mapping.slot}={mapping.name}" for mapping in sorted(observed_mappings, key=lambda item: item.slot)
        )
        raise HmlParseError(f"Inconsistent target GPU mapping across session: {formatted}")

    return next(iter(observed_mappings))


def infer_session_metric_names(session_dir: Path) -> tuple[str, ...] | None:
    observed_headers: set[tuple[str, ...]] = set()

    for run_dir in iter_run_dirs(session_dir):
        hml_path = run_dir / "HardwareMonitoring.hml"
        if not hml_path.exists():
            continue

        with hml_path.open("r", encoding="cp1251", errors="replace", newline="") as handle:
            raw_lines = handle.read().splitlines()
        rows = list(csv.reader(raw_lines))
        rows_with_lines = list(zip(raw_lines, rows))

        header_row = find_optional_row(rows_with_lines, "02")
        if header_row is None:
            continue

        metric_names = tuple(value.strip() for value in header_row[2:])
        if metric_names:
            observed_headers.add(metric_names)

    if not observed_headers:
        return None

    if len(observed_headers) != 1:
        raise HmlParseError("Inconsistent HML metric header row across session")

    return next(iter(observed_headers))


def collect_metrics(
    session_dirs: list[Path],
    keep_saves: set[str] | None,
    min_line_ratio: float,
    tail_sample_count: int,
) -> list[RunMetrics]:
    session_fallbacks = {
        session_dir: SessionFallback(
            gpu_mapping=infer_session_gpu_mapping(session_dir),
            metric_names=infer_session_metric_names(session_dir),
        )
        for session_dir in session_dirs
    }
    selected_runs: dict[tuple[str, str, int], tuple[Path, Path]] = {}
    for session_dir in sorted(session_dirs, key=lambda path: path.stat().st_mtime):
        for run_dir in iter_run_dirs(session_dir):
            metadata_path = run_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                key = (
                    str(metadata["save"]),
                    str(metadata.get("settings_config_name", "default")),
                    int(metadata["thread_count"]),
                )
            except Exception:
                continue
            selected_runs[key] = (session_dir, run_dir)

    collected: list[RunMetrics] = []
    for session_dir, run_dir in selected_runs.values():
        session_fallback = SessionFallback(
            gpu_mapping=session_fallbacks[session_dir].gpu_mapping,
            metric_names=session_fallbacks[session_dir].metric_names,
        )
        try:
            metrics = load_run_metrics(
                run_dir=run_dir,
                session_dir=session_dir,
                min_line_ratio=min_line_ratio,
                tail_sample_count=tail_sample_count,
                session_fallback=session_fallback,
            )
        except Exception as exc:
            print(f"[warn] skipping {run_dir.name}: {exc}", file=sys.stderr)
            continue

        if keep_saves is not None and metrics.save not in keep_saves:
            continue

        collected.append(metrics)

    collected.sort(key=lambda item: (item.save, item.settings_config_name, item.thread_count))
    return collected


def write_summary_csv(output_dir: Path, metrics_rows: list[RunMetrics]) -> Path:
    output_path = output_dir / "summary.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "save",
                "settings_config_name",
                "settings_config_path",
                "settings_snapshot_path",
                "thread_count",
                "sample_count",
                "measure_seconds",
                "gpu_slot",
                "gpu_name",
                "avg_fps",
                "fps_1pct_low",
                "avg_cpu_usage_pct",
                "avg_gpu_usage_pct",
                "avg_cpu_power_w",
                "avg_gpu_power_w",
                "cpu_energy_j",
                "gpu_energy_j",
                "total_energy_j",
                "session_name",
                "run_dir",
            ],
        )
        writer.writeheader()
        for item in metrics_rows:
            writer.writerow(
                {
                    "save": item.save,
                    "settings_config_name": item.settings_config_name,
                    "settings_config_path": item.settings_config_path or "",
                    "settings_snapshot_path": item.settings_snapshot_path or "",
                    "thread_count": item.thread_count,
                    "sample_count": item.sample_count,
                    "measure_seconds": f"{item.measure_seconds:.3f}",
                    "gpu_slot": item.gpu_slot,
                    "gpu_name": item.gpu_name,
                    "avg_fps": f"{item.avg_fps:.3f}",
                    "fps_1pct_low": f"{item.fps_1pct_low:.3f}",
                    "avg_cpu_usage_pct": f"{item.avg_cpu_usage_pct:.3f}",
                    "avg_gpu_usage_pct": f"{item.avg_gpu_usage_pct:.3f}",
                    "avg_cpu_power_w": f"{item.avg_cpu_power_w:.3f}",
                    "avg_gpu_power_w": f"{item.avg_gpu_power_w:.3f}",
                    "cpu_energy_j": f"{item.cpu_energy_j:.3f}",
                    "gpu_energy_j": f"{item.gpu_energy_j:.3f}",
                    "total_energy_j": f"{item.total_energy_j:.3f}",
                    "session_name": item.session_name,
                    "run_dir": str(item.run_dir),
                }
            )
    return output_path


def try_load_settings_payload(path_str: str | None) -> dict[str, object] | None:
    if not path_str:
        return None

    path = Path(path_str)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    return payload


def settings_resolution_label(item: RunMetrics) -> str | None:
    payload = try_load_settings_payload(item.settings_snapshot_path)
    if payload is None:
        payload = try_load_settings_payload(item.settings_config_path)
    if payload is None:
        return None

    width = payload.get("Width")
    height = payload.get("Height")
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        return None

    height_int = int(height)
    width_int = int(width)
    if height_int in {720, 1080, 1440, 2160}:
        return f"{height_int}p"
    return f"{width_int}x{height_int}"


def build_settings_label_map(rows: list[RunMetrics]) -> dict[str, str]:
    unique_rows: dict[str, RunMetrics] = {}
    for item in rows:
        unique_rows.setdefault(item.settings_config_name, item)

    base_labels: dict[str, str] = {}
    counts: dict[str, int] = {}
    for settings_name, item in unique_rows.items():
        label = settings_resolution_label(item) or settings_name
        base_labels[settings_name] = label
        counts[label] = counts.get(label, 0) + 1

    resolved: dict[str, str] = {}
    for settings_name, label in base_labels.items():
        resolved[settings_name] = label if counts[label] == 1 else settings_name
    return resolved


def annotate_selected_points(
    axis: plt.Axes,
    rows: list[RunMetrics],
    value_getter,
    fmt: str,
    color: str,
    y_offset: float = 8.0,
) -> None:
    for item in rows:
        if item.thread_count not in ANNOTATED_THREAD_COUNTS:
            continue
        value = value_getter(item)
        axis.annotate(
            fmt.format(value),
            (item.thread_count, value),
            xytext=(0, y_offset),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=color,
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": color, "alpha": 0.8},
        )


def build_mosaic(selected_plots: list[str]) -> list[list[str]]:
    if len(selected_plots) == 1:
        return [[selected_plots[0]]]
    if len(selected_plots) == 2:
        return [[selected_plots[0], selected_plots[1]]]
    if len(selected_plots) == 3:
        return [[selected_plots[0], selected_plots[1]], [selected_plots[2], selected_plots[2]]]
    return [[selected_plots[0], selected_plots[1]], [selected_plots[2], selected_plots[3]]]


def make_dashboard(
    output_dir: Path,
    session_name: str,
    save_name: str,
    settings_config_name: str,
    display_name: str,
    description: str,
    rows: list[RunMetrics],
    selected_plots: list[str],
) -> Path:
    rows = sorted(rows, key=lambda item: item.thread_count)
    thread_counts = [item.thread_count for item in rows]
    max_thread_count = max(thread_counts)
    x_ticks = sorted({thread_counts[0], *range(4, max_thread_count + 1, 4)})

    if len(selected_plots) <= 2:
        figsize = (14, 5.5)
    else:
        figsize = (14, 9)

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    mosaic = fig.subplot_mosaic(build_mosaic(selected_plots))
    title = f"Scraptifine Benchmark: {display_name} ({settings_config_name})"
    if description:
        title += f" - {description}"
    fig.suptitle(title, fontsize=16)

    if "energy" in mosaic:
        ax_energy = mosaic["energy"]
        cpu_energy = [item.cpu_energy_j for item in rows]
        gpu_energy = [item.gpu_energy_j for item in rows]
        total_energy = [item.total_energy_j for item in rows]
        ax_energy.bar(thread_counts, cpu_energy, width=0.8, label="CPU energy (J)", color="#3d7ea6")
        ax_energy.bar(
            thread_counts,
            gpu_energy,
            width=0.8,
            bottom=cpu_energy,
            label="GPU energy (J)",
            color="#d68c45",
        )
        ax_energy.plot(thread_counts, total_energy, color="#222222", marker="o", label="Total energy (J)")
        ax_energy.set_title("Energy Usage")
        ax_energy.set_xlabel("Thread Count")
        ax_energy.set_ylabel("Energy (J)")
        ax_energy.set_xticks(x_ticks)
        ax_energy.grid(True, axis="y", alpha=0.3)
        ax_energy.legend()
        annotate_selected_points(ax_energy, rows, lambda item: item.total_energy_j, "{:.0f}", "#222222")

    if "power" in mosaic:
        ax_power = mosaic["power"]
        avg_cpu_power = [item.avg_cpu_power_w for item in rows]
        avg_gpu_power = [item.avg_gpu_power_w for item in rows]
        total_power = [item.avg_cpu_power_w + item.avg_gpu_power_w for item in rows]
        ax_power.plot(thread_counts, avg_cpu_power, marker="o", color="#3d7ea6", label="CPU power (W)")
        ax_power.plot(thread_counts, avg_gpu_power, marker="o", color="#d68c45", label="GPU power (W)")
        ax_power.plot(thread_counts, total_power, marker="o", color="#222222", label="Total power (W)")
        ax_power.set_title("Power Usage")
        ax_power.set_xlabel("Thread Count")
        ax_power.set_ylabel("Power (W)")
        ax_power.set_xticks(x_ticks)
        ax_power.set_ylim(bottom=0, top=max(total_power) * 1.12)
        ax_power.grid(True, alpha=0.3)
        ax_power.legend()
        annotate_selected_points(ax_power, rows, lambda item: item.avg_cpu_power_w, "{:.1f}", "#3d7ea6", y_offset=10.0)
        annotate_selected_points(ax_power, rows, lambda item: item.avg_gpu_power_w, "{:.1f}", "#d68c45", y_offset=-18.0)
        annotate_selected_points(
            ax_power,
            rows,
            lambda item: item.avg_cpu_power_w + item.avg_gpu_power_w,
            "{:.1f}",
            "#222222",
            y_offset=8.0,
        )

    if "fps" in mosaic:
        ax_fps = mosaic["fps"]
        avg_fps = [item.avg_fps for item in rows]
        low_fps = [item.fps_1pct_low for item in rows]
        ax_fps.plot(thread_counts, avg_fps, marker="o", color="#2c8c59", label="Average FPS")
        ax_fps.plot(thread_counts, low_fps, marker="o", color="#8c2c5a", label="1% low FPS")
        ax_fps.set_title("Framerate")
        ax_fps.set_xlabel("Thread Count")
        ax_fps.set_ylabel("FPS")
        ax_fps.set_xticks(x_ticks)
        ax_fps.grid(True, alpha=0.3)
        ax_fps.legend()
        annotate_selected_points(ax_fps, rows, lambda item: item.avg_fps, "{:.1f}", "#2c8c59")

    if "usage" in mosaic:
        ax_usage = mosaic["usage"]
        avg_cpu_usage = [item.avg_cpu_usage_pct for item in rows]
        avg_gpu_usage = [item.avg_gpu_usage_pct for item in rows]
        ax_usage.plot(thread_counts, avg_cpu_usage, marker="o", color="#4c78a8", label="CPU usage")
        ax_usage.plot(
            thread_counts,
            avg_gpu_usage,
            marker="o",
            color="#f58518",
            label=f"GPU usage ({rows[0].gpu_name})",
        )
        ax_usage.set_title("CPU and GPU Usage")
        ax_usage.set_xlabel("Thread Count")
        ax_usage.set_ylabel("Usage (%)")
        ax_usage.set_xticks(x_ticks)
        ax_usage.set_ylim(bottom=0)
        ax_usage.grid(True, alpha=0.3)
        ax_usage.legend()
        annotate_selected_points(ax_usage, rows, lambda item: item.avg_cpu_usage_pct, "{:.1f}", "#4c78a8", y_offset=10.0)
        annotate_selected_points(ax_usage, rows, lambda item: item.avg_gpu_usage_pct, "{:.1f}", "#f58518", y_offset=-18.0)

    output_path = output_dir / f"{save_name}_{settings_config_name}_dashboard.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def make_settings_comparison_dashboard(
    output_dir: Path,
    save_name: str,
    display_name: str,
    description: str,
    rows: list[RunMetrics],
    selected_plots: list[str],
) -> Path:
    grouped_rows: dict[str, list[RunMetrics]] = {}
    for item in rows:
        grouped_rows.setdefault(item.settings_config_name, []).append(item)

    label_map = build_settings_label_map(rows)
    ordered_settings = sorted(
        grouped_rows,
        key=lambda name: (
            label_map.get(name, name),
            name,
        ),
    )

    all_thread_counts = sorted({item.thread_count for item in rows})
    max_thread_count = max(all_thread_counts)
    x_ticks = sorted({all_thread_counts[0], *range(4, max_thread_count + 1, 4)})

    if len(selected_plots) <= 2:
        figsize = (14, 5.5)
    else:
        figsize = (14, 9)

    fig = plt.figure(figsize=figsize, constrained_layout=True)
    mosaic = fig.subplot_mosaic(build_mosaic(selected_plots))
    title = f"Scraptifine Benchmark: {display_name} Settings Comparison"
    if description:
        title += f" - {description}"
    fig.suptitle(title, fontsize=16)

    colors = list(plt.cm.tab10.colors)

    if "energy" in mosaic:
        ax_energy = mosaic["energy"]
        for idx, settings_name in enumerate(ordered_settings):
            color = colors[idx % len(colors)]
            setting_rows = sorted(grouped_rows[settings_name], key=lambda item: item.thread_count)
            thread_counts = [item.thread_count for item in setting_rows]
            total_energy = [item.total_energy_j for item in setting_rows]
            ax_energy.plot(
                thread_counts,
                total_energy,
                marker="o",
                color=color,
                label=f"{label_map[settings_name]} total energy",
            )
        ax_energy.set_title("Energy Usage")
        ax_energy.set_xlabel("Thread Count")
        ax_energy.set_ylabel("Energy (J)")
        ax_energy.set_xticks(x_ticks)
        ax_energy.grid(True, alpha=0.3)
        ax_energy.legend()

    if "power" in mosaic:
        ax_power = mosaic["power"]
        max_power = 0.0
        for idx, settings_name in enumerate(ordered_settings):
            color = colors[idx % len(colors)]
            setting_rows = sorted(grouped_rows[settings_name], key=lambda item: item.thread_count)
            thread_counts = [item.thread_count for item in setting_rows]
            cpu_power = [item.avg_cpu_power_w for item in setting_rows]
            gpu_power = [item.avg_gpu_power_w for item in setting_rows]
            max_power = max(max_power, *cpu_power, *gpu_power)
            label = label_map[settings_name]
            ax_power.plot(
                thread_counts,
                cpu_power,
                marker="o",
                linestyle="--",
                color=color,
                label=f"{label} CPU power",
            )
            ax_power.plot(
                thread_counts,
                gpu_power,
                marker="o",
                linestyle="-",
                color=color,
                label=f"{label} GPU power",
            )
        ax_power.set_title("Power Usage")
        ax_power.set_xlabel("Thread Count")
        ax_power.set_ylabel("Power (W)")
        ax_power.set_xticks(x_ticks)
        ax_power.set_ylim(bottom=0, top=max_power * 1.12 if max_power > 0 else None)
        ax_power.grid(True, alpha=0.3)
        ax_power.legend()

    if "fps" in mosaic:
        ax_fps = mosaic["fps"]
        for idx, settings_name in enumerate(ordered_settings):
            color = colors[idx % len(colors)]
            setting_rows = sorted(grouped_rows[settings_name], key=lambda item: item.thread_count)
            thread_counts = [item.thread_count for item in setting_rows]
            avg_fps = [item.avg_fps for item in setting_rows]
            low_fps = [item.fps_1pct_low for item in setting_rows]
            label = label_map[settings_name]
            ax_fps.plot(
                thread_counts,
                avg_fps,
                marker="o",
                linestyle="-",
                color=color,
                label=f"{label} average FPS",
            )
            ax_fps.plot(
                thread_counts,
                low_fps,
                marker="o",
                linestyle=":",
                color=color,
                label=f"{label} 1% low FPS",
            )
        ax_fps.set_title("Framerate")
        ax_fps.set_xlabel("Thread Count")
        ax_fps.set_ylabel("FPS")
        ax_fps.set_xticks(x_ticks)
        ax_fps.grid(True, alpha=0.3)
        ax_fps.legend()

    if "usage" in mosaic:
        ax_usage = mosaic["usage"]
        for idx, settings_name in enumerate(ordered_settings):
            color = colors[idx % len(colors)]
            setting_rows = sorted(grouped_rows[settings_name], key=lambda item: item.thread_count)
            thread_counts = [item.thread_count for item in setting_rows]
            cpu_usage = [item.avg_cpu_usage_pct for item in setting_rows]
            gpu_usage = [item.avg_gpu_usage_pct for item in setting_rows]
            label = label_map[settings_name]
            ax_usage.plot(
                thread_counts,
                cpu_usage,
                marker="o",
                linestyle="--",
                color=color,
                label=f"{label} CPU usage",
            )
            ax_usage.plot(
                thread_counts,
                gpu_usage,
                marker="o",
                linestyle="-",
                color=color,
                label=f"{label} GPU usage",
            )
        ax_usage.set_title("CPU and GPU Usage")
        ax_usage.set_xlabel("Thread Count")
        ax_usage.set_ylabel("Usage (%)")
        ax_usage.set_xticks(x_ticks)
        ax_usage.set_ylim(bottom=0)
        ax_usage.grid(True, alpha=0.3)
        ax_usage.legend()

    output_path = output_dir / f"{save_name}_settings_comparison_dashboard.png"
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def main() -> int:
    args = parse_args()
    session_dirs = resolve_session_paths(args.results_root.resolve(), args.session)
    newest_session_dir = max(session_dirs, key=lambda path: path.stat().st_mtime)
    default_output_dirname = DEFAULT_OUTPUT_DIRNAME if len(session_dirs) == 1 else f"{DEFAULT_OUTPUT_DIRNAME}_merged"
    output_dir = args.output_dir.resolve() if args.output_dir else newest_session_dir / default_output_dirname
    output_dir.mkdir(parents=True, exist_ok=True)

    session_metadata = apply_session_metadata_overrides(
        load_session_metadata(newest_session_dir),
        args.description,
        args.save_display_name,
    )
    if len(session_dirs) == 1:
        write_session_metadata(newest_session_dir, session_metadata)

    keep_saves = set(args.save) if args.save else None
    rows = collect_metrics(
        session_dirs=session_dirs,
        keep_saves=keep_saves,
        min_line_ratio=args.min_line_ratio,
        tail_sample_count=args.tail_sample_count,
    )
    if not rows:
        session_list = ", ".join(str(path) for path in session_dirs)
        raise SystemExit(f"No valid benchmark runs were found in {session_list}")

    summary_path = write_summary_csv(output_dir, rows)
    print(f"[info] wrote summary: {summary_path}")

    grouped: dict[tuple[str, str], list[RunMetrics]] = {}
    for row in rows:
        grouped.setdefault((row.save, row.settings_config_name), []).append(row)

    for (save_name, settings_config_name), save_rows in grouped.items():
        display_name = session_metadata.save_display_names.get(save_name, save_name)
        dashboard_path = make_dashboard(
            output_dir=output_dir,
            session_name=newest_session_dir.name,
            save_name=save_name,
            settings_config_name=settings_config_name,
            display_name=display_name,
            description=session_metadata.description,
            rows=save_rows,
            selected_plots=args.plots,
        )
        print(f"[info] wrote dashboard: {dashboard_path}")

    comparison_groups: dict[str, list[RunMetrics]] = {}
    for row in rows:
        comparison_groups.setdefault(row.save, []).append(row)

    for save_name, save_rows in comparison_groups.items():
        settings_names = {item.settings_config_name for item in save_rows}
        if len(settings_names) < 2:
            continue
        display_name = session_metadata.save_display_names.get(save_name, save_name)
        dashboard_path = make_settings_comparison_dashboard(
            output_dir=output_dir,
            save_name=save_name,
            display_name=display_name,
            description=session_metadata.description,
            rows=save_rows,
            selected_plots=args.plots,
        )
        print(f"[info] wrote dashboard: {dashboard_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
