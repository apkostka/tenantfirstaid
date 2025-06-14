#!/usr/bin/env python3
import jsonlines
import os
from pathlib import Path

# Import the model from app.py
from .chat import MODEL
from .shared import DEFAULT_INSTRUCTIONS

# Define file paths (relative to the script location)
SCRIPT_DIR = Path(__file__).parent.parent  # Go up one level to backend directory
DATA_FILE = SCRIPT_DIR / "chatlog.jsonl"
OUTPUT_FILE = SCRIPT_DIR / f"combined_training_{MODEL.replace('.', '_')}.jsonl"


def prepare_training_data():
    """
    Process training data from chatlog.jsonl to create a clean combined_training.jsonl 
    file suitable for model training.

    This script fixes several issues with the data format:
    1. Removes the 'metadata' field from each entry (causing API errors)
    2. Ensures each conversation includes the system prompt
    3. Organizes messages by session to create proper conversation flows
    4. Uses a sliding window approach to create multiple training examples from each conversation
       at different points, which helps the model learn to respond appropriately at various stages

    The approach:
    - For conversations: [system, assistant, user, assistant, user, assistant, ...]
      - Creates the full conversation example
      - Plus intermediate examples ending with assistant responses:
        1. [system, assistant, user, assistant]
        2. [system, assistant, user, assistant, user, assistant]
        3. And so on
    - This helps the model learn to respond appropriately at different
      points in a conversation

    Returns:
        Path: The path to the generated training file
    """
    print("Preparing training data...")
    print(f"- Data file: {DATA_FILE}")
    print(f"- Output file: {OUTPUT_FILE}")

    # List to collect all processed training examples
    processed_examples = []

    # Track sessions to build complete conversations
    sessions = {}

    # Process regular conversation data
    if os.path.exists(DATA_FILE):
        print(f"Reading conversation data from {DATA_FILE}")
        with jsonlines.open(DATA_FILE, mode="r") as inf:
            for item in inf:
                if (
                    "messages" in item
                    and "metadata" in item
                    and "session_id" in item["metadata"]
                ):
                    session_id = item["metadata"]["session_id"]

                    # Initialize session with system prompt if needed
                    if session_id not in sessions:
                        sessions[session_id] = [
                            {"role": "system", "content": DEFAULT_INSTRUCTIONS}
                        ]

                    # Add the user and assistant messages
                    for msg in item["messages"]:
                        sessions[session_id].append(msg)
    else:
        print(f"Warning: {DATA_FILE} not found")

    # Process feedback data
    separate_feedback_examples = []
    feedback_session_ids = set()  # Track which sessions came from feedback

    if os.path.exists(FEEDBACK_FILE):
        print(f"Reading feedback data from {FEEDBACK_FILE}")
        with jsonlines.open(FEEDBACK_FILE, mode="r") as inf:
            for item in inf:
                if "messages" in item:
                    # Feedback examples often contain complete conversations already
                    # Just need to ensure they have a system message
                    if item["messages"] and item["messages"][0]["role"] != "system":
                        item["messages"].insert(
                            0, {"role": "system", "content": DEFAULT_INSTRUCTIONS}
                        )

                    # For feedback examples, create sliding window examples
                    # just like for regular conversations
                    messages = item["messages"]

                    if len(messages) >= 3:  # system + user + assistant
                        # Create sliding window examples with proper user/assistant pairs
                        user_indices = []
                        for i, msg in enumerate(messages):
                            if msg["role"] == "user":
                                user_indices.append(i)

                        # For each user message, create a training example that ends
                        # with that user message and the assistant's response
                        for idx in user_indices:
                            # Only create example if there's an assistant response after this user message
                            if (
                                idx < len(messages) - 1
                                and messages[idx + 1]["role"] == "assistant"
                            ):
                                # Create a window up to and including this user message + assistant response
                                window = messages[
                                    : idx + 2
                                ]  # Include user message and assistant response
                                separate_feedback_examples.append({"messages": window})

                    # If this feedback has a session_id, track it and update the session data
                    if "metadata" in item and "session_id" in item["metadata"]:
                        session_id = item["metadata"]["session_id"]
                        feedback_session_ids.add(
                            session_id
                        )  # Mark this session as coming from feedback

                        if session_id in sessions:
                            # Replace the session with the corrected conversation but we won't process it again
                            sessions[session_id] = item["messages"]
    else:
        print(f"Warning: {FEEDBACK_FILE} not found")

    # Convert sessions to training examples using sliding window approach
    for session_id, messages in sessions.items():

        # Only use examples with at least one exchange
        if len(messages) >= 3:  # system + user + assistant
            # Track whether we've added the full conversation already
            added_full = False

            # Include sliding window examples
            for i in range(3, len(messages), 2):  # Start with minimum context
                # Only include if this slice ends with an assistant message
                if i < len(messages) and messages[i - 1]["role"] == "assistant":
                    conversation_window = messages[:i]

                    # If we're at the last window (full conversation),
                    # only add it if we haven't already
                    if i >= len(messages) - 1:
                        if not added_full:
                            processed_examples.append({"messages": conversation_window})
                            added_full = True
                    else:
                        # For intermediate windows, always add
                        processed_examples.append({"messages": conversation_window})

            # Make sure we add the full conversation if we didn't already
            if not added_full:
                processed_examples.append({"messages": messages})


    # Write the processed data to the output file
    print(f"Writing {len(processed_examples)} examples to {OUTPUT_FILE}")
    with jsonlines.open(OUTPUT_FILE, mode="w") as outf:
        for item in processed_examples:
            outf.write(item)

    print(f"Training data preparation complete. Output file: {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    output_file = prepare_training_data()
    print(f"\nSuccess! Your training file is ready at:\n{output_file}")
    print("\nTo use this file for training, run:")
    print(
        f"openai fine-tuning create -t {output_file} -m {MODEL} --suffix law_chat"
    )
