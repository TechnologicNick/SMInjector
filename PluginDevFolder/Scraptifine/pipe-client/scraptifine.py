import argparse
import json
import os
import re

import pywintypes
import win32file
import win32pipe


PIPE_PATTERN = re.compile(r"ScrapMechanic_(\d+)_Scraptifine$")


def list_pipes():
    pipes = {}
    for name in os.listdir(r"\\.\pipe\\"):
        match = PIPE_PATTERN.fullmatch(name)
        if match:
            pipes[int(match.group(1))] = rf"\\.\pipe\{name}"
    return dict(sorted(pipes.items()))


def print_pipes(pipes):
    print("Discovered Scraptifine pipes:")
    if not pipes:
        print("  (none)")
        return

    for pid, pipe_name in pipes.items():
        print(f"  PID {pid}: {pipe_name}")


def resolve_pipe(pipes, pid):
    if not pipes:
        raise SystemExit("No Scraptifine pipes were found.")

    if pid is not None:
        if pid not in pipes:
            raise SystemExit(f"No Scraptifine pipe found for PID {pid}.")
        return pipes[pid]

    if len(pipes) == 1:
        return next(iter(pipes.values()))

    raise SystemExit("Multiple Scraptifine pipes were found. Pass --pid to choose one.")


def send_request(pipe_name, request):
    try:
        handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )
    except pywintypes.error as exc:
        raise SystemExit(f"Failed to connect to {pipe_name}: {exc}") from exc

    try:
        win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
        payload = json.dumps(request).encode("utf-8")
        win32file.WriteFile(handle, payload)
        _, response = win32file.ReadFile(handle, 4096)
    finally:
        win32file.CloseHandle(handle)

    return json.loads(response.decode("utf-8"))


def print_status(response):
    print(f"Pipe: {response['pipe_name']}")
    print(f"Override worker count: {response['override_worker_count']}")
    print(f"Observed backends: {response['observed_backend_count']}")
    for backend in response["backends"]:
        print(
            "  "
            f"{backend['address']} "
            f"(first_seen={backend['first_seen_order']}, "
            f"last_game_requested={backend['last_game_requested']}, "
            f"last_applied={backend['last_applied']})"
        )


def main():
    parser = argparse.ArgumentParser(description="Scraptifine named pipe client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List all Scraptifine pipes")
    list_parser.set_defaults(requires_pipe=False)

    status_parser = subparsers.add_parser("status", help="Show current Scraptifine status")
    status_parser.add_argument("--pid", type=int)
    status_parser.set_defaults(requires_pipe=True)

    set_parser = subparsers.add_parser("set", help="Override the worker count")
    set_parser.add_argument("count", type=int)
    set_parser.add_argument("--pid", type=int)
    set_parser.set_defaults(requires_pipe=True)

    clear_parser = subparsers.add_parser("clear", help="Clear the worker-count override")
    clear_parser.add_argument("--pid", type=int)
    clear_parser.set_defaults(requires_pipe=True)

    args = parser.parse_args()

    pipes = list_pipes()
    print_pipes(pipes)

    if not args.requires_pipe:
        return

    pipe_name = resolve_pipe(pipes, getattr(args, "pid", None))

    if args.command == "status":
        response = send_request(pipe_name, {"cmd": "status"})
    elif args.command == "set":
        response = send_request(pipe_name, {"cmd": "set_worker_count", "value": args.count})
    else:
        response = send_request(pipe_name, {"cmd": "clear_override"})

    if not response.get("ok", False):
        raise SystemExit(f"Request failed: {response.get('error')}")

    print_status(response)


if __name__ == "__main__":
    main()
