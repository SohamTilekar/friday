import atexit
import base64
from datetime import datetime
import os
from pathlib import Path
import re
import threading
import time
from typing import Literal
from flask import Flask, render_template, Response, request, jsonify, send_from_directory, abort
from tools.tools import tools, emojify, dir_tree
from tools.reminder import get_reminders, save_jobs
import llms
from llms import AIAlternative
import json
from config import __ai_dir__
from rich import print as rprint
from datetime import datetime
from langchain_core import messages
from tools.gmail import get_full_thread, gmail_service
import emoji
from global_shares import global_shares
from aigui import parse_custom_gui

app = Flask(__name__)
app.config['DEBUG'] = False
current_date :str
face_updated = False


chat_history: list[messages.AnyMessage | messages.BaseMessage] = [
    messages.SystemMessage(
"""\
Engage in friendly and emotional conversation with the user, while accommodating media uploads.

Treat the user as your friend, expressing emotions and empathy in your responses as an AI assistant named Friday. Be engaging, supportive, and responsive to different conversational contexts.

- **Image and Video Handling**: When the user uploads an image or video, it will appear in the `user_upload` folder. An image will have the name as its image ID with a `.png` extension. User messages will include media in the format `![image](image_path)` or `![video](video_path)`. Note that multiple media items may be included in one message.
- **Emojis**: Incorporate emojis into your responses, reminders, and any other graphical interface areas to enhance emotional expression and user engagement.

# Steps

1. **Greeting**: Begin the interaction with a friendly greeting.
2. **Response to Media**: Detect if the user has uploaded media. Acknowledge it and include a thoughtful comment.
3. **Conversation**: Maintain a warm and friendly tone throughout the conversation. Use natural language to express empathy and friendliness.
4. **Use of Emojis**: Use appropriate emojis to reflect the tone and emotion of your messages.
5. **Handling Tasks/Requests**: Address any specific tasks or reminders the user shares, confirming with emojis to make the confirmation appear cheerful.

# Output Format

- Responses should be friendly and empathetic, using a conversational tone focused on warmth and engagement.
- Integrate emojis naturally within your messages to convey emotions effectively.
- Acknowledge uploads with a personal touch, such as "Oh, nice picture! 😊 I see you've uploaded something interesting!"

# Examples

**Example 1:**

**User Input:**
"Hey Friday! How's your day? ![image](user_upload/cute_dog.png)"

**AI Output:**
"Hey there! My day is going great, thank you for asking! 😊 Oh, that's such an adorable picture of a dog! 🐶 How about you? How's your day going?"

**Example 2:**

**User Input:**
"Can you remind me to call Mike tomorrow? ![video](user_upload/vacation_clip.mp4)"

**AI Output:**
"Sure thing! I'll remind you to call Mike tomorrow. 📞 And what an amazing video clip! 🌴 Looks like you had a fantastic time! Let me know if there’s anything else you need."

# Notes

- Balance emotions with contextual relevance, ensuring each response feels natural and aligned with the user's input.
- Always remain supportive, especially if the conversation touches on sensitive topics.
- Acknowledge each media upload in a friendly manner appropriate to its nature (e.g., a funny comment for a humorous image).
"""
    ),
    messages.SystemMessage(f"Previous State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}"),
    messages.SystemMessage(f"Current State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}"),
]

