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

SETTINGS_TEMPLATE = {
    "AmbientVolume": 0.0,
    "Bloom": 1,
    "Brightness": 0.0,
    "CameraShake": 1,
    "DOF": 1,
    "DevConsole": 0,
    "DisplayMode": 3,
    "DrawDistance": 4,
    "DynamicLights": 1,
    "EffectVolume": 0.8000000119209290,
    "FOV": 9,
    "FXAA": 1,
    "Foliage": 4,
    "FrameRateCap": 10000.0,
    "GUIVolume": 0.8000000119209290,
    "Godrays": 1,
    "GraphicsSettingVersion": "32187_32_1",
    "Height": 2160,
    "InvYAxisState": 0,
    "Language": "English",
    "MasterVolume": 1.0,
    "MouseSpeed": 0.3199999928474426,
    "MusicVolume": 0.0,
    "ParticleQuality": 3,
    "ReflectionQuality": 3,
    "SSAO": 3,
    "ShaderQuality": 3,
    "ShadowQuality": 3,
    "ShadowResolution": 3,
    "TextureFiltering": 4,
    "TextureQuality": 2,
    "VehicleCameraMode": 1,
    "VerticalSync": 0,
    "Width": 3840,
}


@dataclass(frozen=True)
class SaveSpec:
    name: str
    bundled_path: Path


SAVE_SPECS = {
    "creative_flat": SaveSpec(
        "creative_flat", BENCHMARK_SAVES_DIR / "BenchmarkCreativeFlat.db"
    ),
    "creative_terrain": SaveSpec(
        "creative_terrain", BENCHMARK_SAVES_DIR / "BenchmarkCreativeTerrain.db"
    ),
    "survival": SaveSpec("survival", BENCHMARK_SAVES_DIR / "BenchmarkSurvival.db"),
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
    return parser.parse_args()


def write_settings() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps(SETTINGS_TEMPLATE, indent=4) + "\n", encoding="utf-8"
    )


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


def validate_environment(args: argparse.Namespace) -> None:
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

    if not args.injector.exists():
        raise FileNotFoundError(f"Injector not found: {args.injector}")

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
) -> None:
    run_name = f"{save_spec.name}_threads_{thread_count:02d}"
    run_dir = output_root / run_name
    run_dir.mkdir(parents=True, exist_ok=False)

    save_copy_path = run_dir / save_spec.bundled_path.name
    shutil.copy2(save_spec.bundled_path, save_copy_path)

    write_settings()

    before_pids = list_scrap_mechanic_pids()
    previous_game_log = newest_game_log()
    previous_game_log_mtime = (
        previous_game_log.stat().st_mtime if previous_game_log else None
    )

    if AFTERBURNER_LOG_PATH.exists():
        AFTERBURNER_LOG_PATH.unlink()

    print(f"[run] launching {run_name}")
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
        }
        (run_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=4) + "\n", encoding="utf-8"
        )

        print(f"[run] completed {run_name}")
    except Exception:
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
        raise


def main() -> int:
    args = parse_args()
    validate_environment(args)

    output_root = args.output_root / time.strftime("%Y%m%d-%H%M%S")
    output_root.mkdir(parents=True, exist_ok=False)

    print(f"[info] results root: {output_root}")
    print(f"[info] injector: {args.injector}")

    for save_spec in selected_saves(args.save):
        for thread_count in args.threads:
            run_single_benchmark(
                injector_path=args.injector,
                output_root=output_root,
                save_spec=save_spec,
                thread_count=thread_count,
                load_seconds=args.load_seconds,
                measure_seconds=args.measure_seconds,
            )

    print("[done] all benchmark runs completed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[error] interrupted by user", file=sys.stderr)
        raise SystemExit(130)
