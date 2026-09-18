"""Checkpoint: first real IT tool."""

import subprocess


def ping_host(host):
    result = subprocess.run(
        ["ping", "-n", "1", host],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return f"Host {host} is reachable"

    return f"Host {host} is not reachable"


result = ping_host("google.com")
print(result)
