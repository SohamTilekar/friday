import os
import time
from flask import Flask, render_template, Response, request, jsonify
from tools import tools, emojify
from llms import *  # messages, rate_limiters, ChatGroq & all the llms
import json
from config import load_config
import pyaudio
from rich import print as rprint
from datetime import datetime
from langchain_core import messages

# Load the API key from configuration
GROQ_API_KEY, HF_API_Key = load_config()

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
FILENAME = "recorded_audio.wav"
LONG_PRESS_DURATION = 1  # Duration threshold in seconds for a long press

app = Flask(__name__)
current_date :str
face_updated = False

chat_history: list[messages.AnyMessage | messages.BaseMessage] = [
    messages.SystemMessage(
"""\
You are an AI assistant named Friday. You have emotions.
Treat the user as your friend and engage in conversation.
"""
    ),
    messages.SystemMessage(f"Previous State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}"),
    messages.SystemMessage(f"Current State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}"),
]

if os.path.exists('chat_history.json'):
    with open('chat_history.json', 'r') as f:
        file_content = f.read()
        if file_content.strip():  # Check if the file is not empty
            data = json.loads(file_content)
            chat_history.extend(messages.messages_from_dict(data["messages"]))
            current_date = data["current_date"]
            ai_face_url: str = data["ai_face_url"]
            ai_face_name: str = data["ai_face_name"]
            chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
            chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
        else:
            with open('chat_history.json', 'w') as f:
                current_date = datetime.now().strftime("%Y-%m-%d")
                ai_face_url = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.gif"
                ai_face_name = "robot"
                chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
                chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
                json.dump([{"messages": [], "current_date": current_date, "ai_face_url": ai_face_url, "ai_face_name": ai_face_name}], f)
else:
    with open('chat_history.json', 'w') as f:
        current_date = datetime.now().strftime("%Y-%m-%d")
        ai_face_url = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.gif"
        ai_face_name = "robot"
        chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
        chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}" # type: ignore
        json.dump([{"messages": [], "current_date": current_date, "ai_face_url": ai_face_url, "ai_face_name": ai_face_name}], f)

# Initialize the Groq client and model
main_model = llama3_70b_8192.bind_tools(tools)
emoji_selector = emoji_selector.bind_tools([emojify], tool_choice="emojify")

def serialize_message(message):
    """Converts message objects to a serializable dictionary."""
    return {
        "type": message.type,
        "content": message.content if message.content else message.tool_calls if isinstance(message, messages.AIMessage) else None,
        "date_time": message.additional_kwargs.get("datetime", "?"),
    }

@app.route('/', methods=['GET'])
def index():
    serialized_chat_history = [serialize_message(msg) for msg in chat_history]
    return render_template('index.html', chat_history=serialized_chat_history)