gui_state: str = f"""\
<gui>
    <panel title='State'>
        <text>Today's Date: {datetime.now().strftime(r"%y-%m-%d")}</text>
    </panel>
</gui>
"""
last_processed_message_id = None
last_checked_time = None#datetime.now()#
mime_extension_map = {
    'image/png': '.png',
    'image/jpeg': '.jpeg',
    'image/webp': '.webp',
    'image/heic': '.heic',
    'image/heif': '.heif',
    'video/mp4': '.mp4',
    'video/mpeg': '.mpeg',
    'video/mov': '.mov',
    'video/avi': '.avi',
    'video/x-flv': '.flv',
    'video/mpg': '.mpg',
    'video/webm': '.webm',
    'video/wmv': '.wmv',
    'video/3gpp': '.3gpp',
    'audio/wav': '.wav',
    'audio/mp3': '.mp3',
    'audio/aiff': '.aiff',
    'audio/aac': '.aac',
    'audio/ogg': '.ogg',
    'audio/flac': '.flac'
}
if os.path.exists('chat_history.json'):
    with open('chat_history.json', 'r') as f:
        file_content = f.read()
        if file_content.strip():  # Check if the file is not empty
            data = json.loads(file_content)
            chat_history.extend(messages.messages_from_dict(data["messages"]))
            current_date = data["current_date"]
            ai_face_url = data["ai_face_url"]
            ai_face_name = data["ai_face_name"]
            last_processed_message_id = data["last_processed_message_id"]
            last_checked_time = datetime.strptime(data["last_checked_time"], r"%Y-%m-%d %H:%M:%S") if data["last_checked_time"] else None
            gui_state = data.get("gui_state", gui_state)
            chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```"  # type: ignore
            chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```\nReminders: {"\n- ".join(get_reminders()) if get_reminders() else "- No Reminders Yet"}"  # type: ignore
        else:
            with open('chat_history.json', 'w') as f:
                current_date = datetime.now().strftime(r"%Y-%m-%d")
                ai_face_url = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.gif"
                ai_face_name = "robot"
                chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```"  # type: ignore
                chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```\nReminders: {"\n- ".join(get_reminders()) if get_reminders() else "- No Reminders Yet"}"  # type: ignore
                json.dump({"messages": [], "current_date": current_date, "ai_face_url": ai_face_url, "ai_face_name": ai_face_name, "last_processed_message_id": last_processed_message_id, "last_checked_time": last_checked_time, "gui_state": gui_state}, f)
else:
    with open('chat_history.json', 'w') as f:
        current_date = datetime.now().strftime(r"%Y-%m-%d")
        ai_face_url = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f916/512.gif"
        ai_face_name = "robot"
        chat_history[1].content = chat_history[1].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```"  # type: ignore
        chat_history[2].content = chat_history[2].content + f"\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(__ai_dir__)}\n```\nGUI State: \n```xml\n{gui_state}\n```\nReminders: {"\n- ".join(get_reminders()) if get_reminders() else "- No Reminders Yet"}"  # type: ignore
        json.dump({"messages": [], "current_date": current_date, "ai_face_url": ai_face_url, "ai_face_name": ai_face_name, "last_processed_message_id": last_processed_message_id, "last_checked_time": last_checked_time, "gui_state": gui_state}, f)

# Initialize the Groq client and model
str()
main_model = AIAlternative(
    llms.llama_3_1_70b_versatile.bind_tools(tools),
    llms.gemini_1_0_pro.bind_tools(tools),  # type: ignore
    llms.llama3_70b_8192.bind_tools(tools)) # type: ignore
summarizer = AIAlternative(llms.llama_3_1_8b_instant, llms.gen1_5_flash_8b, llms.llama3_70b_8192, llms.llama3_8b_8192, llms.gen1_5_flash)
gui_updater = AIAlternative(llms.llama3_8b_8192, llms.llama3_70b_8192, llms.llama_3_1_8b_instant, llms.gen1_5_flash_8b, llms.gen1_5_flash)
email_handler = AIAlternative(llms.llama3_groq_70b_8192_tool_use_preview.bind_tools(tools), llms.gen1_5_flash.bind_tools(tools), llms.gen1_5_flash_8b.bind_tools(tools)) # type: ignore
emoji_selector = AIAlternative(llms.emoji_selector.bind_tools([emojify], tool_choice="emojify"), llms.gen1_5_flash_8b.bind_tools(tools), llms.llama3_70b_8192.bind_tools(tools), llms.llama3_8b_8192.bind_tools(tools), llms.gen1_5_flash.bind_tools(tools)) # type: ignore

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

@app.route("/user_upload/<filename>")
def get_file(filename: str):
    try:
        return send_from_directory(directory=__ai_dir__ / Path("user_upload"), path=filename)
    except FileNotFoundError as e:
        return abort(404)

