from __future__ import annotations

import argparse
import csv
import ctypes
import json
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_INJECTOR = REPO_ROOT / "SMInjector" / "x64" / "Debug" / "SMInjector.exe"
DEFAULT_RESULTS_ROOT = SCRIPT_DIR / "benchmark_results"
BENCHMARK_SAVES_DIR = SCRIPT_DIR / "benchmark_saves"
DEFAULT_THREAD_COUNTS = (1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 24, 32)
DEFAULT_SETTINGS_CONFIG = SCRIPT_DIR / "settings_uncapped_2160p.json"
SETTINGS_PATH = Path(
    r"C:\Users\Nick\AppData\Roaming\Axolot Games\Scrap Mechanic\User\User_76561198142527219\settings.json"
)
AFTERBURNER_LOG_PATH = SCRIPT_DIR / "afterburner" / "HardwareMonitoring.hml"
GAME_LOG_DIR = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Scrap Mechanic\Logs"
)

WM_CLOSE = 0x0010
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INPUT_KEYBOARD = 1
MAPVK_VK_TO_VSC = 0
ULONG_PTR = (
    ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
)

@dataclass(frozen=True)
class SaveSpec:
    name: str
    bundled_path: Path


@dataclass(frozen=True)
class SettingsSpec:
    name: str
    path: Path
    payload: dict[str, object]
    snapshot_path: Path


class EmptyCaptureError(RuntimeError):
    pass


SAVE_SPECS = {
    "creative_flat": SaveSpec(
        "creative_flat", BENCHMARK_SAVES_DIR / "BenchmarkCreativeFlat.db"
    ),
    "creative_terrain": SaveSpec(
        "creative_terrain", BENCHMARK_SAVES_DIR / "BenchmarkCreativeTerrain.db"
    ),
    "survival": SaveSpec("survival", BENCHMARK_SAVES_DIR / "BenchmarkSurvival.db"),
}

