"""Checkpoint: manual menu-based tool routing."""

import subprocess


def greet(name):
    return f"Hello {name}"


def ping_host(host):
    result = subprocess.run(
        ["ping", "-n", "1", host],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return f"Host {host} is reachable"

    return f"Host {host} is not reachable"


def select_tool():
    print("Tools: 1.ping 2.greet ")
    user_input = input("Select tool: ")

    if user_input == "1":
        return ping_host(input("Enter hostname: "))

    elif user_input == "2":
        return greet(input("Enter username: "))

    return f"Please select from the listed tools: {user_input}"


result = select_tool()
print(result)