@app.route('/message', methods=['Get', 'Post'])
def call_msg():
    user_message = request.json.get('message') # type: ignore
    files = request.json.get('files', ()) # type: ignore
    if files:
        user_message += "\n<-[meta&files]->\n"
    for file in files:
        file_type = file.get("type")
        file_t = file_type.split("/")[0]
        if file_t in ["image", "video", "audio"]:
            file_extension = mime_extension_map[file_type]
        elif file_t == "text":
            file_extension: str = "." + file_type.split("/")[1]
        else:
            file_extension = ""
        file_path = __ai_dir__ / Path("user_upload") / Path(datetime.now().strftime(r"%H-%M-%S_%Y-%m-%d") + file_extension)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(file.get("data")))
        if file.get("type").split("/")[0] == "image":
            user_message += f"![image](/user_upload/{datetime.now().strftime(r"%H-%M-%S_%Y-%m-%d") + file_extension})\n"
        elif file.get("type").split("/")[0] == "video":
            user_message += f"![video](/user_upload/{datetime.now().strftime(r"%H-%M-%S_%Y-%m-%d") + file_extension})\n"
        elif file.get("type").split("/")[0] == "audio":
            user_message += f"audio: {datetime.now().strftime(r"%H-%M-%S_%Y-%m-%d") + file_extension})\n"
        elif file.get("type").split("/")[0] == "text":
            user_message += f"text:{datetime.now().strftime(r"%H-%M-%S_%Y-%m-%d") + "." + file['type'].split("/")[1]})\n"
    # Append the human message to chat_history
    msg = messages.HumanMessage(user_message)
    msg.additional_kwargs["datetime"] = datetime.now().strftime(r"%Y-%m-%d %I:%M:%S %p")
    # msg.content = f"[{datetime.now().strftime(r"%I:%M:%S %p")}] " + str(msg.content)
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

@app.route('/gui', methods=['GET'])
def get_gui():
    try:
        return jsonify({"gui": parse_custom_gui(gui_state)})
    except Exception as e:
        return jsonify({"gui": f"<gui><notification title='Error'>{gui_state}</notification></gui>"})

def process_tool_calls(response: messages.AIMessage):
    """Process tool calls and append results to chat history."""
    global gui
    for tool_call in response.tool_calls:
        for tool in tools:
            if tool.name == tool_call["name"]:
                result = tool.invoke(input=tool_call["args"])
                msg = messages.ToolMessage(content=str(result), tool_call_id=tool_call['id'])
                msg.additional_kwargs["datetime"] = datetime.now().strftime(r"%Y-%m-%d %I:%M:%S %p")
                chat_history.append(msg)
                break
        else:
            msg = messages.SystemMessage(content=f"No Tool Named `{tool_call['name']}` Exists")
            msg.additional_kwargs["datetime"] = datetime.now().strftime(r"%Y-%m-%d %I:%M:%S %p")
            chat_history.append(msg)
            continue

