import ollama  # Import Ollama so Python can communicate with the local LLM runtime
import json  # Import json so we can load/save structured conversation data
from pathlib import Path  # Import Path so file paths stay relative to this agent folder
from tools import ping_host  # Import the real Python tool from the separate tools module


#-------------------- Paths -----------------------------#
BASE_DIR = Path(__file__).parent  # Get the folder that contains this agent.py file
SYSTEM_PROMPT_PATH = BASE_DIR / "prompts" / "system.md"  # Point to the external system instructions
CHAT_HISTORY_PATH = BASE_DIR / "data" / "chat_history.json"  # Point to the persistent chat history file


#-------------------- Tools -----------------------------#
tools = {  # Create a registry that maps model-selected tool names to real Python functions
    "ping_host": ping_host
}
#-------------------- Tools -----------------------------#


#-------------------- Agent setup -----------------------------#
with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:  # Open the external system prompt
    system_prompt = file.read()  # Read the complete agent instructions into Python

CHAT_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)  # Make sure the local data folder exists

if CHAT_HISTORY_PATH.exists():  # Check whether a local chat history file already exists
    with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as file:  # Open the saved conversation history
        chats_history = json.load(file)  # Convert the JSON history into a Python list
else:
    chats_history = []  # Start with an empty history on the first run

print("Hello I'm IT Agent built by @Baslx0")  # Print a startup message when the program starts
print("How can I help you?")  # Print a simple welcome message for the user


def save_chat_history():  # Save the current in-memory conversation state to disk
    with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as file:  # Open the history file for replacement
        json.dump(chats_history, file, indent=2, ensure_ascii=False)  # Store the list as readable JSON


def Chat_agent(user_input):  # Create a function that sends the user's message to the local model
    user_message = {  # Build the structured user message once
        "role": "user",
        "content": user_input
    }

    chats_history.append(user_message)  # Add the latest user message to persistent conversation state

    messages = [  # Build the full context that will be sent to the model
        {
            "role": "system",
            "content": system_prompt
        }
    ] + chats_history  # Keep system instructions separate, then append conversation history

    response = ollama.chat(  # Send the full conversation to Ollama and wait for Phi-4-mini
        model="phi4-mini",  # Select the local model used as the decision-making brain
        messages=messages,  # Send system instructions + saved conversation history
        format="json"  # Require the model to return valid JSON
    )

    assistant_message = {  # Convert the Ollama response into plain JSON-friendly conversation data
        "role": "assistant",
        "content": response["message"]["content"]
    }

    chats_history.append(assistant_message)  # Save the assistant/model reply in conversation state
    save_chat_history()  # Persist the updated conversation to data/chat_history.json

    return assistant_message  # Return the assistant message to the main controller


while True:  # Keep the agent running until the user explicitly exits
    user_input = input("Ask: ")  # Read a natural-language request from the user

    if user_input == "exit":  # Handle the local exit command before calling the model
        print("Goodbye")  # Print a closing message
        break  # Stop the continuous agent loop

    reply = Chat_agent(user_input)  # Ask the model to classify the request and return a structured decision
    decision = json.loads(reply["content"])  # Convert the model's JSON string into a Python dictionary
    print(reply["content"])  # Print the raw structured model response for learning/debugging

    if decision["tool"] in tools and "host" in decision["arguments"]:  # Validate the registered tool and required argument
        host = decision["arguments"]["host"]  # Extract the host/domain/IP chosen by the model

        print("\n[✓] Decision validated")  # Confirm that the model's tool decision passed validation
        print(f"[→] Tool   : {decision['tool']}")  # Show the selected tool name
        print(f"[→] Target : {host}")  # Show the target that will be passed to the tool
        print("[…] Executing tool...")  # Show that real system execution is about to begin

        selected_tool = tools[decision["tool"]]  # Use the model's tool choice as the registry key
        use_tool = selected_tool(host)  # Execute the retrieved function with the validated host argument

        print(f"[✓] Result : {use_tool}")  # Print the real result returned by the tool
        print("-" * 60)  # Print a separator before the next user request

    elif decision["tool"] is None:  # Handle requests that do not require or match a real tool
        print(decision["message"])  # Print the model's user-facing answer instead of executing anything
