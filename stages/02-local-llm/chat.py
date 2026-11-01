import ollama  # Import the Ollama Python library so we can communicate with the local LLM runtime
import re  # Use regular expressions to keep only the first sentence of the reply

print("Hello I'm IT Agent built by @Baslx0")  # Print a startup message when the program starts
print("How can I help you?")  # Print a simple welcome message for the user

# Start the conversation with instructions that are included in every model request.
chats_history = [  # Create a list that will store the conversation history
    {
        "role": "system",  # This message contains the main instructions for the LLM
        "content": "You are a simple IT assistant. Answer in one short sentence."  # Define how the LLM should behave
    }
]

def Chat_agent(user_input):  # Receive a message, ask the model, and return its reply
    # Save the user's message so the model can use the full conversation as context.
    chats_history.append({
        "role": "user",  # Tell the model that this message came from the user
        "content": user_input  # Store the actual text that the user entered
    })

    # Send the conversation history to the local model and cap its generated tokens.
    response = ollama.chat(
        model="phi4-mini",  # Choose the local model that Ollama should use
        messages=chats_history,  # Include previous messages for conversational context
        options={"num_predict": 70}  # Limit the length of the generated response
    )

    # Remove surrounding whitespace, keep the first sentence, and cap its character count.
    answer = response["message"]["content"].strip()
    answer = re.split(r"(?<=[.!?])\s+|\n", answer, maxsplit=1)[0]
    answer = answer[:180]

    # Store the assistant's concise reply so it is available in the next model request.
    chats_history.append({
        "role": "assistant",
        "content": answer
    })

    # Return the reply in a dictionary for the calling code to print.
    return {"content": answer}


# Keep prompting until the user enters the exit command.
while True:
    user_input = input("Ask: ")

    # Stop the chat loop without sending the exit command to the model.
    if user_input == "exit":
        print("Goodbye")
        break

    # Get a model response and display its text.
    reply = Chat_agent(user_input)

    print(f'{reply["content"]}\n')
    print("---------------------------------------------------------------------------------------------")
    # Display the stored messages to make the current conversation state visible.
    print(f"This is the chat history {chats_history}")
    print("---------------------------------------------------------------------------------------------")