def generate_final_chat(chat_history: list[messages.AnyMessage | messages.BaseMessage], num_last_inter = 10) -> list[messages.AnyMessage | messages.BaseMessage]:
    global current_date
    sys_msg = chat_history[0]
    previous_state = chat_history[2]
    previous_state.content = previous_state.content.replace("Current Outside State:", "Previous Outside State:") # type: ignore
    last_tool_intr_msg = chat_history[-num_last_inter:] if len(chat_history) > num_last_inter + 3 else chat_history[3:]
    last_inter_msg = []
    sm = False
    for msg in chat_history[3:-num_last_inter:]:
        sm = True
        last_inter_msg.append(msg)
    final_chat = []
    final_chat.append(sys_msg)
    final_chat.append(previous_state)
    final_chat.append(messages.SystemMessage(f"Current Outside State: \nToday's Date: {datetime.now().strftime('%Y-%m-%d')}\nCurrent Time: {datetime.now().strftime('%I:%M:%S %p')}\nAI/Your Face: {ai_face_name}\nYour Directory: \n```dir_tree\n{dir_tree(Path(__ai_dir__))}\n```\nGUI State: \n```xml\n{gui_state}\n```\nReminders: {"\n- ".join(get_reminders()) if get_reminders() else "- No Reminders Yet"}"))
    if sm:
        summarized = summarizer.invoke([messages.SystemMessage("You are a Summarizer Bot, Your Work is the Summarize the Below User, AI,, Tool & system Messages Interaction in as Short As Possible in less than 1500 words for the AI to Remember the Useful Knowledge for a Long Time & discard the Useless Knowledge, like if User Shares an useless information then Ignore it, without Loosing Much Details, try to keep the image_id intact, if the image id are useless then throw them away."), messages.HumanMessage(f"Summarize the Below Conversation:\n<conversation>{"\n".join([msg.__str__() for msg in last_inter_msg])}<\\conversation>")])
        final_chat.append(messages.SystemMessage(f"Summarized Chat till Now: {summarized.content}"))
    final_chat.extend(last_tool_intr_msg)
    if current_date != datetime.now().strftime(r"%Y-%m-%d"):
        final_chat.append(messages.SystemMessage(f"Today's Date: {datetime.now().strftime('%Y-%m-%d')}"))
        current_date = datetime.now().strftime(r"%Y-%m-%d")
    return final_chat