@app.route('/message', methods=['Get', 'Post'])
def call_msg():
    user_message = request.json.get('message') # type: ignore
    # Append the human message to chat_history
    msg = messages.HumanMessage(user_message)
    msg.additional_kwargs["datetime"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    USER_WORDS = user_message
    msg.content = f"[{datetime.now().strftime("%I:%M:%S %p")}] " + str(msg.content)
    chat_history.append(msg)
    # Trigger the AI to respond
    call_AI()
    serialized_chat_history = [serialize_message(msg) for msg in chat_history]
    return jsonify(serialized_chat_history)

@app.route('/face', methods=['GET'])
def get_face():
    return jsonify({"url": ai_face_url, "name": ai_face_name})

@app.route('/face_updates')
def face_updates():
    def stream():
        global face_updated
        while True:
            face_updated = False
            # Assuming the face is updated at some point, the server sends the new data
            yield f"data: {json.dumps({'url': ai_face_url, 'name': ai_face_name})}\n\n"
            while not face_updated:
                time.sleep(2)
    return Response(stream(), content_type='text/event-stream')

def process_tool_calls(response: messages.AIMessage):
    """Process tool calls and append results to chat history."""
    global gui
    for tool_call in response.tool_calls:
        rprint(f"Tool Call: {tool_call}")
        for tool in tools:
            if tool.name == tool_call["name"]:
                result = tool.invoke(input=tool_call["args"])
                msg = messages.ToolMessage(content=str(result), tool_call_id=tool_call['id'])
                msg.additional_kwargs["datetime"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                chat_history.append(msg)
                break
        else:
            msg = messages.SystemMessage(content=f"No Tool Named `{tool_call['name']}` Exists")
            msg.additional_kwargs["datetime"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            chat_history.append(msg)
            continue

def generate_final_chat(chat_history: list[messages.AnyMessage | messages.BaseMessage], num_last_inter = 10) -> list[messages.AnyMessage | messages.BaseMessage]:
    global current_date
    sys_msg = chat_history[0]
    previous_state = chat_history[2]
    previous_state.content = previous_state.content.replace("Current Outside State:", "Previous Outside State:") # type: ignore
    last_tool_intr_msg = chat_history[-num_last_inter:] if len(chat_history) > num_last_inter else chat_history[4:]
    last_inter_msg = []
    for msg in chat_history[3:-num_last_inter:]:
        last_inter_msg.append(msg)
    summarized = llama_3_1_70b_versatile.invoke([messages.SystemMessage("You are a Summarizer Bot, Your Work is the Summarize the Below User, AI,, Tool & system Messages Interaction in as Short As Possible in less than 1500 words for the AI to Remember the Useful Knowledge for a Long Time & discard the Useless Knowledge, like if User Shares an useless information then Ignore it, without Loosing Much Details"), messages.HumanMessage(f"Summarize the Below Conversation:\n<conversation>{"\n".join(last_inter_msg.__str__())}<\\conversation>")])
    final_chat = []
    final_chat.append(sys_msg)
    final_chat.append(previous_state)
    final_chat.append(messages.SystemMessage(f"Current Outside State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}\nAI/Your Face: {ai_face_name}"))
    final_chat.append(messages.SystemMessage(f"Summarized Chat till Now: {summarized.content}"))
    final_chat.extend(last_tool_intr_msg)
    if current_date != datetime.now().strftime("%Y-%m-%d"):
        final_chat.append(messages.SystemMessage(f"Today's Date: {datetime.now().strftime('%Y-%m-%d')}"))
        current_date = datetime.now().strftime("%Y-%m-%d")
    return final_chat

def call_routine(reason: str):
    match reason:
        case "state_change":
            ...
        case "ai_called_by_user":
            # emoji Selector for the AI Face based on the chat history
            history = chat_history[1:].copy()
            history.insert(0, messages.SystemMessage("You are an AI Which work is to use the Tools named `emojify` to show the `AI` face in terms of the emoji based on the User, AI, Tool Messages Interaction, do not reply the user just use the tool to `emojify` use this tool only."))
            history.append(messages.SystemMessage("Select the Emoji for the AI Face based on the above conversion till now, try to select the different emoji from the last one because it feels boring to see the same emoji again and again"))
            msg = emoji_selector.invoke(history)
            if isinstance(msg, messages.AIMessage) and msg.tool_calls:
                global ai_face_url, ai_face_name, face_updated
                id, ai_face_name = emojify.invoke(input=msg.tool_calls[0]["args"])
                ai_face_url = f"https://fonts.gstatic.com/s/e/notoemoji/latest/{id}/512.gif"
                face_updated = True
        case _:
            ...

def call_AI():
    """Call the AI with the recorded words."""
    # Create a copy of chat_history for processing
    global chat_history
    chat_history = generate_final_chat(chat_history)
    msg = main_model.invoke(chat_history) # type: ignore
    msg.additional_kwargs["datetime"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    chat_history.append(msg)
    while isinstance(msg, messages.AIMessage) and msg.tool_calls:
        process_tool_calls(msg)
        # Reset the initial content for the next invocation
        msg = main_model.invoke(chat_history)
        msg.additional_kwargs["datetime"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        chat_history.append(msg)
    call_routine("ai_called_by_user")
    rprint("Chat History: ", chat_history)

def main():
    try:
        app.run(debug=True)
    finally:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            # Clean up
            with open('chat_history.json', 'w') as f:
                json.dump(
                    {
                        "messages": messages.messages_to_dict(chat_history[3:]),
                        "current_date": current_date,
                        "ai_face_url": ai_face_url,
                        "ai_face_name": ai_face_name
                    },
                    f,
                    indent=4
                )
            rprint("Exiting Friday...")

rprint("Starting Friday...")

if __name__ == "__main__":
    main()