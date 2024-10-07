import pickle
from rich import print
import schedule
import time
from langchain_core.tools import tool as tool_decorator
from typing import Literal, Optional
import os


class Reminder:
    def __init__(self, message: str, once: bool) -> None:
        self.message = message
        self.once = once
        self.skip_next = False
        self.re_remind = False
        self.id: str

    def __call__(self):
        if self.skip_next:
            self.skip_next = False
            return
        create_popup(self.message)
        if self.once:
            return schedule.CancelJob


# Dark-themed tkinter template for reminders
import customtkinter as ctk
import time
from threading import Thread

# Set the appearance and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class ReminderPopup(ctk.CTk):
    def __init__(self, message):
        super().__init__()

        self.message = message
        self.title("Reminder")  # Title of the window
        self.geometry("400x250")  # Size of the window
        self.configure(fg_color='#2C2F33')  # Set the background color
        self.resizable(False, False)  # Make the window non-resizable
        self.wm_attributes('-topmost', True)  # Keep the window on top
        self.wm_attributes('-alpha', 0)  # Start with transparency for fade-in

        self.init_ui()  # Initialize the UI elements
        self.fade_in()  # Call the fade-in effect

    def init_ui(self):
        # Custom title bar
        title_bar = ctk.CTkFrame(self, fg_color='#23272A', corner_radius=10)
        title_bar.pack(fill=ctk.X, padx=10, pady=(10, 0))

        title_label = ctk.CTkLabel(title_bar, text="🔔 Reminder", text_color='#FFFFFF', font=ctk.CTkFont(size=12, weight='bold'))
        title_label.pack(side=ctk.LEFT, padx=5)

        close_button = ctk.CTkButton(title_bar, text='X', text_color='#FFFFFF', fg_color='#23272A', hover_color='#ff5555',
                                     font=ctk.CTkFont(size=12, weight='bold'), width=30, height=30, command=self.close_window)
        close_button.pack(side=ctk.RIGHT)

        # Message label
        message_label = ctk.CTkLabel(self, text=self.message, text_color='#FFFFFF', font=ctk.CTkFont(size=14), wraplength=380)
        message_label.pack(pady=(20, 10), padx=20)

        # "Remind Again" label and input field
        remind_again_label = ctk.CTkLabel(self, text="Remind again in (minutes):", text_color='#CCCCCC', font=ctk.CTkFont(size=12))
        remind_again_label.pack()

        self.remind_again_input = ctk.CTkEntry(self, font=ctk.CTkFont(size=12))
        self.remind_again_input.insert(0, "2.5")
        self.remind_again_input.pack(pady=5)

        # Button layout
        button_frame = ctk.CTkFrame(self, fg_color='#2C2F33')
        button_frame.pack(pady=10)

        remind_button = ctk.CTkButton(button_frame, text='Remind Again', fg_color='#7289DA', text_color='#FFFFFF',
                                      font=ctk.CTkFont(size=12, weight='bold'), command=self.remind_again)
        remind_button.pack(side=ctk.LEFT, padx=10)

        ok_button = ctk.CTkButton(button_frame, text='OK', fg_color='#7289DA', text_color='#FFFFFF',
                                  font=ctk.CTkFont(size=12, weight='bold'), command=self.close_window)
        ok_button.pack(side=ctk.LEFT)

    def fade_in(self):
        """
        Creates a smooth fade-in effect for the window.
        """
        def fade():
            try:
                for i in range(0, 21):
                    self.wm_attributes('-alpha', i / 20)
                    time.sleep(0.05)
            except Exception as e:
                print(f"Error during fade-in: {e}")
        Thread(target=fade).start()

    def remind_again(self):
        """
        Logic for reminding again. For now, it just closes the popup.
        """
        try:
            minutes = float(self.remind_again_input.get())
            print(f"Reminder set again for {minutes} minutes.")
            self.close_window()
        except ValueError as e:
            print(f"Invalid input for remind again: {e}")

    def close_window(self):
        self.destroy()

def create_popup(message: str):
    app = ReminderPopup(message)
    app.mainloop()

