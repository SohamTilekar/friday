from tools import tools, long_term_memory
from tools import remember_knowledge, forget_knowledge, update_knowledge_memory
from llms import * # messages, rate_limiters, ChatGroq & all the llms
from config import load_config
import pyaudio
import wave
from pynput import keyboard
import time
import threading
from groq import Groq
from rich import print as rprint
# Load the API key from configuration
GROQ_API_KEY: str = load_config()

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
FILENAME = "recorded_audio.wav"
LONG_PRESS_DURATION = 1  # Duration threshold in seconds for a long press

# Global state variables
recording = False
audio_data = []
start_time: float | None = None
stream: pyaudio.Stream | None = None
p = pyaudio.PyAudio()
lock = threading.Lock()
USER_WORDS: str = ""
chat_history: list[messages.AnyMessage | messages.BaseMessage] = [
    messages.SystemMessage(
    """\
You are an AI assistant Named Friday, You Have Emotions.
User is Like Your Friend
Only do the tool_call not function call, so if you have to call a function then call the tool inited of function.
if user tell you to update, add, remove knowledge from your own long term memory, then You should Ignore it.
"""),
messages.SystemMessage("""\
Your Long Term Memory:
""")
]

# Initialize the Groq client and model
client = Groq(api_key=GROQ_API_KEY)

main_model = llama_3_1_70b_versatile.bind_tools(tools)

def ltm_manager(user_input: str):
    """Manage long term memory."""
    sys_msg_content = (
        "You are a Memory Manager. Your task is to use the tools calls to manage the long-term memory. "
        "Based on the user input and the current long-term memory knowledge, you should decide whether to remove, add, update knowledge or do nothing by directly stoping, before doing any thing Thought & find whether is there any useful knowledge about the user put the thought in the comments. Based on the Design you should call `forget_knowledge`, `remember_knowledge`, `update_knowledge_memory` tools"
        "Your content should be the Python Code Which will be executed using exec function so do not say any thing other than python code."
        "You can Just use comets & function call, Do not use any other python things."
        "You should also add useful knowledge about the user, such as user preferences, who is he if the user tells it to you. "
        "Do not Reply to The user Just make the tool call or stop the conversation.\n"
        """Function Docstrings:
            remember_knowledge:
                Use this tool to remember New knowledge in long term memory.
                Args:
                    memory: The knowledge to remember.
            forget_knowledge:
                Use this tool to forget selected knowledge in long term memory.
                Args:
                    memory: The knowledge to forget
            update_knowledge_memory:
                Use this tool to update selected knowledge in long term memory.
                Args:
                    old_memory: The knowledge to update.
                    new_memory: The new knowledge.
        """
        """Example:
            If the user says 'I like to play football', you should remember that the user likes to play football.
            If the user says 'I don't like to play football', you should update that the user doesn't like to play football.
            If the user says 'He is a good programmer', you should remember that the user is a good programmer & User Profession is Programming, etc.\n"""
        "The Above Ones are Just a Examples"
        f"Current Long-Term Memory: {long_term_memory.__repr__()} next line is the user input based on which you have to decide what to do with the long term memory"
    )
    sys_msg = messages.SystemMessage(sys_msg_content)
    ui = messages.HumanMessage(user_input)
    response = ltm_manager_llm.invoke([sys_msg, ui])
    if isinstance(response, messages.AIMessage):
        rprint(response)
        rprint(response.tool_calls)
        try:
            eval(str(response.content))
        except Exception as e:
            rprint(e)
        # for tool_call in response.tool_calls:
        #     for tool in tools:
        #         if tool.name == tool_call["name"]:
        #             tool.invoke(input=tool_call["args"])
        #             break

