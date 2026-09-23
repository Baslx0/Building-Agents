import ollama  # Import the Ollama Python library so we can communicate with the local LLM runtime

print("Hello I'm IT Agent built by @Baslx0")  # Print a startup message when the program starts
print("How can I help you?")  # Print a simple welcome message for the user

chats_history = [  # Create a list that will store the conversation history
    {
        "role": "system",  # This message contains the main instructions for the LLM
        "content": "You are a simple IT assistant. Answer in one short sentence."  # Define how the LLM should behave
    }
]


def Chat_agent(user_input):  # Create a function that receives the user's message
    chats_history.append({  # Add a new message to the conversation history
        "role": "user",  # Tell the model that this message came from the user
        "content": user_input  # Store the actual text that the user entered
    })

    response = ollama.chat(  # Send the conversation to Ollama and wait for the model's response
        model="phi4-mini",  # Choose the local model that Ollama should use
        messages=chats_history  # Send the entire conversation history to the model
    )

    chats_history.append(response["message"])  # Save the assistant's response inside the conversation history

    return response["message"]  # Return the assistant's message back to the code that called this function


while True:
    user_input = input("Ask: ")

    if user_input == "exit":
        print("Goodbye")
        break

    reply = Chat_agent(user_input)

    print(f'{reply["content"]}\n')
    print("---------------------------------------------------------------------------------------------")
    print(f"This is the chat history {chats_history}")
    print("---------------------------------------------------------------------------------------------")