DEFAULT_SAVE_DISPLAY_NAMES = {
    "creative_flat": "Creative Flat",
    "creative_terrain": "Creative Terrain",
    "survival": "Survival",
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
user32.SendInput.argtypes = (ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int)
user32.SendInput.restype = ctypes.c_uint
user32.MapVirtualKeyW.argtypes = (ctypes.c_uint, ctypes.c_uint)
user32.MapVirtualKeyW.restype = ctypes.c_uint
kernel32.GetLastError.argtypes = ()
kernel32.GetLastError.restype = ctypes.c_ulong


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Scrap Mechanic benchmark sweeps with MSI Afterburner capture."
    )
    parser.add_argument("--injector", type=Path, default=DEFAULT_INJECTOR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--load-seconds", type=float, default=30.0)
    parser.add_argument("--measure-seconds", type=float, default=30.0)
    parser.add_argument(
        "--threads",
        type=int,
        nargs="+",
        default=list(DEFAULT_THREAD_COUNTS),
        help="Thread counts to benchmark. Defaults to 1 2 3 4 5 6 7 8 12 16 24 32.",
    )
    parser.add_argument(
        "--save",
        action="append",
        choices=sorted(SAVE_SPECS.keys()),
        help="Benchmark only the specified save. Repeat to benchmark multiple saves.",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Session description used in graph titles, for example '2160p'.",
    )
    parser.add_argument(
        "--settings-config",
        type=Path,
        action="append",
        help="Settings preset JSON to apply before each benchmark run. Repeat to benchmark multiple presets in one session.",
    )
    parser.add_argument(
        "--save-display-name",
        action="append",
        nargs=2,
        metavar=("SAVE", "LABEL"),
        help="Override the display name for a save, for example --save-display-name creative_flat 'Creative Flat'.",
    )
    parser.add_argument(
        "--max-empty-capture-retries",
        type=int,
        default=2,
        help="How many times to retry a run when HardwareMonitoring.hml contains no 80 sample rows.",
    )
    return parser.parse_args()


def normalize_save_display_names(overrides: list[list[str]] | None) -> dict[str, str]:
    display_names = dict(DEFAULT_SAVE_DISPLAY_NAMES)
    if not overrides:
        return display_names

    for save_name, label in overrides:
        if save_name not in SAVE_SPECS:
            raise ValueError(f"Unknown save for --save-display-name: {save_name}")
        display_names[save_name] = label
    return display_names


def resolve_settings_config_path(settings_config: Path) -> Path:
    if settings_config.exists():
        return settings_config.resolve()

    candidate = (SCRIPT_DIR / settings_config).resolve()
    if candidate.exists():
        return candidate

    raise FileNotFoundError(f"Settings config not found: {settings_config}")


def resolve_settings_config_paths(
    settings_configs: list[Path] | None,
) -> list[Path]:
    requested = settings_configs or [DEFAULT_SETTINGS_CONFIG]
    resolved = [resolve_settings_config_path(path) for path in requested]
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in resolved:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def load_settings_payload(settings_config_path: Path) -> dict[str, object]:
    payload = json.loads(settings_config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Settings config must contain a JSON object: {settings_config_path}")
    return payload


def write_settings_snapshot(snapshot_path: Path, settings_payload: dict[str, object]) -> Path:
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(settings_payload, indent=4) + "\n", encoding="utf-8")
    return snapshot_path


def create_settings_specs(
    output_root: Path, settings_config_paths: list[Path]
) -> list[SettingsSpec]:
    settings_specs: list[SettingsSpec] = []
    seen_names: set[str] = set()

    for settings_config_path in settings_config_paths:
        name = settings_config_path.stem
        if name in seen_names:
            raise ValueError(f"Duplicate settings config name: {name}")
        seen_names.add(name)

        payload = load_settings_payload(settings_config_path)
        if len(settings_config_paths) == 1:
            snapshot_path = write_settings_snapshot(output_root / "settings.json", payload)
        else:
            snapshot_path = write_settings_snapshot(output_root / "settings" / f"{name}.json", payload)
        settings_specs.append(
            SettingsSpec(
                name=name,
                path=settings_config_path,
                payload=payload,
                snapshot_path=snapshot_path,
            )
        )

    return settings_specs


def write_session_metadata(
    output_root: Path,
    description: str,
    save_display_names: dict[str, str],
    settings_specs: list[SettingsSpec],
) -> None:
    settings_configs = [
        {
            "name": item.name,
            "path": str(item.path),
            "snapshot_path": str(item.snapshot_path),
        }
        for item in settings_specs
    ]
    metadata = {
        "description": description,
        "save_display_names": save_display_names,
        "settings_configs": settings_configs,
    }
    if len(settings_specs) == 1:
        metadata["settings_config_name"] = settings_specs[0].name
        metadata["settings_config_path"] = str(settings_specs[0].path)
        metadata["settings_snapshot_path"] = str(settings_specs[0].snapshot_path)
    (output_root / "metadata.json").write_text(
        json.dumps(metadata, indent=4) + "\n",
        encoding="utf-8",
    )


def write_settings(settings_payload: dict[str, object]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(settings_payload, indent=4) + "\n", encoding="utf-8"
    )


def count_hml_sample_rows(hml_path: Path) -> int:
    with hml_path.open("r", encoding="cp1251", errors="replace", newline="") as handle:
        rows = csv.reader(handle)
        return sum(1 for row in rows if row and row[0].strip() == "80")


def cleanup_attempt_artifacts(run_dir: Path) -> None:
    for path in run_dir.iterdir():
        if path.name in {"metadata.json", "HardwareMonitoring.hml"}:
            path.unlink(missing_ok=True)
            continue
        if path.is_file() and path.name.startswith("game-") and path.suffix == ".log":
            path.unlink(missing_ok=True)


def list_scrap_mechanic_pids() -> set[int]:
    completed = subprocess.run(
        ["tasklist", "/fo", "csv", "/nh", "/fi", "IMAGENAME eq ScrapMechanic.exe"],
        capture_output=True,
        text=True,
        check=True,
    )

    pids: set[int] = set()
    for row in csv.reader(
        line for line in completed.stdout.splitlines() if line.strip()
    ):
        if not row or row[0] != "ScrapMechanic.exe":
            continue
        try:
            pids.add(int(row[1]))
        except ValueError:
            continue
    return pids


def wait_for_new_game_pid(existing_pids: set[int], timeout_seconds: float) -> int:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        current_pids = list_scrap_mechanic_pids()
        new_pids = current_pids - existing_pids
        if len(new_pids) == 1:
            return next(iter(new_pids))
        if len(new_pids) > 1:
            raise RuntimeError(
                f"Expected exactly one new ScrapMechanic.exe process, found {sorted(new_pids)}"
            )
        time.sleep(0.5)
    raise TimeoutError("Timed out waiting for Scrap Mechanic to launch")


def process_is_running(pid: int) -> bool:
    handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    try:
        return kernel32.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
    finally:
        kernel32.CloseHandle(handle)


def wait_for_process_exit(pid: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not process_is_running(pid):
            return True
        time.sleep(0.5)
    return not process_is_running(pid)


def send_numpad_key(vk_code: int) -> None:
    scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    if scan_code == 0:
        raise RuntimeError(f"MapVirtualKeyW failed for virtual key 0x{vk_code:02X}")

    key_down = INPUT()
    key_down.type = INPUT_KEYBOARD
    key_down.ki = KEYBDINPUT(0, scan_code, KEYEVENTF_SCANCODE, 0, 0)

    key_up = INPUT()
    key_up.type = INPUT_KEYBOARD
    key_up.ki = KEYBDINPUT(0, scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, 0)

    for input_event in (key_down, key_up):
        ctypes.set_last_error(0)
        sent = user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))
        if sent != 1:
            error = ctypes.get_last_error() or kernel32.GetLastError()
            raise RuntimeError(
                f"SendInput failed for virtual key 0x{vk_code:02X} (sent={sent}, error={error})"
            )
        if input_event is key_down:
            time.sleep(0.1)


