import google.generativeai as genai
import openai
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Text
from tkinter.font import Font
from datetime import datetime
import os
import yaml
import time
import json
import glob
import requests
import subprocess
import anthropic
import threading
from queue import Queue

class APIConfig:
    """
    A class to create a configuration window for API settings.
    """
    def __init__(self, parent, config_data, save_callback):
        self.window = tk.Toplevel(parent)
        self.window.title("API Configuration")
        self.config_data = config_data
        self.save_callback = save_callback
        self.window.geometry("600x500")  # Increased height to accommodate new fields
        self.window.resizable(False, False)

        self.provider_frame = ttk.LabelFrame(self.window, text="API Provider")
        self.provider_frame.pack(padx=10, pady=5, fill="x")

        self.providers = ["Google Gemini", "OpenAI", "Ollama", "OpenAI Compatible", "xAI Grok", "Anthropic Claude"]
        self.selected_provider = tk.StringVar(value=self.config_data.get("active_provider", "Google Gemini"))

        self.provider_dropdown = ttk.Combobox(self.provider_frame, textvariable=self.selected_provider, values=self.providers, state="readonly", width=40)
        self.provider_dropdown.pack(padx=10, pady=10)
        self.provider_dropdown.bind("<<ComboboxSelected>>", self.update_parameter_fields)

        self.params_frame = ttk.LabelFrame(self.window, text="Provider Parameters")
        self.params_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.api_key_var = tk.StringVar()
        self.base_url_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.system_prompt_var = tk.StringVar()
        self.temperature_var = tk.DoubleVar()

        api_key_frame = ttk.Frame(self.params_frame)
        api_key_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(api_key_frame, text="API Key:", width=15).pack(side=tk.LEFT)
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)

        base_url_frame = ttk.Frame(self.params_frame)
        base_url_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(base_url_frame, text="Base URL:", width=15).pack(side=tk.LEFT)
        self.base_url_entry = ttk.Entry(base_url_frame, textvariable=self.base_url_var, width=50)
        self.base_url_entry.pack(side=tk.LEFT, padx=5)

        model_frame = ttk.Frame(self.params_frame)
        model_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(model_frame, text="Model:", width=15).pack(side=tk.LEFT)
        self.model_entry = ttk.Entry(model_frame, textvariable=self.model_var, width=50)
        self.model_entry.pack(side=tk.LEFT, padx=5)

        system_prompt_frame = ttk.Frame(self.params_frame)
        system_prompt_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(system_prompt_frame, text="System Prompt:", width=15).pack(side=tk.LEFT)
        self.system_prompt_entry = ttk.Entry(system_prompt_frame, textvariable=self.system_prompt_var, width=50)
        self.system_prompt_entry.pack(side=tk.LEFT, padx=5)

        temperature_frame = ttk.Frame(self.params_frame)
        temperature_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(temperature_frame, text="Temperature:", width=15).pack(side=tk.LEFT)
        self.temperature_scale = ttk.Scale(temperature_frame, from_=0.0, to=1.0, variable=self.temperature_var, orient="horizontal")
        self.temperature_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

        self.active_var = tk.BooleanVar(value=True)
        self.active_check = ttk.Checkbutton(self.params_frame, text="Set as Active Provider", variable=self.active_var)
        self.active_check.pack(pady=10)

        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(padx=10, pady=10)
        ttk.Button(self.button_frame, text="Save", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="Cancel", command=self.window.destroy, width=15).pack(side=tk.LEFT, padx=5)

        self.load_current_config()

    def load_current_config(self):
        provider = self.selected_provider.get()
        provider_config = self.config_data.get(provider, {})
        self.api_key_var.set(provider_config.get("api_key", ""))
        self.base_url_var.set(provider_config.get("base_url", ""))
        self.model_var.set(provider_config.get("model", ""))
        self.system_prompt_var.set(provider_config.get("system_prompt", "You are a helpful assistant."))
        self.temperature_var.set(provider_config.get("temperature", 0.7))

    def update_parameter_fields(self, event=None):
        self.load_current_config()

    def save_config(self):
        provider = self.selected_provider.get()
        if self.active_var.get():
            self.config_data["active_provider"] = provider
        self.config_data[provider] = {
            "api_key": self.api_key_var.get(),
            "base_url": self.base_url_var.get(),
            "model": self.model_var.get(),
            "system_prompt": self.system_prompt_var.get(),
            "temperature": self.temperature_var.get()
        }
        self.save_callback(self.config_data)
        messagebox.showinfo("Success", f"{provider} configuration saved successfully!")
        self.window.destroy()

