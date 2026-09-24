import subprocess  # Import subprocess so this module can execute Windows system commands

#-------------------- ping_host Tool --------------------#

def ping_host(host):  # Create a tool that checks whether a host/domain/IP is reachable
    result = subprocess.run(  # Execute the Windows ping command and store the process result
        ["ping", "-n", "1", host],  # Send one ping request to the provided target
        capture_output=True,  # Capture stdout/stderr instead of printing command output directly
        text=True  # Return captured output as normal Python strings
    )

    if result.returncode == 0:  # A return code of 0 means the ping command succeeded
        return f"Host {host} is reachable"  # Return a simple success result to the agent controller

    return f"Host {host} is not reachable"  # Return a simple failure result when the host cannot be reached

#-------------------- ping_host Tool --------------------#
