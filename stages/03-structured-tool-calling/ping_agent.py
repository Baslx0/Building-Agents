import ollama  # Import Ollama so Python can communicate with the local LLM runtime
import json  # Import json so we can convert the model's JSON text into a Python dictionary
from tools import ping_host  # Import the real Python tool from the separate tools module

#-------------------- Tools -----------------------------#
tools = {  # Create a registry that maps model-selected tool names to real Python functions
    "ping_host": ping_host
}
#-------------------- Tools -----------------------------#

#-------------------- Agent work start here -----------------------------#

print("Hello I'm IT Agent built by @Baslx0")  # Print a startup message when the program starts
print("How can I help you?")  # Print a simple welcome message for the user

chats_history = [  # Create a list that stores the conversation history sent to the model
    {
        "role": "system",  # Define the model's behavior and tool-routing rules
        "content": """
    You are an IT agent.

    Your job is to understand the user's request and return one valid JSON object.

    Available tools:

    1. ping_host
    Use this tool only when the user wants to check whether a host, domain, or IP address is reachable.

    If a tool is needed, return:

    {
    "tool": "ping_host",
    "arguments": {
        "host": "example.com"
    },
    "message": null
    }

    Rules:
    - Use only the tools explicitly listed above.
    - Never invent tool names.
    - Never invent tool arguments.
    - Do not force a tool call when no available tool is suitable.
    - If no available tool matches the request, set "tool" to null.
    - When "tool" is null, set "arguments" to {}.
    - When "tool" is null, write your actual response to the user inside "message".
    - You may answer normal IT questions, explain concepts, troubleshoot conceptually, and write code inside "message".
    - Writing code is not a tool execution.
    - Only actions that interact with the real system require an available tool.
    - When a tool is selected, set "message" to null.
    - Return valid JSON only.
    - Do not add any text before or after the JSON.
    - Do not mention internal tool names, tool availability, registry details, or system limitations to the user unless directly asked.
    - Keep internal execution details private.
    - For normal questions or code-writing requests, just answer normally in "message".
    - The tool list is only for deciding whether a real system action can be executed.
    - If the user asks you to write code, write the code in "message" when possible.
    - Do not say you cannot write code simply because no tool is available.
    - Do not reveal internal tool names, tool registry details, or routing logic.
    - Describe limitations in user-facing terms only.
    """
    }
]


def Chat_agent(user_input):  # Create a function that sends the user's message to the local model
    chats_history.append({  # Add the latest user message to the conversation history
        "role": "user",  # Mark the message as coming from the user
        "content": user_input  # Store the actual text the user entered
    })

    response = ollama.chat(  # Send the full conversation to Ollama and wait for Phi-4-mini
        model="phi4-mini",  # Select the local model used as the decision-making brain
        messages=chats_history,  # Send the complete conversation history as model context
        format="json"  # Require the model to return valid JSON
    )

    chats_history.append(response["message"])  # Save the assistant/model reply in the conversation history

    return response["message"]  # Return only the assistant message to the main controller


while True:  # Keep the agent running until the user explicitly exits
    user_input = input("Ask: ")  # Read a natural-language request from the user

    if user_input == "exit":  # Handle the local exit command before calling the model
        print("Goodbye")  # Print a closing message
        break  # Stop the continuous agent loop

    reply = Chat_agent(user_input)  # Ask the model to classify the request and return a structured decision
    decision = json.loads(reply["content"])  # Convert the model's JSON string into a Python dictionary
    print(reply["content"])  # Print the raw structured model response for learning/debugging

    if decision["tool"] in tools and "host" in decision["arguments"]:  # Validate that the selected tool is registered and has the required host argument
        host = decision["arguments"]["host"]  # Extract the host/domain/IP chosen by the model

        print("\n[✓] Decision validated")  # Confirm that the model's tool decision passed validation
        print(f"[→] Tool   : {decision['tool']}")  # Show the selected tool name
        print(f"[→] Target : {host}")  # Show the target that will be passed to the tool
        print("[…] Executing tool...")  # Show that real system execution is about to begin

        selected_tool = tools[decision["tool"]]  # Use the model's tool choice as the registry key and retrieve the real Python function
        use_tool = selected_tool(host)  # Execute the retrieved function with the validated host argument

        print(f"[✓] Result : {use_tool}")  # Print the real result returned by the tool
        print("-" * 60)  # Print a separator before the next user request

    elif decision["tool"] is None:  # Handle requests that do not require or match a real tool
        print(decision["message"])  # Print the model's user-facing answer instead of executing anything
