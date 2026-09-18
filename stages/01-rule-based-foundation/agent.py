import subprocess

def greet(name):
    return f"Hello {name}"

def ping_host(host):
    result = subprocess.run(
        ["ping", "-n", "1", host],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        return f"Host {host} is reachable"

    return f"Host {host} is not reachable"


def select_tool():
    keywords = ["ping"]
    greet_keywords = ['greet']
    print("Welcome how can I help you ?")
    user_input = input(f"Just say it!: ")
    parts = user_input.split()
    if len(parts) == 0 or len(parts) == 1:
        return 'Pls Enter SomeThing . . . like google.com'
    
    if parts[0] == keywords[0] and len(parts) == 2:
            ping_result = ping_host(parts[1])
            return ping_result

    if parts[0] == greet_keywords[0] and len(parts) == 2:
        select_result = greet(parts[1])
        return select_result
    else:
        return (f"I can't help u with this order - not in my allowed tools !")


result = select_tool()

print(result)