class ChatApplication:
    """
    A class to manage the main chat application.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-API Chat")

        # Color Palette
        self.left_bg = "#203354"
        self.left_text = "#E5E7EB"
        self.button_bg = "#38B2AC"
        self.button_text = "#FFFFFF"
        self.right_bg = "#F6F9FC"
        self.user_msg_bg = "#B2D8D8"
        self.ai_msg_bg = "#E3E4FA"
        self.right_text = "#1A202C"
        self.highlight_color = "#FF6F61"

        # Load configuration
        self.load_config()

        # Create Menu Bar
        self.create_menu_bar()

        # Session Frame
        self.create_session_frame()

        # Chat Frame
        self.create_chat_frame()

        # Initialize sessions and chat history
        self.sessions = {}
        self.current_session = None
        self.conversation_history = []
        self.log_dir = "chat_logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.load_previous_sessions()
        if not self.sessions:
            self.new_session()

        # Initialize API
        self.initialize_api()
        
        # Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_text)

        # File Attachments Variables
        self.attached_files = {} # Dictionary to store file attachments for session {session_name: {"file_path": <file_path>, "file_name":<file_name>, "file_content":<bytes>}}
        self.file_counter = 0 # A counter for each attachment

        # Font styles for message formatting
        self.bold_font = Font(weight="bold")
        self.italic_font = Font(slant="italic")
        self.underline_font = Font(underline=True)

        # Message Queue
        self.message_queue = Queue()
        self.processing_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.processing_thread.start()

    def create_menu_bar(self):
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Export Chat", command=self.export_chat)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="API Configuration", command=self.show_api_config)

    def create_session_frame(self):
        self.session_frame = tk.Frame(self.root, width=200, bg=self.left_bg)
        self.session_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.session_label = tk.Label(self.session_frame, text="Sessions", bg=self.left_bg, fg=self.left_text, font=("Arial", 12, "bold"))
        self.session_label.pack(pady=10)

        self.session_listbox = tk.Listbox(self.session_frame, bg=self.left_bg, fg=self.left_text, selectbackground=self.highlight_color, selectforeground=self.left_text)
        self.session_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.session_listbox.bind("<Double-Button-1>", self.load_selected_session)

        self.new_session_button = tk.Button(self.session_frame, text="New Session", bg=self.button_bg, fg=self.button_text, command=self.new_session)
        self.new_session_button.pack(pady=5)

        self.delete_session_button = tk.Button(self.session_frame, text="Delete Session", bg=self.button_bg, fg=self.button_text, command=self.delete_session)
        self.delete_session_button.pack(pady=5)

    def create_chat_frame(self):
        self.chat_frame = tk.Frame(self.root, bg=self.right_bg)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.api_label = tk.Label(self.chat_frame, text="Current API: None", bg=self.right_bg, fg=self.right_text, font=("Arial", 10, "italic"))
        self.api_label.pack(pady=5)

        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, font=("Arial", 10), bg=self.right_bg, fg=self.right_text)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.bind("<Key>", lambda e: "break")  # Disable direct editing
        self.chat_display.bind("<Control-c>", self.copy_text)  # Allow copy
        self.chat_display.tag_configure("sel", background=self.right_text, foreground=self.right_bg)
        self.chat_display.bind("<ButtonRelease-1>", self.on_select) # Handle selection with mouse
        self.chat_display.bind("<Button-3>", self.show_context_menu) # Bind right-click to show context menu

        self.message_entry = Text(self.chat_frame, font=("Arial", 12), wrap=tk.WORD, height=3, bg=self.right_bg, fg=self.right_text)
        self.message_entry.pack(fill=tk.X, padx=5, pady=5)
        self.message_entry.bind("<Return>", self.send_message)
        self.message_entry.bind("<Control-b>", self.toggle_bold)
        self.message_entry.bind("<Control-i>", self.toggle_italic)
        self.message_entry.bind("<Control-u>", self.toggle_underline)

        self.button_frame = tk.Frame(self.chat_frame, bg=self.right_bg)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.send_button = tk.Button(self.button_frame, text="Send", bg=self.button_bg, fg=self.button_text, command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.attach_button = tk.Button(self.button_frame, text="Attach", bg=self.button_bg, fg=self.button_text, command=self.attach_file)
        self.attach_button.pack(side=tk.LEFT, padx=5)

        self.emoji_button = tk.Button(self.button_frame, text="😊 Emoji", bg=self.button_bg, fg=self.button_text, command=self.insert_emoji)
        self.emoji_button.pack(side=tk.LEFT, padx=5)

    def load_config(self):
         """Loads the configuration from config.yaml or uses default values"""
         default_config = {
             "active_provider": "Google Gemini",
             "Google Gemini": {"api_key": "", "model": "gemini-pro", "system_prompt": "You are a helpful assistant.", "temperature": 0.7},
             "OpenAI": {"api_key": "", "model": "gpt-3.5-turbo", "system_prompt": "You are a helpful assistant.", "temperature": 0.7},
             "Ollama": {"ollama_model": "llama3.1:latest"},
             "OpenAI Compatible": {"api_key": "", "base_url": "", "model": "gpt-3.5-turbo", "system_prompt": "You are a helpful assistant.", "temperature": 0.7},
             "xAI Grok": {"api_key": "", "base_url": "https://api.x.ai", "model": "grok-1", "system_prompt": "You are a helpful assistant.", "temperature": 0.7},
             "Anthropic Claude": {"api_key": "", "model": "claude-3-opus-20240229", "system_prompt": "You are a helpful assistant.", "temperature": 0.7}

         }
         try:
             with open("config.yaml", "r") as file:
                 self.config = yaml.safe_load(file) or default_config
         except FileNotFoundError:
             self.config = default_config
             self.save_config()

    def save_config(self):
         """Saves the current configuration to config.yaml"""
         with open("config.yaml", "w") as file:
             yaml.dump(self.config, file)

    def show_api_config(self):
        """Opens the API configuration window"""
        APIConfig(self.root, self.config, self.save_and_reload_config)

    def save_and_reload_config(self, new_config):
        """Saves the config and reinitializes the API."""
        self.config = new_config
        self.save_config()
        self.initialize_api()
        self.update_api_label()

    def update_api_label(self):
        """Updates the API label in the chat window"""
        provider = self.config.get("active_provider", "None")
        self.api_label.config(text=f"Current API: {provider}")

    def initialize_api(self):
         """Initializes the API based on the active provider."""
         provider = self.config.get("active_provider", "")
         if not provider:
             return
         provider_config = self.config.get(provider, {})
         try:
             if provider == "Google Gemini":
                 genai.configure(api_key=provider_config.get("api_key", ""))
                 self.model_instance = genai.GenerativeModel(provider_config.get("model", "gemini-pro"))
             elif provider in ["OpenAI", "OpenAI Compatible"]:
                 openai.api_key = provider_config.get("api_key", "")
                 if provider == "OpenAI Compatible":
                     openai.base_url = provider_config.get("base_url", "")
             elif provider == "Anthropic Claude":
                  anthropic.api_key = provider_config.get("api_key", "")
                  self.model_instance = anthropic.Client()
             elif provider == "xAI Grok":
                   url = provider_config.get("base_url", "")
                   if url and "https://api.x.ai" not in url:
                      messagebox.showerror("Error", "Grok Base URL must point to https://api.x.ai.")
                      return
             elif provider == "Ollama":
                  self.ollama_model_name = provider_config.get("ollama_model", "llama3.1:latest")
                  self.ollama_command = ["ollama", "run", self.ollama_model_name]
             self.update_api_label()
         except Exception as e:
             messagebox.showerror("API Initialization Error", str(e))

    def export_chat(self):
        """Exports the chat log to a text file."""
        if not self.current_session:
            messagebox.showwarning("Warning", "No active session to export.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    for sender, message, timestamp in self.sessions[self.current_session]:
                        file.write(f"{timestamp} {sender}: {message}\n")
                    if self.attached_files.get(self.current_session):
                        file.write(f"\n\nAttached Files:\n")
                        for file_index, file_info in self.attached_files[self.current_session].items():
                             file.write(f"  {file_index}. {file_info['file_name']}\n")
                messagebox.showinfo("Success", "Chat exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chat: {str(e)}")

    def new_session(self):
        """Creates a new chat session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"Session_{timestamp}"
        self.sessions[session_name] = []
        self.current_session = session_name
        self.conversation_history = []
        self.update_session_list()
        messagebox.showinfo("New Session", f"Session '{session_name}' created.")
        self.update_chat_display()
        self.attached_files[self.current_session] = {} #clear existing attachments

    def delete_session(self):
        """Deletes the selected chat session."""
        selected_session = self.session_listbox.get(tk.ACTIVE)
        if not selected_session:
            messagebox.showwarning("Error", "Please select a session to delete.")
            return
        if selected_session in self.sessions:
            del self.sessions[selected_session]
            if self.attached_files.get(selected_session):
                del self.attached_files[selected_session]
        log_file = os.path.join(self.log_dir, f"{selected_session}.json")
        if os.path.exists(log_file):
            os.remove(log_file)
        self.current_session = None
        self.update_session_list()
        self.conversation_history = []
        self.update_chat_display()
        messagebox.showinfo("Session Deleted", f"Session '{selected_session}' deleted.")

    def send_message(self, event=None):
         """Sends the user's message to the AI and updates chat display."""
         message = self.message_entry.get("1.0", tk.END).strip()
         if not message:
            return
         if self.current_session is None:
             messagebox.showerror("Error","Please create a new session or select an existing one first.")
             return
         timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
         self.sessions[self.current_session].append(("You", message, timestamp))
         self.conversation_history.append({"role": "user", "parts": [message]})
         self.message_entry.delete("1.0", tk.END)
         self.update_chat_display()
         self.message_queue.put(("generate_response", {"user_message": message}))

    def process_messages(self):
        while True:
            try:
                task, data = self.message_queue.get()
                if task == "generate_response":
                    self.generate_ai_response(data["user_message"])
                self.message_queue.task_done()
            except Exception as e:
                messagebox.showerror("Message Processing Error", f"Error processing message queue: {e}")

    def generate_ai_response(self, user_message):
         """Generates the AI's response based on the active API provider."""
         max_retries = 3
         retry_delay = 2
         ai_message = ""
         for attempt in range(max_retries):
             try:
                 provider = self.config.get("active_provider", "")
                 provider_config = self.config.get(provider, {})
                 if provider == "Google Gemini":
                      response = self.model_instance.generate_content(self.conversation_history)
                      ai_message = response.text.strip()
                 elif provider in ["OpenAI", "OpenAI Compatible"]:
                      messages = []
                      system_prompt = provider_config.get("system_prompt", "You are a helpful assistant.")
                      messages.append({"role": "system", "content": system_prompt})

                      for msg in self.conversation_history:
                          if msg["role"] == "user":
                             messages.append({"role": "user", "content": msg["parts"][0]})
                          elif msg["role"] == "model":
                             messages.append({"role":"assistant", "content": msg["parts"][0]})
                      response = openai.chat.completions.create(
                         model=provider_config.get("model", "gpt-3.5-turbo"),
                         messages=messages,
                         temperature=provider_config.get("temperature", 0.7)
                     )
                      ai_message = response.choices[0].message.content.strip()

                 elif provider == "Anthropic Claude":
                     response = self.model_instance.completions.create(
                          model=provider_config.get("model", "claude-3-opus-20240229"),
                          max_tokens=10000,
                          prompt=self.construct_prompt(),
                     )
                     ai_message = response.completion.strip()
                 elif provider == "xAI Grok":
                      url = provider_config.get("base_url", "") + "/chat/completions"
                      headers = {
                         "Content-Type": "application/json",
                         "Authorization": f"Bearer {provider_config.get('api_key', '')}"
                      }
                      messages = []
                      system_prompt = provider_config.get("system_prompt", "You are a helpful assistant.")
                      messages.append({"role": "system", "content": system_prompt})
                      for msg in self.conversation_history:
                          if msg["role"] == "user":
                             messages.append({"role": "user", "content": msg["parts"][0]})
                          elif msg["role"] == "model":
                             messages.append({"role":"assistant", "content": msg["parts"][0]})

                      data = {
                         "messages": messages,
                         "model": provider_config.get("model", "grok-1"),
                         "temperature": provider_config.get("temperature", 0.7)
                      }
                      response = requests.post(url, headers=headers, json=data)
                      response.raise_for_status() # Raise an exception for bad responses
                      ai_message = response.json()['choices'][0]['message']['content'].strip()
                 elif provider == "Ollama":
                    process = subprocess.Popen(self.ollama_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate(input=self.construct_prompt())
                    if stderr:
                        raise Exception(f"Ollama Error:{stderr}")
                    ai_message = stdout.strip()
                 break
             except requests.exceptions.RequestException as e:
                if attempt < max_retries -1 and "429" in str(e):
                    time.sleep(retry_delay)
                else:
                    ai_message = f"API request failed: {e}"

             except Exception as e:
                  if attempt < max_retries - 1:
                      time.sleep(retry_delay)
                  else:
                     ai_message = f"Error generating response: {str(e)}"

         timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
         self.sessions[self.current_session].append(("AI", ai_message, timestamp))
         self.conversation_history.append({"role": "model", "parts": [ai_message]})
         self.root.after(0, self.update_chat_display) # Use root.after to update the UI
         self.save_session()

    def construct_prompt(self):
        prompt = ""
        provider = self.config.get("active_provider", "")
        provider_config = self.config.get(provider, {})

        if provider in ["OpenAI", "OpenAI Compatible", "xAI Grok"]:
            system_prompt = provider_config.get("system_prompt", "You are a helpful assistant.")
            prompt += f"System: {system_prompt}\n"
            for msg in self.conversation_history:
               if msg["role"] == "user":
                  prompt += f"User: {msg['parts'][0]}\n"
               elif msg["role"] == "model":
                  prompt += f"Assistant: {msg['parts'][0]}\n"
        elif provider == "Anthropic Claude":
           system_prompt = provider_config.get("system_prompt", "You are a helpful assistant.")
           prompt += f"{system_prompt}\n\n"
           for msg in self.conversation_history:
              if msg["role"] == "user":
                 prompt += f"Human: {msg['parts'][0]}\n"
              elif msg["role"] == "model":
                 prompt += f"Assistant: {msg['parts'][0]}\n"
        elif provider == "Ollama":
            system_prompt = provider_config.get("system_prompt", "You are a helpful assistant.")
            prompt += f"{system_prompt}\n"
            for msg in self.conversation_history:
               if msg["role"] == "user":
                  prompt += f"User: {msg['parts'][0]}\n"
               elif msg["role"] == "model":
                  prompt += f"Assistant: {msg['parts'][0]}\n"
        else:
            for msg in self.conversation_history:
               if msg["role"] == "user":
                   prompt += f"{msg['parts'][0]}\n"
               elif msg["role"] == "model":
                   prompt += f"{msg['parts'][0]}\n"
        return prompt

    def update_session_list(self):
        """Updates the list of sessions in the left panel."""
        self.session_listbox.delete(0, tk.END)
        for session in self.sessions:
            self.session_listbox.insert(tk.END, session)

    def load_selected_session(self, event):
         """Loads the selected chat session into the chat display."""
         selected_session = self.session_listbox.get(tk.ACTIVE)
         if selected_session:
            self.current_session = selected_session
            self.conversation_history = []
            for sender, message, timestamp in self.sessions[self.current_session]:
                if sender == "You":
                     self.conversation_history.append({"role":"user", "parts":[message]})
                elif sender == "AI":
                    self.conversation_history.append({"role":"model", "parts":[message]})
            self.update_chat_display()
            messagebox.showinfo("Session Loaded", f"Session '{selected_session}' loaded successfully.")

    def update_chat_display(self):
        """Updates the chat display with the latest messages."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        if self.current_session:
            for sender, message, timestamp in self.sessions[self.current_session]:
                 if sender == "You":
                      self.add_formatted_message(sender, message, timestamp, self.user_msg_bg)
                 elif sender == "AI":
                      self.add_formatted_message(sender, message, timestamp, self.ai_msg_bg)

            if self.attached_files.get(self.current_session):
                 self.chat_display.insert(tk.END, "\n\nAttached Files:\n")
                 for file_index, file_info in self.attached_files[self.current_session].items():
                       self.chat_display.insert(tk.END, f"  {file_index}. {file_info['file_name']}\n")
        self.chat_display.config(state=tk.DISABLED)

    def add_formatted_message(self, sender, message, timestamp, bg_color):
        """Adds a formatted message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{timestamp} {sender}: ", "bold")
        self.add_text_with_formatting(message)
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)

    def add_text_with_formatting(self, text):
        """Adds text to chat display with formatting."""
        # Handle bold text: *bold*
        parts = text.split('*')
        for i, part in enumerate(parts):
            if i % 2 == 0:  # Regular text
                self.chat_display.insert(tk.END, part)
            else:  # Bold text
                self.chat_display.insert(tk.END, part, "bold")
        
        # Configure tags
        self.chat_display.tag_configure("bold", font=self.bold_font)
        self.chat_display.tag_configure("italic", font=self.italic_font)
        self.chat_display.tag_configure("underline", font=self.underline_font)

    def toggle_bold(self, event=None):
        """Toggle bold formatting at cursor position"""
        try:
            selection = self.message_entry.tag_ranges(tk.SEL)
            if selection:
                start, end = selection
                text = self.message_entry.get(start, end)
                self.message_entry.delete(start, end)
                self.message_entry.insert(start, f"*{text}*")
        except tk.TclError:
            pass
        return "break"

    def toggle_italic(self, event=None):
        """Toggle italic formatting at cursor position"""
        try:
            selection = self.message_entry.tag_ranges(tk.SEL)
            if selection:
                start, end = selection
                text = self.message_entry.get(start, end)
                self.message_entry.delete(start, end)
                self.message_entry.insert(start, f"_{text}_")
        except tk.TclError:
            pass
        return "break"

    def toggle_underline(self, event=None):
        """Toggle underline formatting at cursor position"""
        try:
            selection = self.message_entry.tag_ranges(tk.SEL)
            if selection:
                start, end = selection
                text = self.message_entry.get(start, end)
                self.message_entry.delete(start, end)
                self.message_entry.insert(start, f"~{text}~")
        except tk.TclError:
            pass
        return "break"

    def insert_emoji(self):
        """Opens emoji selector window"""
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("Select Emoji")
        emoji_window.geometry("300x200")
        
        emojis = ["😊", "😂", "👍", "❤️", "🎉", "😎", "🤔", "👋", "✨", "🔥"]
        
        def add_emoji(emoji):
            self.message_entry.insert(tk.INSERT, emoji)
            emoji_window.destroy()
        
        for i, emoji in enumerate(emojis):
            btn = tk.Button(emoji_window, text=emoji, font=("Arial", 20),
                           command=lambda e=emoji: add_emoji(e))
            btn.grid(row=i//5, column=i%5, padx=5, pady=5)

    def attach_file(self):
        """Handles file attachment"""
        if not self.current_session:
            messagebox.showerror("Error", "Please select or create a session first")
            return
            
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                
                # Check file size (e.g., limit to 10MB)
                if file_size > 10 * 1024 * 1024:
                    messagebox.showerror("Error", "File size exceeds 10MB limit")
                    return
                    
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    
                if self.current_session not in self.attached_files:
                    self.attached_files[self.current_session] = {}
                    
                self.file_counter += 1
                self.attached_files[self.current_session][self.file_counter] = {
                    'file_path': file_path,
                    'file_name': file_name,
                    'file_content': file_content
                }
                
                # Add attachment message to chat
                timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
                self.sessions[self.current_session].append(
                    ("System", f"File attached: {file_name}", timestamp)
                )
                self.update_chat_display()
                self.save_session()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to attach file: {str(e)}")

    def save_session(self):
        """Saves the current session data."""
        if self.current_session:
            log_file = os.path.join(self.log_dir, f"{self.current_session}.json")
            with open(log_file, "w") as f:
                json.dump({
                   "chat_log": self.sessions[self.current_session],
                   "conversation_history": self.conversation_history,
                   "attached_files": self.attached_files.get(self.current_session, {})
                     }, f, indent=4)

    def load_previous_sessions(self):
         """Loads the previously saved sessions."""
         log_files = glob.glob(os.path.join(self.log_dir, "*.json"))
         log_files.sort(key=os.path.getmtime, reverse=True)
         for log_file in log_files:
             session_name = os.path.splitext(os.path.basename(log_file))[0]
             try:
                 with open(log_file, "r") as f:
                      data = json.load(f)
                      self.sessions[session_name] = data["chat_log"]
                      if "attached_files" in data:
                          self.attached_files[session_name] = data["attached_files"]
             except:
                 print(f"Failed to load log file {log_file}")

         self.update_session_list()

    def on_select(self, event):
        """Handles the selection of text in the chat display."""
        try:
            self.chat_display.tag_remove("sel", "1.0", tk.END)
            if self.chat_display.tag_ranges("sel"):
                 sel_start = self.chat_display.index("sel.first")
                 sel_end = self.chat_display.index("sel.last")
                 self.chat_display.tag_remove("sel", sel_start, sel_end)

            selected_text = self.chat_display.selection_get()
            if selected_text:
                sel_start = self.chat_display.index(tk.SEL_FIRST)
                sel_end = self.chat_display.index(tk.SEL_LAST)
                self.chat_display.tag_add("sel", sel_start, sel_end)
        except tk.TclError:
            pass

    def copy_text(self, event=None):
         """Copies the selected text to the clipboard."""
         try:
             selected_text = self.chat_display.selection_get()
             self.root.clipboard_clear()
             self.root.clipboard_append(selected_text)
         except tk.TclError:
             pass

    def show_context_menu(self, event):
        """Displays the right-click context menu."""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApplication(root)
    root.geometry("800x600")
    root.config(bg=app.right_bg)
    root.mainloop()