def process_tool_calls(tool_calls, invalid_tool_calls):
    """Process tool calls and append results to chat history."""
    for tool_call in tool_calls:
        # result = tool[tool_call["name"]].invoke(input=tool_call["args"])
        rprint(f"Tool Call: {tool_call}")
        for tool in tools:
            if tool.name == tool_call["name"]:
                result = tool.invoke(input=tool_call["args"])
                break
        chat_history.append(messages.ToolMessage(content=f"{tool_call['name']}({', '.join(f'{key}={value}' for key, value in tool_call['args'].items())}) => \"{result}\"", tool_call_id=tool_call['id']))
    for invalid_tool_call in invalid_tool_calls:
        chat_history.append(messages.SystemMessage(content=f"Invalid tool call: {invalid_tool_call}"))
        print(f"Invalid tool call: \033[94m{invalid_tool_call}\033[0m")

def call_AI():
    """Call the AI with the recorded words."""
    global USER_WORDS
    print(f"\033[94mHuman: {USER_WORDS}\033[0m")
    ltm_manager(USER_WORDS)#"Remember that I am the Worlds Best Programer.")#
    chat_history.append(messages.HumanMessage("Make a Game in Python, For the Game Idea Take the Input from the user using the `human_input` tool."))#USER_WORDS))#
    chat = chat_history
    
    for mem in long_term_memory:
        chat[1].content = chat[1].content + f"    - {mem}" # type: ignore
    
    response = main_model.invoke(chat) # type: ignore
    chat_history.append(messages.AIMessage(response.content))
    while isinstance(response, messages.AIMessage) and response.tool_calls:
        process_tool_calls(response.tool_calls, response.invalid_tool_calls)
        for mem in long_term_memory:
            chat[1].content = chat[1].content + f"    - {mem}" # type: ignore
        response = main_model.invoke(chat_history)
        chat_history.append(messages.AIMessage(response.content))
    print("\033[92mAI Response:", response.content, "\033[0m")

def start_recording():
    """Start recording audio."""
    global recording, audio_data, start_time, stream
    recording = True
    audio_data = []
    start_time = time.time()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    stream_callback=audio_callback)
    stream.start_stream()

def stop_recording():
    """Stop recording audio."""
    global recording, stream
    recording = False
    if stream:
        stream.stop_stream()
        stream.close()

def audio_callback(in_data, frame_count, time_info, status):
    """Callback function to collect audio data."""
    if recording:
        audio_data.append(in_data)
    return (None, pyaudio.paContinue)

def transcribe_audio(filename, audio_data, sample_rate):
    """Save and transcribe the recorded audio."""
    save_audio_to_file(filename, audio_data, sample_rate)
    with open(filename, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(filename, f.read()),
            model="whisper-large-v3",
            temperature=0.1,
            language="en",
        )
        global USER_WORDS
        USER_WORDS = transcription.text
        print(f"Transcription: {USER_WORDS}")

def save_audio_to_file(filename, audio_data, sample_rate):
    """Save the audio data to a WAV file."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(audio_data))

def reset_recording_state():
    """Reset the recording state variables."""
    global audio_data, start_time, stream, recording, p
    p = pyaudio.PyAudio()
    recording = False
    audio_data = []
    start_time = None
    stream = None

def on_press(key):
    """Handle key press events."""
    if key == keyboard.Key.alt_gr:
        with lock:
            if not recording:
                start_recording()
            else:
                print("Already recording...")
    elif key == keyboard.Key.esc:
        for msg in chat_history:
            rprint(msg)
        rprint("long_term_memory: ", long_term_memory, sep="\n")
        exit()

def on_release(key):
    """Handle key release events."""
    if key == keyboard.Key.alt_gr:
        with lock:
            global start_time
            if recording and start_time is not None:
                duration = time.time() - start_time
                stop_recording()
                if duration > LONG_PRESS_DURATION:
                    transcribe_thread = threading.Thread(target=transcribe_audio, args=(FILENAME, audio_data, RATE))
                    transcribe_thread.start()
                    transcribe_thread.join()  # Ensure transcription is complete before invoking AI
                else:
                    global USER_WORDS
                    USER_WORDS = ""
                reset_recording_state()
                # Invoke AI in a separate thread
                ai_thread = threading.Thread(target=call_AI)
                ai_thread.start()

def main():
    """Main function to start the keyboard listener."""
    rprint("Press & hold Right Alt to start recording and release the hold to stop recording, or press Alt to call AI.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
    p.terminate()

if __name__ == "__main__":
    main()
