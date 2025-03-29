import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
from datetime import datetime, timedelta
import threading
import sys
import os
import platform
import traceback  # Added for better error handling
if platform.system() == 'Windows':
    from subprocess import CREATE_NO_WINDOW

# Define a modern color scheme
COLORS = {
    "primary": "#1E88E5",       # Blue
    "secondary": "#7CB342",     # Green
    "accent": "#FFC107",        # Amber
    "warning": "#FF5722",       # Deep Orange
    "background": "#F5F5F5",    # Light grey
    "text": "#212121",          # Dark grey
    "light_text": "#757575",    # Medium grey
    "error": "#F44336"          # Red for errors
}

class ModernTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        # Get widget position
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create a toplevel window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background=COLORS["accent"],
                         foreground=COLORS["text"], relief="solid", borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=5, pady=2)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class CustomButton(tk.Canvas):
    def __init__(self, parent, text, command, width=120, height=40, bg_color=COLORS["primary"], hover_color=None, **kwargs):
        self.bg_color = bg_color
        self.hover_color = hover_color if hover_color else self._lighten_color(bg_color, 0.2)
        self.command = command
        self.text = text
        
        tk.Canvas.__init__(self, parent, width=width, height=height, 
                          bg=COLORS["background"], highlightthickness=0, **kwargs)
        
        self.rect_id = self.create_rectangle(0, 0, width, height, fill=bg_color, outline="")
        self.text_id = self.create_text(width//2, height//2, text=text, fill="white", font=("Segoe UI", 10, "bold"))
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _lighten_color(self, color, factor=0.2):
        # Convert hex to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Lighten
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_enter(self, event):
        self.itemconfig(self.rect_id, fill=self.hover_color)
    
    def _on_leave(self, event):
        self.itemconfig(self.rect_id, fill=self.bg_color)
    
    def _on_click(self, event):
        self.itemconfig(self.rect_id, fill=self._lighten_color(self.bg_color, -0.1))
    
    def _on_release(self, event):
        self.itemconfig(self.rect_id, fill=self.hover_color)
        if self.command:
            self.command()

class StenaInternetMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("KERRY the FERRY Internet Monitor")
        self.root.geometry("550x800")
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS["background"])
        
        # Configure style for Windows modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme for better color customization
        
        # Configure styles
        self.style.configure("TFrame", background=COLORS["background"])
        self.style.configure("TLabel", background=COLORS["background"], foreground=COLORS["text"])
        self.style.configure("TLabelframe", background=COLORS["background"], foreground=COLORS["primary"])
        self.style.configure("TLabelframe.Label", background=COLORS["background"], foreground=COLORS["primary"], font=("Segoe UI", 10, "bold"))
        self.style.configure("TEntry", fieldbackground="white", foreground=COLORS["text"])
        self.style.map("TButton", background=[("active", COLORS["primary"])], foreground=[("active", "white")])
        self.style.configure("Link.TLabel", background=COLORS["background"], foreground=COLORS["primary"], font=("Segoe UI", 8, "underline"))
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a container for all content including footer
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create footer frame for GitHub link
        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.pack(fill=tk.X, side=tk.BOTTOM, before=self.content_frame)
        
        # Add GitHub link to footer
        self.github_link = tk.Label(
            self.footer_frame,
            text="© Damiasroca",
            fg=COLORS["primary"],
            bg=COLORS["background"],
            cursor="hand2",
            font=("Segoe UI", 8, "underline")
        )
        self.github_link.pack(side=tk.RIGHT, padx=10, pady=2)
        self.github_link.bind("<Button-1>", self.open_github)
        
        # Info banner about username/password
        self.info_frame = ttk.Frame(self.content_frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.info_label = ttk.Label(
            self.info_frame, 
            text="Note: For Stena Line captive portal, the username and password are the same.",
            foreground=COLORS["primary"],
            font=("Segoe UI", 10, "italic")
        )
        self.info_label.pack(pady=5)
        
        # Create credentials frame
        self.creds_frame = ttk.LabelFrame(self.content_frame, text="Login Credentials", padding="5 5 5 5")
        self.creds_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create username and password fields
        ttk.Label(self.creds_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.username_var = tk.StringVar(value="")
        self.username_entry = ttk.Entry(self.creds_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.creds_frame, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.password_var = tk.StringVar(value="")
        self.password_entry = ttk.Entry(self.creds_frame, textvariable=self.password_var, show="*", width=20)
        self.password_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Create profile management
        self.profile_frame = ttk.LabelFrame(self.content_frame, text="Profile Management", padding="5 5 5 5")
        self.profile_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Profile selection
        self.profiles_frame = ttk.Frame(self.profile_frame)
        self.profiles_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.profiles_frame, text="Select Profile:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.profiles = self.load_profiles()
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(self.profiles_frame, textvariable=self.profile_var, width=20)
        self.profile_combo.grid(row=0, column=1, padx=5, pady=5)
        self.update_profile_list()
        
        self.profile_combo.bind("<<ComboboxSelected>>", self.load_selected_profile)
        
        # New profile creation
        self.new_profile_frame = ttk.Frame(self.profile_frame)
        self.new_profile_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.new_profile_frame, text="New Profile:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.profile_name_var = tk.StringVar()
        self.profile_name_entry = ttk.Entry(self.new_profile_frame, textvariable=self.profile_name_var, width=20)
        self.profile_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Buttons for profile management
        self.profile_buttons_frame = ttk.Frame(self.new_profile_frame)
        self.profile_buttons_frame.grid(row=0, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        self.save_profile_btn = CustomButton(
            self.profile_buttons_frame, "Save Profile", self.save_profile, 
            width=100, height=28, bg_color=COLORS["secondary"]
        )
        self.save_profile_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_profile_btn = CustomButton(
            self.profile_buttons_frame, "Delete Profile", self.delete_profile, 
            width=100, height=28, bg_color=COLORS["warning"]
        )
        self.delete_profile_btn.pack(side=tk.LEFT, padx=5)
        
        # Create action buttons frame
        self.buttons_frame = ttk.Frame(self.content_frame)
        self.buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # Create buttons with custom styling
        self.fetch_btn = CustomButton(
            self.buttons_frame, "Fetch Data/Connect", self.fetch_data, 
            width=140, height=35, bg_color=COLORS["primary"]
        )
        self.fetch_btn.pack(side=tk.LEFT, padx=10)
        
        self.save_btn = CustomButton(
            self.buttons_frame, "Save History", self.save_history, 
            width=120, height=35, bg_color=COLORS["secondary"]
        )
        self.save_btn.pack(side=tk.LEFT, padx=10)
        
        self.clear_btn = CustomButton(
            self.buttons_frame, "Clear Display", self.clear_output, 
            width=120, height=35, bg_color=COLORS["light_text"]
        )
        self.clear_btn.pack(side=tk.LEFT, padx=10)
        
        # Add tooltips to buttons
        ModernTooltip(self.fetch_btn, "Fetch your current internet usage data")
        ModernTooltip(self.save_btn, "Save current usage data to history file")
        ModernTooltip(self.clear_btn, "Clear the display area")
        
        # Create output text area
        self.output_frame = ttk.LabelFrame(self.content_frame, text="Internet Usage Information", padding="5 5 5 5")
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame, wrap=tk.WORD, 
            font=("Consolas", 10), 
            background="white", 
            foreground=COLORS["text"]
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for formatting
        self.output_text.tag_configure("title", foreground=COLORS["primary"], font=("Segoe UI", 12, "bold"))
        self.output_text.tag_configure("subtitle", foreground=COLORS["secondary"], font=("Segoe UI", 10, "bold"))
        self.output_text.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 10))
        self.output_text.tag_configure("error", foreground=COLORS["error"], font=("Segoe UI", 10, "bold"))
        self.output_text.tag_configure("error_details", foreground=COLORS["error"], font=("Consolas", 9))
        
        # Create status bar with colorful indicator
        self.status_frame = ttk.Frame(self.content_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_indicator = tk.Canvas(self.status_frame, width=15, height=15, background=COLORS["background"], highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=5)
        self.status_light = self.status_indicator.create_oval(2, 2, 13, 13, fill=COLORS["secondary"], outline="")
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Storage for fetched data
        self.current_data = None
        
        # Welcome message with colors
        self.display_welcome_message()
    
    def open_github(self, event=None):
        """Open the GitHub profile in the default web browser"""
        try:
            import webbrowser
            webbrowser.open("https://github.com/Damiasroca/kerry_network_monitor")
        except Exception as e:
            self.display_error(f"Failed to open GitHub link: {e}", traceback.format_exc())
    
    def display_welcome_message(self):
        self.output_text.tag_configure("title", foreground=COLORS["primary"], font=("Segoe UI", 12, "bold"))
        self.output_text.tag_configure("subtitle", foreground=COLORS["secondary"], font=("Segoe UI", 10, "bold"))
        self.output_text.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 10))
        
        self.output_text.insert(tk.END, "Welcome to KERRY the FERRY Internet Monitor!\n", "title")
        self.output_text.insert(tk.END, "\nThis tool helps you monitor your internet usage from Kerry's network.\n\n", "normal")
        self.output_text.insert(tk.END, "Getting Started:\n", "subtitle")
        self.output_text.insert(tk.END, "1. Enter your password\n", "normal")
        self.output_text.insert(tk.END, "2. Click 'Fetch Data/Connect' to check your usage\n", "normal")
        self.output_text.insert(tk.END, "3. Save profiles for easier access next time\n\n", "normal")
        self.output_text.insert(tk.END, "Ready to check your internet usage status!\n", "normal")
    
    def display_error(self, error_message, error_details=None):
        """Display an error message in the output text area with formatting"""
        self.output_text.insert(tk.END, f"ERROR: {error_message}\n", "error")
        
        if error_details:
            self.output_text.insert(tk.END, "\nError Details:\n", "subtitle")
            self.output_text.insert(tk.END, f"{error_details}\n", "error_details")
        
        self.output_text.see(tk.END)  # Scroll to see the error
    
    def load_profiles(self):
        try:
            if os.path.exists('profiles.json'):
                with open('profiles.json', 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            error_details = traceback.format_exc()
            self.root.after(0, lambda: self.display_error(f"Failed to load profiles: {e}", error_details))
            return {}
    
    def save_profiles(self):
        try:
            with open('profiles.json', 'w') as f:
                json.dump(self.profiles, f)
        except Exception as e:
            error_details = traceback.format_exc()
            self.display_error(f"Failed to save profiles: {e}", error_details)
    
    def update_profile_list(self):
        try:
            self.profile_combo['values'] = list(self.profiles.keys())
        except Exception as e:
            error_details = traceback.format_exc()
            self.display_error(f"Failed to update profile list: {e}", error_details)
    
    def load_selected_profile(self, event=None):
        try:
            profile_name = self.profile_var.get()
            if profile_name in self.profiles:
                profile = self.profiles[profile_name]
                self.username_var.set(profile.get('username', ''))
                self.password_var.set(profile.get('password', ''))
                self.set_status(f"Loaded profile: {profile_name}", "success")
        except Exception as e:
            error_details = traceback.format_exc()
            self.display_error(f"Failed to load profile: {e}", error_details)
    
    def save_profile(self):
        try:
            profile_name = self.profile_name_var.get().strip()
            if not profile_name:
                messagebox.showerror("Error", "Profile name cannot be empty")
                return
            
            self.profiles[profile_name] = {
                'username': self.username_var.get(),
                'password': self.password_var.get()
            }
            self.save_profiles()
            self.update_profile_list()
            self.profile_var.set(profile_name)
            self.profile_name_var.set('')
            self.set_status(f"Profile '{profile_name}' saved", "success")
        except Exception as e:
            error_details = traceback.format_exc()
            self.display_error(f"Failed to save profile: {e}", error_details)
    
    def delete_profile(self):
        try:
            profile_name = self.profile_var.get()
            if profile_name in self.profiles:
                del self.profiles[profile_name]
                self.save_profiles()
                self.update_profile_list()
                self.profile_var.set('')
                self.set_status(f"Profile '{profile_name}' deleted", "warning")
            else:
                messagebox.showerror("Error", "No profile selected")
        except Exception as e:
            error_details = traceback.format_exc()
            self.display_error(f"Failed to delete profile: {e}", error_details)
    
    def set_status(self, message, status_type="info"):
        self.status_var.set(message)
        
        if status_type == "success":
            self.status_indicator.itemconfig(self.status_light, fill=COLORS["secondary"])
        elif status_type == "warning":
            self.status_indicator.itemconfig(self.status_light, fill=COLORS["warning"])
        elif status_type == "error":
            self.status_indicator.itemconfig(self.status_light, fill=COLORS["error"])
        else:  # info
            self.status_indicator.itemconfig(self.status_light, fill=COLORS["primary"])
    
    def fetch_data(self):
        # Disable the button during fetch
        self.fetch_btn.configure(state=tk.DISABLED)
        self.set_status("Fetching data... Please wait.", "info")
        
        # Clear previous output and show fetching message
        self.clear_output()
        self.output_text.tag_configure("fetching", foreground=COLORS["primary"], font=("Segoe UI", 10, "italic"))
        self.output_text.insert(tk.END, "Fetching data... Please wait.\n", "fetching")
        
        # Start a new thread to fetch data
        threading.Thread(target=self._fetch_data_thread, daemon=True).start()
    
    def _fetch_data_thread(self):
        try:
            # Get credentials
            username = self.username_var.get()
            password = self.password_var.get()
        
            if not username or not password:
                self.root.after(0, lambda: messagebox.showerror("Error", "Username and password are required"))
                self.root.after(0, lambda: self.set_status("Error: Missing credentials", "error"))
                self.root.after(0, lambda: self.fetch_btn.configure(state=tk.NORMAL))
                return

            # Get the path to the bundled curl executable
            curl_executable = "curl"
            if getattr(sys, 'frozen', False):

                if platform.system() == 'Windows':
                    curl_executable = resource_path(os.path.join("bin", "curl.exe"))
                else:
                    curl_executable = resource_path(os.path.join("bin", "curl"))

            # Create curl command with the executable path
            curl_command = [
                curl_executable,  # Use the bundled curl or system curl
                "-k",   # Skip certificate validation
                "-s",   # Silent mode
                "-X", "POST",
                "https://internet.stenaline.com/portal_api.php",
                "-H", "Content-Type: application/x-www-form-urlencoded",
                "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "-d", f"action=authenticate&switch_package=true&login={username}&password={password}&policy_accept=true&private_policy_accept=false&from_ajax=true&wispr_mode=false"
            ]
        
            # Execute curl command - MODIFIED TO HIDE CONSOLE WINDOW
            # Check if we're on Windows and use the CREATE_NO_WINDOW flag
            if platform.system() == 'Windows':
                try:
                    result = subprocess.run(
                        curl_command, 
                        capture_output=True, 
                        text=True,
                        creationflags=CREATE_NO_WINDOW 
                    )
                except FileNotFoundError:
                    # Handle the case where curl is not installed
                    error_message = "CURL command not found. Make sure curl is installed and in your PATH."
                    self.root.after(0, lambda: self.clear_output())
                    self.root.after(0, lambda: self.display_error(error_message))
                    self.root.after(0, lambda: self.set_status("Error: CURL not found", "error"))
                    self.root.after(0, lambda: self.fetch_btn.configure(state=tk.NORMAL))
                    return
            else:
                # For non-Windows platforms, use the standard call
                try:
                    result = subprocess.run(curl_command, capture_output=True, text=True)
                except FileNotFoundError:
                    # Handle the case where curl is not installed
                    error_message = "CURL command not found. Make sure curl is installed and in your PATH."
                    self.root.after(0, lambda: self.clear_output())
                    self.root.after(0, lambda: self.display_error(error_message))
                    self.root.after(0, lambda: self.set_status("Error: CURL not found", "error"))
                    self.root.after(0, lambda: self.fetch_btn.configure(state=tk.NORMAL))
                    return
        
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    # Check if authentication was successful
                    if "user" in data and "consumedData" in data["user"]:
                        self.current_data = data
                        self.root.after(0, lambda: self.display_info(data))
                        self.root.after(0, lambda: self.set_status("Data fetched successfully", "success"))
                    elif "errorMsg" in data:
                        # Extract API error message if available
                        error_msg = data.get("errorMsg", "Authentication failed or no data returned")
                        self.root.after(0, lambda: self.clear_output())
                        self.root.after(0, lambda: self.display_error(f"API Error: {error_msg}", json.dumps(data, indent=2)))
                        self.root.after(0, lambda: self.set_status("Error: API returned an error", "error"))
                    elif "error" in data and data["error"].get("code") == "error_logon_volume-quota-reached-detail":
                        self.current_data = data
                        self.root.after(0, lambda: self.display_quota_reached_info(data))
                        self.root.after(0, lambda: self.set_status("Quota limit reached", "warning"))
                    else:
                        error_msg = "Authentication failed or no data returned"
                        self.root.after(0, lambda: self.clear_output())
                        self.root.after(0, lambda: self.display_error(error_msg, json.dumps(data, indent=2)))
                        self.root.after(0, lambda: self.set_status("Error: Authentication failed", "error"))
                except json.JSONDecodeError as je:
                    self.root.after(0, lambda: self.clear_output())
                    self.root.after(0, lambda: self.display_error(
                        "Error decoding JSON response", 
                        f"JSON Error: {str(je)}\n\nResponse Content:\n{result.stdout[:500]}...(truncated)"
                    ))
                    self.root.after(0, lambda: self.set_status("Error: Invalid response format", "error"))
            else:
                self.root.after(0, lambda: self.clear_output())
                self.root.after(0, lambda: self.display_error(
                    f"Curl command failed with exit code: {result.returncode}", 
                    f"STDERR: {result.stderr}\n\nSTDOUT: {result.stdout}"
                ))
                self.root.after(0, lambda: self.set_status("Error: Request failed", "error"))
        except Exception as e:
            # Get the full traceback for detailed error information
            error_traceback = traceback.format_exc()
            
            self.root.after(0, lambda: self.clear_output())
            self.root.after(0, lambda: self.display_error(
                f"Error executing curl command: {e}", 
                error_traceback
            ))
            self.root.after(0, lambda: self.set_status(f"Error: {str(e)[:50]}", "error"))
        finally:
            # Re-enable the button
            self.root.after(0, lambda: self.fetch_btn.configure(state=tk.NORMAL))
    
    def format_bytes(self, bytes_value):
        try:
            return f"{bytes_value / 1024 / 1024:.1f} MB"
        except (TypeError, ValueError) as e:
            # Handle type conversion errors
            self.display_error(f"Error formatting bytes: {e}", f"Value was: {bytes_value}")
            return "Error"
    
    def display_quota_reached_info(self, data):
        try:
            # Clear previous output
            self.clear_output()
            
            # Configure text tags for colorful display if not already configured
            self.output_text.tag_configure("header", foreground=COLORS["primary"], font=("Segoe UI", 12, "bold"))
            self.output_text.tag_configure("section", foreground=COLORS["secondary"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("label", foreground=COLORS["light_text"], font=("Segoe UI", 9))
            self.output_text.tag_configure("value", foreground=COLORS["text"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("warning", foreground=COLORS["warning"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("alert", foreground=COLORS["error"], font=("Segoe UI", 11, "bold"))
            self.output_text.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 10))
            self.output_text.tag_configure("footer", foreground=COLORS["light_text"], font=("Segoe UI", 8, "italic"))
            self.output_text.tag_configure("debug", foreground=COLORS["light_text"], font=("Consolas", 9))
            
            # Extract error data
            error_value = data.get("error", {}).get("value", {})
            
            if not error_value:
                self.display_error("Missing quota details in API response", json.dumps(data, indent=2))
                return
            
            try:
                consumed_up = int(error_value.get("consumedUp", 0))
                consumed_down = int(error_value.get("consumedDown", 0))
                threshold_up = int(error_value.get("thresoldUp", 0))
                
                # Handle negative threshold values
                threshold_down_raw = int(error_value.get("thresoldDown", 0))
                threshold_down = abs(threshold_down_raw) if threshold_down_raw < 0 else threshold_down_raw
                
                renew_timestamp = int(error_value.get("renewTimeStamp", 0))
                
                # Calculate total consumption
                total_consumed = consumed_up + consumed_down
                total_consumed_mb = total_consumed / (1024 * 1024)
                threshold_up_mb = threshold_up / (1024 * 1024)
            except (ValueError, TypeError) as e:
                # Handle conversion errors
                self.display_error(f"Invalid data format in quota-reached response: {e}", 
                                f"Data received: {json.dumps(error_value, indent=2)}")
                return
            
            # Calculate time remaining
            current_time = datetime.now().timestamp()
            time_remaining_seconds = renew_timestamp - current_time
            time_remaining = timedelta(seconds=max(0, time_remaining_seconds))
            
            # Display information with formatting
            self.output_text.insert(tk.END, "QUOTA LIMIT REACHED\n\n", "alert")
            
            # Display quota alert message
            self.output_text.insert(tk.END, "Your internet quota has been reached. You will have limited or no internet access until the renewal time.\n\n", "warning")
            
            # Data usage section
            self.output_text.insert(tk.END, "DATA USAGE\n", "section")
            
            self.output_text.insert(tk.END, "Download: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(consumed_down)}\n", "value")
            
            self.output_text.insert(tk.END, "Upload: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(consumed_up)}\n", "value")
            
            self.output_text.insert(tk.END, "Total Usage: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(consumed_up + consumed_down)}\n\n", "value")
            
            # Quota information section
            self.output_text.insert(tk.END, "QUOTA INFORMATION\n", "section")
        
            if total_consumed > threshold_up and threshold_up > 0:
                self.output_text.insert(tk.END, "Total Data Limit: ", "label")
                self.output_text.insert(tk.END, f"{self.format_bytes(threshold_up)}\n", "value")
                
                usage_percentage = (total_consumed / threshold_up) * 100
                self.output_text.insert(tk.END, "Total Usage: ", "label")
                self.output_text.insert(tk.END, f"{usage_percentage:.1f}% ", "warning")
                
                # Calculate actual overage
                excess_mb = total_consumed_mb - threshold_up_mb
                if excess_mb > 0:
                    self.output_text.insert(tk.END, f"(Exceeded by {excess_mb:.1f} MB)\n", "warning")
                else:
                    self.output_text.insert(tk.END, "(Limit reached)\n", "warning")
            else:

                if threshold_up > 0:
                    self.output_text.insert(tk.END, "Upload Limit: ", "label")
                    self.output_text.insert(tk.END, f"{self.format_bytes(threshold_up)}\n", "value")
                    
                    upload_percentage = (consumed_up / threshold_up) * 100
                    self.output_text.insert(tk.END, "Upload Usage: ", "label")
                    self.output_text.insert(tk.END, f"{upload_percentage:.1f}% (Limit reached)\n", "warning")
            
            # Time information
            self.output_text.insert(tk.END, "\nTIME INFORMATION\n", "section")
            
            self.output_text.insert(tk.END, "Time until renewal: ", "label")
            self.output_text.insert(tk.END, f"{time_remaining.days} days, {time_remaining.seconds // 3600} hours, {(time_remaining.seconds % 3600) // 60} minutes\n", "value")
            
            renewal_time = datetime.fromtimestamp(renew_timestamp)
            self.output_text.insert(tk.END, "Renewal date: ", "label")
            self.output_text.insert(tk.END, f"{renewal_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n", "value")
            
            # Footer
            self.output_text.insert(tk.END, f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "footer")
            
            # Scroll to the top to see all information
            self.output_text.see(1.0)
            
        except Exception as e:
            # Get the full traceback for detailed error information
            error_traceback = traceback.format_exc()
            self.display_error(
                f"Error processing quota-reached data: {e}", 
                f"Traceback:\n{error_traceback}\n\nData received:\n{json.dumps(data, indent=2)[:500]}...(truncated)"
            )
    
    def display_info(self, data):
        if not data:
            self.output_text.insert(tk.END, "No data available\n")
            return
        
        try:
            # Clear previous output
            self.clear_output()
            
            # Configure text tags for colorful display
            self.output_text.tag_configure("header", foreground=COLORS["primary"], font=("Segoe UI", 12, "bold"))
            self.output_text.tag_configure("section", foreground=COLORS["secondary"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("label", foreground=COLORS["light_text"], font=("Segoe UI", 9))
            self.output_text.tag_configure("value", foreground=COLORS["text"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("warning", foreground=COLORS["warning"], font=("Segoe UI", 10, "bold"))
            self.output_text.tag_configure("normal", foreground=COLORS["text"], font=("Segoe UI", 10))
            self.output_text.tag_configure("footer", foreground=COLORS["light_text"], font=("Segoe UI", 8, "italic"))
            
            # Extract user consumption data
            consumed = data.get("user", {}).get("consumedData", {})
            
            if not consumed:
                self.display_error("Missing consumption data in API response", json.dumps(data, indent=2))
                return
            
            try:
                download_bytes = int(consumed.get("download", {}).get("value", 0))
                upload_bytes = int(consumed.get("upload", {}).get("value", 0))
            except (ValueError, TypeError) as e:
                # Handle conversion errors
                self.display_error(f"Invalid data format: {e}", f"Data received: {json.dumps(consumed, indent=2)}")
                return
            
            # Get quota information
            extra_data = consumed.get("extra", {}).get("value", [])
            quota_info = None
            for item in extra_data:
                if item.get("isSumQuota") and item.get("isDisconnectQuota"):
                    quota_info = item
                    break
            
            # Get time information
            try:
                renew_timestamp = int(consumed.get("renewTimestamp", {}).get("value", 0))
                current_timestamp = int(consumed.get("timestamp", {}).get("value", 0))
            except (ValueError, TypeError) as e:
                self.display_error(f"Invalid timestamp format: {e}", f"Data received: {json.dumps(consumed, indent=2)}")
                # Set default values to avoid further errors
                renew_timestamp = int(datetime.now().timestamp()) + 86400  # Default to 1 day
                current_timestamp = int(datetime.now().timestamp())
            
            # Calculate time remaining
            current_time = datetime.now().timestamp()
            time_remaining_seconds = renew_timestamp - current_time
            time_remaining = timedelta(seconds=max(0, time_remaining_seconds))
            
            # Display information with formatting
            self.output_text.insert(tk.END, "INTERNET USAGE SUMMARY\n\n", "header")
            
            # User info
            username = data.get('user', {}).get('login', {}).get('value', 'N/A')
            profile = data.get('user', {}).get('profile', {}).get('value', 'N/A')
            
            self.output_text.insert(tk.END, "User: ", "label")
            self.output_text.insert(tk.END, f"{username}\n", "value")
            
            self.output_text.insert(tk.END, "Profile: ", "label")
            self.output_text.insert(tk.END, f"{profile}\n\n", "value")
            
            # Data usage section
            self.output_text.insert(tk.END, "DATA USAGE\n", "section")
            
            self.output_text.insert(tk.END, "Download: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(download_bytes)}\n", "value")
            
            self.output_text.insert(tk.END, "Upload: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(upload_bytes)}\n", "value")
            
            self.output_text.insert(tk.END, "Total Usage: ", "label")
            self.output_text.insert(tk.END, f"{self.format_bytes(download_bytes + upload_bytes)}\n\n", "value")
            
            # Quota information
            if quota_info:
                try:
                    total_upload_quota = quota_info.get("total", {}).get("upload")
                    available_upload = quota_info.get("available", {}).get("upload")
                    
                    if total_upload_quota is not None:
                        self.output_text.insert(tk.END, "QUOTA INFORMATION\n", "section")
                        
                        self.output_text.insert(tk.END, "Total Traffic Quota: ", "label")
                        self.output_text.insert(tk.END, f"{self.format_bytes(total_upload_quota)}\n", "value")
                        
                        if available_upload is not None:
                            self.output_text.insert(tk.END, "Remaining: ", "label")
                            self.output_text.insert(tk.END, f"{self.format_bytes(available_upload)}\n", "value")
                            
                            usage_percentage = (total_upload_quota - available_upload) / total_upload_quota * 100
                            self.output_text.insert(tk.END, "Used: ", "label")
                            
                            # Use warning color if usage is high
                            if usage_percentage > 80:
                                self.output_text.insert(tk.END, f"{self.format_bytes(total_upload_quota - available_upload)} ({usage_percentage:.1f}%)\n\n", "warning")
                            else:
                                self.output_text.insert(tk.END, f"{self.format_bytes(total_upload_quota - available_upload)} ({usage_percentage:.1f}%)\n\n", "value")
                except (TypeError, ValueError) as e:
                    # Handle calculation errors
                    self.output_text.insert(tk.END, "Error processing quota information:\n", "error")
                    self.output_text.insert(tk.END, f"{str(e)}\n\n", "error_details")
            
            # Time information
            self.output_text.insert(tk.END, "TIME INFORMATION\n", "section")
            
            self.output_text.insert(tk.END, "Time until renewal: ", "label")
            self.output_text.insert(tk.END, f"{time_remaining.days} days, {time_remaining.seconds // 3600} hours, {(time_remaining.seconds % 3600) // 60} minutes\n", "value")
            
            renewal_time = datetime.fromtimestamp(renew_timestamp)
            self.output_text.insert(tk.END, "Renewal date: ", "label")
            self.output_text.insert(tk.END, f"{renewal_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n", "value")
            
            # Footer
            self.output_text.insert(tk.END, f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n", "footer")
            
            # Scroll to the top to see all information
            self.output_text.see(1.0)
            
        except Exception as e:
            # Get the full traceback for detailed error information
            error_traceback = traceback.format_exc()
            self.display_error(
                f"Error processing data: {e}", 
                f"Traceback:\n{error_traceback}\n\nData received:\n{json.dumps(data, indent=2)[:500]}...(truncated)"
            )
            
    def save_history(self):
        if not self.current_data:
            messagebox.showerror("Error", "No data to save. Please fetch data first.")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = self.username_var.get()
            
            # Extract data based on response type
            if "user" in self.current_data and "consumedData" in self.current_data["user"]:
                # Normal response
                consumed = self.current_data.get("user", {}).get("consumedData", {})
                download_bytes = int(consumed.get("download", {}).get("value", 0))
                upload_bytes = int(consumed.get("upload", {}).get("value", 0))
            elif "error" in self.current_data and self.current_data["error"].get("code") == "error_logon_volume-quota-reached-detail":
                # Quota-reached response
                error_value = self.current_data.get("error", {}).get("value", {})
                download_bytes = int(error_value.get("consumedDown", 0))
                upload_bytes = int(error_value.get("consumedUp", 0))
            else:
                messagebox.showerror("Error", "Unrecognized data format. Cannot save history.")
                return
            
            # Check if file exists
            file_exists = os.path.isfile('usage_history.csv')
            
            with open('usage_history.csv', 'a') as f:
                # Write header if file doesn't exist
                if not file_exists:
                    f.write("Timestamp,Username,Download (MB),Upload (MB),Total (MB),Status\n")
                
                # Write data with status
                status = "Quota Reached" if "error" in self.current_data else "Active"
                f.write(f"{timestamp},{username},{download_bytes/1024/1024:.2f},{upload_bytes/1024/1024:.2f},{(download_bytes+upload_bytes)/1024/1024:.2f},{status}\n")
            
            self.set_status("Usage data saved to usage_history.csv", "success")
            messagebox.showinfo("Success", "Usage data saved to usage_history.csv")
        except Exception as e:
            self.set_status("Error saving data", "error")
            messagebox.showerror("Error", f"Error saving usage data: {e}")
    
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

def center_window(window):
    """Center the window on the screen"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        icon_path = resource_path("icon.ico")
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Could not load icon: {e}")
    app = StenaInternetMonitor(root)
    center_window(root)
    root.mainloop()
