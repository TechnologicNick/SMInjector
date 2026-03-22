import win32pipe, win32file, pywintypes
import os
import re

def list_pipes():
    pipes = dict()

    for file in os.listdir("\\\\.\\pipe\\"):
        pid = re.search(r"ScrapMechanic_(\d+)_ConnectByIP", file)
        if pid:
            pipes[int(pid.group(1))] = "\\\\.\\pipe\\" + file

    return pipes

for pid, pipe in list_pipes().items():
    try:
        handle = win32file.CreateFile(
            pipe,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)

        win32file.WriteFile(handle, b"ip://127.0.0.1:38799")

    except pywintypes.error as e:
        print(e)
