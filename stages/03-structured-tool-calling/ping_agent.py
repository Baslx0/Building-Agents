import ollama  # Import Ollama so Python can communicate with the local LLM runtime
import subprocess  # Import subprocess so Python can execute the real Windows ping command
import json  # Import json so we can convert the model's JSON text into a Python dictionary

#-------------------- Tools -----------------------------#
#1- ping_host Tool:

def ping_host(host):  # Create a tool function that receives a host/domain/IP to ping
    result = subprocess.run(  # Execute the Windows ping command and store the process result
        ["ping", "-n", "1", host],  # Send one ping request to the selected host
        capture_output=True,  # Capture stdout/stderr instead of printing command output directly
        text=True  # Return captured output as normal Python strings
    )

    if result.returncode == 0:  # A return code of 0 means the ping command completed successfully
        return f"Host {host} is reachable"  # Return a readable success result to the controller

    return f"Host {host} is not reachable"  # Return a readable failure result if ping was unsuccessful


#-------------------- Agent work start here -----------------------------#

print("Hello I'm IT Agent built by @Baslx0")  # Print a startup message when the program starts
print("How can I help you?")  # Print a simple welcome message for the user

chats_history = [  # Create the conversation history that will be sent to the model
    {
        "role": "system",  # Define this first message as instructions for the model
        "content": """
    You are an IT agent.

    Your job is to understand the user's request and return a structured decision.

    If the user wants to check whether a host or domain is reachable, use this format:

    {
    "tool": "ping_host",
    "arguments": {
        "host": "example.com"
    }
    }

    Return JSON only.
    Do not add explanations before or after the JSON.
    """
    }
]


def Chat_agent(user_input):  # Create a function that sends a user request to the local LLM
    chats_history.append({  # Save the user's new message in the conversation history
        "role": "user",  # Mark the message as coming from the user
        "content": user_input  # Store the actual text entered by the user
    })

    response = ollama.chat(  # Send the full conversation to Ollama and wait for Phi-4-mini
        model="phi4-mini",  # Select the local model used as the decision-making brain
        messages=chats_history,  # Give the model the complete conversation history
        format="json"  # Require the model response to be valid JSON
    )

    chats_history.append(response["message"])  # Save the assistant/model response in the history

    return response["message"]  # Return only the model's message to the main controller


while True:  # Keep the agent running until the user explicitly exits
    user_input = input("Ask: ")  # Read a natural-language request from the user

    if user_input == "exit":  # Check for the local exit command before calling the model
        print("Goodbye")  # Print a closing message
        break  # Stop the continuous agent loop

    reply = Chat_agent(user_input)  # Ask the LLM to convert the user's request into a structured decision
    decision = json.loads(reply["content"])  # Convert the JSON string returned by the model into a Python dictionary

    if decision["tool"] == "ping_host" and "host" in decision["arguments"]:  # Validate the allowed tool and required argument
        host = decision["arguments"]["host"]  # Extract the host selected by the model

        print("\n[✓] Decision validated")  # Confirm that the structured decision passed the current validation
        print(f"[→] Tool   : {decision['tool']}")  # Show which tool the LLM selected
        print(f"[→] Target : {host}")  # Show the host/domain/IP that will be passed to the tool
        print("[…] Executing tool...")  # Show that real tool execution is about to begin

        use_tool = ping_host(host)  # Execute the approved Python tool with the validated argument

        print(f"[✓] Result : {use_tool}")  # Print the real result returned by the tool
        print("-" * 60)  # Print a separator before the next user request
    else:  # Handle decisions that do not match the currently supported tool contract
        print("\nwallahy shooof . . .")  # Keep a small personal touch in the learning project
        print("[!] Unsupported or invalid tool request")  # Print the technical reason for rejection