def enum_process_windows(pid: int) -> list[int]:
    hwnds: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def callback(hwnd: int, lparam: int) -> bool:
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(window_pid))
        if window_pid.value == pid and user32.IsWindow(hwnd):
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return hwnds


def close_game_process(pid: int) -> None:
    for hwnd in enum_process_windows(pid):
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    if wait_for_process_exit(pid, 15.0):
        return

    subprocess.run(
        ["taskkill", "/pid", str(pid), "/t", "/f"],
        check=True,
        capture_output=True,
        text=True,
    )
    if not wait_for_process_exit(pid, 15.0):
        raise RuntimeError(
            f"Timed out waiting for Scrap Mechanic process {pid} to exit"
        )


def newest_game_log() -> Path | None:
    logs = sorted(
        (path for path in GAME_LOG_DIR.glob("game-*") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return logs[0] if logs else None


def wait_for_afterburner_log_update(
    previous_mtime: float | None, timeout_seconds: float
) -> Path:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if AFTERBURNER_LOG_PATH.exists():
            current_mtime = AFTERBURNER_LOG_PATH.stat().st_mtime
            if previous_mtime is None or current_mtime > previous_mtime:
                return AFTERBURNER_LOG_PATH
        time.sleep(0.5)
    raise TimeoutError(
        "MSI Afterburner did not update HardwareMonitoring.hml after the measurement run"
    )


def launch_game(
    injector_path: Path, thread_count: int, save_copy_path: Path
) -> subprocess.Popen[str]:
    command = [
        str(injector_path),
        "-skip-initial-message-box",
        "-threads",
        str(thread_count),
        "-open",
        str(save_copy_path),
    ]
    return subprocess.Popen(command)


def selected_saves(save_names: list[str] | None) -> Iterable[SaveSpec]:
    if save_names:
        return [SAVE_SPECS[name] for name in save_names]
    return SAVE_SPECS.values()


def validate_environment(args: argparse.Namespace, settings_config_paths: list[Path]) -> None:
    if not args.threads:
        raise ValueError("At least one thread count must be provided")

    invalid_thread_counts = [
        thread_count
        for thread_count in args.threads
        if thread_count < 1 or thread_count > 32
    ]
    if invalid_thread_counts:
        raise ValueError(
            f"Thread counts must stay within 1..32, got {invalid_thread_counts}"
        )

    if args.max_empty_capture_retries < 0:
        raise ValueError("--max-empty-capture-retries must be >= 0")

    if not args.injector.exists():
        raise FileNotFoundError(f"Injector not found: {args.injector}")

    if not settings_config_paths:
        raise ValueError("At least one settings config must be provided")

    for settings_config_path in settings_config_paths:
        if not settings_config_path.exists():
            raise FileNotFoundError(f"Settings config not found: {settings_config_path}")

    if not BENCHMARK_SAVES_DIR.exists():
        raise FileNotFoundError(
            f"Bundled benchmark saves directory not found: {BENCHMARK_SAVES_DIR}"
        )

    for spec in SAVE_SPECS.values():
        if not spec.bundled_path.exists():
            raise FileNotFoundError(f"Bundled save not found: {spec.bundled_path}")

    if not GAME_LOG_DIR.exists():
        raise FileNotFoundError(f"Game log directory not found: {GAME_LOG_DIR}")

    if not AFTERBURNER_LOG_PATH.parent.exists():
        raise FileNotFoundError(
            f"MSI Afterburner directory not found: {AFTERBURNER_LOG_PATH.parent}"
        )


def run_single_benchmark(
    injector_path: Path,
    output_root: Path,
    save_spec: SaveSpec,
    thread_count: int,
    load_seconds: float,
    measure_seconds: float,
    settings_spec: SettingsSpec,
    max_empty_capture_retries: int,
) -> None:
    run_name = f"{save_spec.name}_{settings_spec.name}_threads_{thread_count:02d}"
    run_dir = output_root / run_name
    run_dir.mkdir(parents=True, exist_ok=False)

    save_copy_path = run_dir / save_spec.bundled_path.name
    shutil.copy2(save_spec.bundled_path, save_copy_path)

    max_attempts = max_empty_capture_retries + 1
    for attempt in range(1, max_attempts + 1):
        write_settings(settings_spec.payload)
        cleanup_attempt_artifacts(run_dir)

        before_pids = list_scrap_mechanic_pids()
        previous_game_log = newest_game_log()
        previous_game_log_mtime = (
            previous_game_log.stat().st_mtime if previous_game_log else None
        )

        if AFTERBURNER_LOG_PATH.exists():
            AFTERBURNER_LOG_PATH.unlink()

        print(f"[run] launching {run_name} (attempt {attempt}/{max_attempts})")
        injector_process = launch_game(injector_path, thread_count, save_copy_path)

        try:
            game_pid = wait_for_new_game_pid(before_pids, 120.0)
            injector_process.wait(timeout=30.0)

            print(f"[run] game pid {game_pid}, waiting {load_seconds:.0f}s for load")
            time.sleep(load_seconds)

            print("[run] starting MSI Afterburner capture")
            send_numpad_key(VK_NUMPAD1)

            print(f"[run] measuring for {measure_seconds:.0f}s")
            time.sleep(measure_seconds)

            print("[run] stopping MSI Afterburner capture")
            send_numpad_key(VK_NUMPAD2)

            print("[run] closing game")
            close_game_process(game_pid)

            afterburner_log = wait_for_afterburner_log_update(None, 15.0)
            archived_hml = run_dir / "HardwareMonitoring.hml"
            shutil.move(str(afterburner_log), archived_hml)

            sample_row_count = count_hml_sample_rows(archived_hml)
            if sample_row_count == 0:
                raise EmptyCaptureError(
                    f"{archived_hml}: contains no 80 sample rows"
                )

            latest_game_log = newest_game_log()
            if latest_game_log is None:
                raise RuntimeError("No Scrap Mechanic game log was found after the run")
            if (
                previous_game_log_mtime is not None
                and latest_game_log.stat().st_mtime <= previous_game_log_mtime
            ):
                raise RuntimeError(
                    "Did not find a newer Scrap Mechanic game log for the completed run"
                )

            archived_game_log = run_dir / latest_game_log.name
            shutil.copy2(latest_game_log, archived_game_log)

            metadata = {
                "save": save_spec.name,
                "thread_count": thread_count,
                "load_seconds": load_seconds,
                "measure_seconds": measure_seconds,
                "save_copy_path": str(save_copy_path),
                "archived_afterburner_log": str(archived_hml),
                "archived_game_log": str(archived_game_log),
                "settings_path": str(SETTINGS_PATH),
                "settings_config_name": settings_spec.name,
                "settings_config_path": str(settings_spec.path),
                "settings_snapshot_path": str(settings_spec.snapshot_path),
                "capture_attempts": attempt,
                "sample_row_count": sample_row_count,
            }
            (run_dir / "metadata.json").write_text(
                json.dumps(metadata, indent=4) + "\n", encoding="utf-8"
            )

            print(f"[run] completed {run_name}")
            return
        except Exception as exc:
            if injector_process.poll() is None:
                injector_process.kill()
                injector_process.wait()
            current_pids = list_scrap_mechanic_pids()
            new_pids = current_pids - before_pids
            for pid in sorted(new_pids):
                try:
                    close_game_process(pid)
                except Exception:
                    pass

            if isinstance(exc, EmptyCaptureError) and attempt < max_attempts:
                print(
                    f"[warn] {run_name} produced an empty capture, retrying ({attempt}/{max_attempts})",
                    file=sys.stderr,
                )
                continue

            raise


def main() -> int:
    args = parse_args()
    settings_config_paths = resolve_settings_config_paths(args.settings_config)
    validate_environment(args, settings_config_paths)
    save_display_names = normalize_save_display_names(args.save_display_name)

    output_root = args.output_root / time.strftime("%Y%m%d-%H%M%S")
    output_root.mkdir(parents=True, exist_ok=False)
    settings_specs = create_settings_specs(output_root, settings_config_paths)
    write_session_metadata(
        output_root=output_root,
        description=args.description,
        save_display_names=save_display_names,
        settings_specs=settings_specs,
    )

    print(f"[info] results root: {output_root}")
    print(f"[info] injector: {args.injector}")

    for settings_spec in settings_specs:
        for save_spec in selected_saves(args.save):
            for thread_count in args.threads:
                run_single_benchmark(
                    injector_path=args.injector,
                    output_root=output_root,
                    save_spec=save_spec,
                    thread_count=thread_count,
                    load_seconds=args.load_seconds,
                    measure_seconds=args.measure_seconds,
                    settings_spec=settings_spec,
                    max_empty_capture_retries=args.max_empty_capture_retries,
                )

    print("[done] all benchmark runs completed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[error] interrupted by user", file=sys.stderr)
        raise SystemExit(130)