@tool_decorator
def create_reminder(
    message: str,
    interval_type: Literal["minute", "hour", "day", "week"] = "minute",
    interval: (
        int
        | list[
            Literal[
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
        ]
        | str
        | None
    ) = None,
    specific_time: Optional[str] = None,
    for_user_or_ai: Literal["user", "ai"] = "user",
    once: bool = False,
) -> str:
    """
    Use this Tool for creating reminders for the user or AI/you.
    If the reminder is for the User, it will display a popup with the reminder message.
    If the reminder is for the AI, it will call the with the reminder message.

    Parameters:
    - message (str): The reminder message to display.
    - interval_type (Literal): Defines the type of interval ('minute', 'hour', 'day', 'week').
    - interval (Union[int, list, str, None]): The value of the interval:
      - For 'minute' or 'hour': specify an integer (e.g., 2 for every 2 minutes).
      - For 'day': specify an integer for days between triggers.
      - For 'week': specify a list of days (e.g., ['monday', 'wednesday']).
    - specific_time (Optional[str]): The time in "HH:MM" format when the reminder should trigger (used for 'day', 'week').
    - for_user_or_ai (Literal): Specify whether the reminder is for the user or the AI. Default is 'user'.
    - once (bool): If True, the reminder will trigger only once. Default is False.
    Returns String: The ID of the reminder job.
    Examples:
    - create_reminder("Drink water", interval_type="minute", interval=30)
    - create_reminder("Take a break", interval_type="hour", interval=1)
    - create_reminder("Go for a walk", interval_type="day", interval=2, specific_time="10:00")
    - create_reminder("Weekly meeting", interval_type="week", interval=["monday", "wednesday"], specific_time="15:00")
    - create_reminder("Meeting", interval_type="day", interval=1, specific_time="10:00", once=True)
    """
    if for_user_or_ai == "ai":
        call_routine(
            reason="state_change", type="reminder", message=message
        )  # AI is called directly

    reminder = Reminder(message, once)

    # Schedule logic
    if interval_type == "minute" and interval:
        job = (
            schedule.every(int(interval))
            .minutes.do(reminder)
            .tag("once" if once else "")
        )
        job.job_func.func.id = hash(reminder)
    elif interval_type == "hour" and interval:
        job = (
            schedule.every(int(interval)).hours.do(reminder).tag("once" if once else "")
        )
        job.job_func.func.id = hash(reminder)
    elif interval_type == "day":
        if specific_time:
            job = (
                schedule.every()
                .day.at(specific_time)
                .do(reminder)
                .tag("once" if once else "")
            )
            job.job_func.func.id = hash(reminder)
        elif interval:
            job = schedule.every(interval).days.do(reminder).tag("once" if once else "")
            job.job_func.func.id = hash(reminder)
    elif interval_type == "week" and isinstance(interval, list):
        for day in interval:
            job = (
                schedule.every()
                .__getattribute__(day)
                .at(specific_time)
                .do(reminder)
                .tag("once" if once else "")
            )
            job.job_func.func.id = hash(reminder)
    else:
        raise ValueError("Invalid interval or missing specific time.")

    return job.job_func.func.id


# Function to save the schedule jobs to a file
def save_jobs() -> None:
    """
    Save the scheduled jobs to a file using pickle.
    """
    with open("reminders.pkl", "wb") as f:
        pickle.dump(schedule.default_scheduler, f)


# Function to load the schedule jobs from a file
def load_jobs() -> None:
    """
    Load the scheduled jobs from a file using pickle, if it exists.
    """
    if os.path.exists("reminders.pkl"):
        with open("reminders.pkl", "rb") as f:
            schedule.default_scheduler = pickle.load(f)


# Function to run the reminders
def run_reminders() -> None:
    """
    Function to keep running the scheduled reminders and save them on exit.
    """
    load_jobs()  # Load reminders on startup

    while True:
        schedule.run_pending()
        time.sleep(1)


def get_reminders() -> list[str]:
    """
    Get the list of scheduled reminders in a clean, human-readable format.

    Returns:
    - A list of strings, each containing the formatted reminder details.
    """
    reminders = []

    for job in schedule.get_jobs():
        once = "Yes" if "once" in job.tags else "No"

        # Skip "Last Run" if the job is scheduled to run once
        last_run = (
            job.last_run.strftime("%Y-%m-%d %H:%M:%S")
            if job.last_run and once == "No"
            else ""
        )
        frequency = ""

        # Handling different scheduling scenarios
        if job.unit == "seconds":
            frequency = f"Runs every {job.interval} seconds"
        elif job.unit == "minutes":
            frequency = f"Runs every {job.interval} minutes"
        elif job.unit == "hours":
            frequency = f"Runs every {job.interval} hours"
        elif job.unit == "days" and job.at_time:
            frequency = f"Runs every day at {job.at_time.strftime('%H:%M:%S')}"
        elif job.unit == "days":
            frequency = f"Runs every {job.interval} days"
        elif job.unit == "weeks" and job.start_day:
            frequency = (
                f"Runs every {job.start_day} at {job.at_time.strftime('%H:%M:%S')}"
                if job.at_time
                else f"Runs every {job.start_day}"
            )
        else:
            frequency = f"Runs every {job.interval} {job.unit}"

        reminder = (
            f"Reminder: Message: {job.job_func.func.message}, Once: {once}, "
            f"{f'Last Run: {last_run}, ' if last_run else ''}"
            f"Schedule: {frequency}, ID: {job.job_func.func.id}, "
            f"{'Skip Next: Yes, ' if job.job_func.func.skip_next else ''}"
            f"{'Re-Remind: Yes' if job.job_func.func.re_remind else ''}"
        ).strip()

        reminders.append(reminder)
    return reminders


@tool_decorator
def cancel_reminder(
    reminder_id: str, forever_or_next: Literal["forever", "next"] = "forever"
) -> str:
    """
    Use this tool to Cancel a scheduled reminder by its ID.

    Parameters:
    - reminder_id (str): The ID of the reminder to cancel.
    - forever_or_next (Literal): Specify whether to cancel the reminder forever or only the next occurrence. Default is 'forever'.
    Returns:
    - String: The status message after cancelling the reminder.
    Examples:
    - cancel_reminder("12345")
    - cancel_reminder("12345", forever_or_next="next")
    """
    for job in schedule.jobs:
        if job.job_func.func.id == reminder_id:
            if forever_or_next == "forever":
                schedule.cancel_job(job)
                return f"Reminder with ID {reminder_id} has been cancelled forever."
            elif forever_or_next == "next":
                job.job_func.func.skip_next = True
                return f"Next occurrence of reminder with ID {reminder_id} has been cancelled."
            else:
                raise ValueError("Invalid value for 'forever_or_next'.")
    return f"Reminder with ID {reminder_id} not found, May have already been cancelled or expired."