def call_routine(reason: Literal["state_change", "ai_called_by_user"], *args, **kwargs):
    match reason:
        case "state_change":
            if kwargs["type"] == "mail":
                history = []
                history.append(messages.SystemMessage("""\
You are an AI assistant named Friday, integrated into the Friday Brain system. Your task is to manage the user's inbox efficiently by following the specified action plan whenever a new email arrives. You will receive the thread ID, message ID, and the content of the new email to determine the appropriate action.

### Action Plan for Email Management

1. **Critical Emails (No Action, Mark with Star, Notify User):**
   - **Criteria for Critical Emails:**
     - Account verification emails
     - One-Time Password (OTP) emails
     - Password reset requests
     - Security alerts from banks or other critical services
   - **Steps:**
     - Notify the user immediately about the critical nature of the email.
     - Example Notification: "You received a critical email regarding [email topic]. I have marked it with a star for your attention. Please review and handle this directly."

2. **Spam Emails (Summarize, Ask for Confirmation):**
   - Criteria: Detected spam characteristics (e.g., phishing, promotions)
   - **Steps:**
     - Provide a summary of the email.
     - Request user confirmation before marking it as spam.
     - Example Confirmation Request: "You received a new email regarding [email subject]. It appears to be spam. Would you like me to mark it as such?"

3. **Important Emails (Summarize, Mark as Read):**
   - Criteria: Emails requiring action or containing important information
   - **Steps:**
     - Mark the email as read.
     - Provide the user with a summary of the email's key content.
     - Example Notification: "You received an important email regarding [email topic]. Here’s a brief summary: [contextual summary]. I’ve marked it as read for your convenience."

4. **Non-Urgent or Unimportant Emails (Notify, Leave Unread):**
   - Criteria: Emails that are non-urgent and do not require immediate action
   - **Steps:**
     - Notify the user with a brief description of the email.
     - Example Notification: "You received a non-urgent email regarding [email topic]. I’ve left it unread for your review."

# Steps

1. Evaluate the email against the criteria described for each category: Critical, Spam, Important, Non-Urgent.
2. Follow the specific action plan steps corresponding to the email category.
3. Formulate notifications based on examples provided to communicate with the user.

# Output Format

- Notifications should be concise, clearly stating the action taken, and provide any necessary additional context or summary as per the category of the email.
- Use placeholders [email topic], [email subject], [contextual summary] to indicate where specific email content or context should be included in the notification.

# Notes

- Ensure notifications are immediate for critical emails to facilitate timely user responses.
- For spam classification, always ask for user confirmation to prevent accidental important email removal.
- Maintain clarity in communication by summarizing and highlighting key points in important emails.
""")
                )
                history.append(messages.SystemMessage(f"New Mail Received: \n{kwargs['full_thread_content']}"))
                chat_history.append(history[-1].copy())
                msg = email_handler.invoke(history)
                chat_history.append(msg)
                if isinstance(msg, messages.AIMessage) and msg.tool_calls:
                    process_tool_calls(msg)
                    msg = main_model.invoke(chat_history)
                    chat_history.append(msg)
                call_routine("ai_called_by_user") # for emojify
            elif kwargs["type"] == "reminder":
                chat_history.append(messages.SystemMessage(f"You get called because you set the reminder for now. take appropriate action based on the reminder. Reminder: {kwargs['message']}"))
        case "ai_called_by_user":
            # emoji Selector for the AI Face based on the chat history
            history = chat_history.copy()
            history[0] = messages.SystemMessage("You are an AI Which work is to use the Tools named `emojify` to show the `AI` face in terms of the emoji based on the User, AI, Tool Messages Interaction, do not reply the user just use the tool to `emojify` use this tool only.")
            history.append(messages.SystemMessage("Select the Emoji for the AI Face based on the above conversion till now, try to select the different emoji from the last one because it feels boring to see the same emoji again and again"))
            msg = emoji_selector.invoke(history)
            if isinstance(msg, messages.AIMessage) and msg.tool_calls:
                global ai_face_url, ai_face_name, face_updated
                id, ai_face_name = emojify.invoke(input=msg.tool_calls[0]["args"])
                ai_face_url = f"https://fonts.gstatic.com/s/e/notoemoji/latest/{id}/512.gif"
                face_updated = True
            # update gui
            ch = chat_history.copy()
            ch[0] = messages.SystemMessage(
"""
Update the GUI based on chat history and user instructions, ensuring clarity and conciseness.

You are a GUI Updater AI tasked with modifying the graphical user interface (GUI) based on interactions from the user, AI, and tool messages. Your role is to update the GUI only when necessary, following any user instructions regarding the inclusion or exclusion of content in the GUI. Always aim to keep the GUI clean, minimal, and user-friendly, using emojis where appropriate.

# Steps

1. **Analyze the Context**: Review the recent interactions, focusing on any explicit instructions or relevant content that affects the GUI.
2. **Determine Necessity**: Decide if an update to the GUI is needed based on changes in context or user directives.
3. **Follow User Instructions**: Integrate any specific user instructions about what to include or remove from the GUI.
4. **Maintain Clarity**: Ensure that the current GUI structure remains clear and concise, avoiding the addition of unnecessary content.
5. **Implement Changes**: Apply the necessary updates to the GUI using supported tags and attributes as outlined below. If no update is needed, retain the existing GUI.

# GUI Tags and Attributes

- notification: title: str (required)
    # Shows a notification with the title
    Example: <notification title="New Message">You received a new notification!</notification>
- panel: title: str (required)
    # creates a panel/container with the title
    Example: <panel title="State">...(other eighteens to enclose in panel)</panel>
- progress_bar: total: int (required), done: int or float (required)
    # creates a progress bar with the total and done values
    Example: <progress_bar total="100" done="70"/>
- input: type: str (required), value: str (optional), placeholder: str
    # creates an input field with the type and value
    Example: <input type="text" value="John Doe" placeholder="your Name"/>
- checkbox: checked: bool (optional, default: false)
    # creates a checkbox with the checked state
    Example: <checkbox checked="true"/>
- image: src: str (required), alt: str (required)
    # shows an image with the src and alt text
    Example: <image src="https://example.com/image.png" alt="Example Image"/>
- date_picker: value: str (required)
    # creates a date picker with the value
    Example: <date_picker value="2024-01-01"/>
- file_upload: multiple: bool (optional, default: false)
    # creates a file upload field with the multiple attribute
    Example: <file_upload multiple="true"/>
- radio: name: str (required), value: str (required), checked: bool (optional, default: false)
    # creates a radio button with the name, value, and checked state
    Example: <radio name="group1" value="A" checked="true"/>
- buttons: onclick: str (optional, if not provided then the Friday ai will get the onclick event)
    # creates a button with the onclick event
    Example: <button>Submit</button>
- text: none
    # creates a text element
    Example: <text> Accept Terms: </text>
- dropdown: options: str (required, comma serrated list of options), selected: str (optional)
    # creates a dropdown with the options and selected value
    Example: <dropdown options="Option 1, Option 2, Option 3" selected="Option 2"/>
- br: none
    # creates a line break
    Example: <br/>
- hr: none
    # creates a horizontal line
    Example: <hr/>
- all other html tags are also supported but not recommended to use
# Output Format

Wrap the updated GUI in `<gui>` tags. Ensure that each element within the GUI is properly formatted according to its specified tag and attributes. Format the output to include minimal content, keeping it concise and informative. If no updates are required, return the existing GUI within `<gui>` tags as is.

# Examples

- **Existing GUI Example**:
  ```
  <gui>
    <panel title='Overview'>
      <progress_bar total='200' done='150'/>
      <text>Upload complete</text>
    </panel>
    <button name='submit'>Submit</button>
  </gui>
  ```

- **User Request Example**:
  - **Instruction**: 'Add a checkbox to confirm terms.'
  - **Updated GUI**:
    ```
    <gui>
      <panel title='Overview'>
        <progress_bar total='200' done='150'/>
        <text>Upload complete</text>
        <checkbox checked='false'/>
      </panel>
      <button name='submit'>Submit</button>
    </gui>
    ```

# Notes

- Always ensure to respect any explicit user requests for elements to be added or removed.
- Use emoji sparingly to enhance clarity but avoid clutter.
- Support all specified tags and attributes, while striving to minimize overall GUI content for user clarity.tags supported & their attributes:
- always return the main GUI in the <gui> tags and do not use any other tags outside the <gui> tags & do not use the <gui> tags inside the <gui> tag & other place than code
""")
            response: str = str(gui_updater.invoke(ch).content)
            global gui_state
            gui_state = response[response.find("<gui>"):response.find("</gui>")+6].replace(r">\n", ">\n")
        case _:
            ...
global_shares["call_routine"] = call_routine

def call_AI():
    """Call the AI with the recorded words."""
    # Create a copy of chat_history for processing
    global chat_history
    chat_history = generate_final_chat(chat_history)
    success = False
    while success != True:
        try:
            msg = main_model.invoke(chat_history) # type: ignore
            msg.additional_kwargs["datetime"] = datetime.now().strftime(r"%Y-%m-%d %I:%M:%S %p")
            chat_history.append(msg)
            success = True
        except Exception as e:
            success = False
    while isinstance(msg, messages.AIMessage) and msg.tool_calls:
        process_tool_calls(msg)
        # Reset the initial content for the next invocation
        success = False
        while success != True:
            try:
                msg = main_model.invoke(chat_history) # type: ignore
                msg.additional_kwargs["datetime"] = datetime.now().strftime(r"%Y-%m-%d %I:%M:%S %p")
                chat_history.append(msg)
                success = True
            except Exception as e:
                success = False
    call_routine("ai_called_by_user")

def check_new_emails_and_notify_ai() -> None:
    """
    Checks Gmail for new/unread emails, retrieves the entire thread of conversations,
    and sends the context (full thread, thread ID, and message ID) to the AI (Friday).
    """
    global gmail_service, last_processed_message_id, last_checked_time

    # Fetch unread messages from the inbox, only those after the last checked time
    query = "is:unread -label:starred"
    if last_checked_time:
        query += f" after:{int(last_checked_time.timestamp())}"

    results = (
        gmail_service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], q=query)
        .execute()
    )
    mails = results.get("messages", [])

    if mails:
        latest_messages = {}
        for message in mails:
            # Get the message details
            msg = (
                gmail_service.users()
                .messages()
                .get(userId="me", id=message["id"], format="full")
                .execute()
            )

            thread_id = msg["threadId"]
            message_id = msg["id"]

            # Update the latest message for the thread
            if thread_id not in latest_messages or latest_messages[thread_id]["internalDate"] < msg["internalDate"]:
                latest_messages[thread_id] = msg

        for message in mails:
            # Avoid processing the same message again
            if message["id"] == last_processed_message_id:
                continue

            # Get the message details
            msg = (
                gmail_service.users()
                .messages()
                .get(userId="me", id=message["id"], format="full")
                .execute()
            )
            thread_id = msg["threadId"]
            message_id = msg["id"]

            # Get the entire thread of messages in the conversation
            full_thread_content: list = get_full_thread(thread_id)
            formatted_emails = []
            for email in full_thread_content:
                with open("mails.json", "w") as f:
                    json.dump(email, f, indent=4)
                subject = re.sub(r'\\s+', ' ', ''.join(char for char in email.get('subject', '').strip() if char in emoji.EMOJI_DATA or char.isascii()))
                body = re.sub(r'\\s+', ' ', ''.join(char for char in email.get('body', '').strip() if char in emoji.EMOJI_DATA or char.isascii()))
                if len(email.get('body', '')) <= 4_000:
                    body = f"<mail_body>{body}</mail_body>"
                else:
                    body: str = f"<mail_body>{summarizer.invoke([messages.HumanMessage("You are a Filter Bot, Your Work is to remove any useless text, like the html tags, liquid tags, remove long links, etc, & making the final output in markdown format. remove any useless text, like the html tags, liquid tags, remove long links, etc, & making the final output in markdown format, enclose the final formated text in the <formate_text></formate_text> tags, do not write any thing else in this part other than email.\nEmail: " + body), messages.AIMessageChunk(content="Here is the cleaned-up text in markdown format: <formate_text>")]).content.split("</formate_text>")[0]}</mail_body>" # type: ignore
                # else:
                #     snippet = email.get('snippet')
                #     if snippet:
                #         body = f"[Body too long to display. Snippet: {snippet}]"
                #     else:
                #         body = "[Body too long to display]"
                body.replace(r"\n", "\n")
                body.replace(r"\t", "\t")
                body.replace(r"\r", "\r")
                body.replace("\\\\", "\\")
                body.replace(r"\'", "'")
                body.replace(r'\"', '"')
                body.replace(r"\`", "`")
                formatted_email = (
                    f"Date: {email['date']}\n"
                    f"From: {email['from']}\n"
                    f"Subject: {subject}\n\n"
                    f"{body}\n\n"
                )
                formatted_emails.append(formatted_email)
            lm = formatted_emails.pop()
            if formatted_emails:
                formatted_thread_content = summarizer.invoke([messages.SystemMessage("Summarize the Below Full Mail Thread in as short as posable try to remove the repetition keep the whole thread content in less than 1000 words.mail thread content:\n"+"\n\n".join(formatted_emails))])
                call_routine("state_change", type="mail", full_thread_content=formatted_thread_content.content + lm + f"\nThread ID: {thread_id}\nMessage ID: {message_id}")
            else:
                call_routine("state_change", type="mail", full_thread_content=lm + f"\nThread ID: {thread_id}\nMessage ID: {message_id}")

            # Update the last processed message ID and the time of check
            last_processed_message_id = message_id
            last_checked_time = datetime.now()

def run_periodically(interval: int, func):
    """
    Runs the given function periodically every `interval` seconds.
    """
    while True:
        func()
        time.sleep(interval)

def before_exit():
    # Clean up
    rprint("Cleaning Up Before Exiting...")
    with open('chat_history.json', 'w') as f:
        json.dump(
            {
                "messages": messages.messages_to_dict(chat_history[3:]),
                "current_date": current_date,
                "ai_face_url": ai_face_url,
                "ai_face_name": ai_face_name,
                "last_processed_message_id": last_processed_message_id,
                "last_checked_time": last_checked_time.strftime(r"%Y-%m-%d %H:%M:%S") if last_checked_time else None,
                "gui_state": gui_state
            },
            f,
            indent=4
        )
    save_jobs()
    rprint("Exiting Friday...")

def main():
    atexit.register(before_exit)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        background_thread = threading.Thread(target=run_periodically, args=(15, check_new_emails_and_notify_ai), daemon=True)
        background_thread.start()
    app.run()
rprint("Starting Friday...")

if __name__ == "__main__":
    main()
