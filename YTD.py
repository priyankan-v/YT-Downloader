import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os
import shutil
from pathlib import Path

# Configuration Constants
DEFAULT_SAVE = r"E:\Music" # Change this to your desired default save path
WINDOW_WIDTH = 520
WINDOW_HEIGHT = 650
APP_TITLE = "YouTube Downloader"
ACCENT_COLOR = "#00ff9c"
BG_COLOR = "#121212"
FG_COLOR = "white"
SECONDARY_BG = "#1f1f1f"
TERTIARY_BG = "#2a2a2a"

# Global state
paste_state = 0
current_download = None

def paste_auto():
    """Smart auto-paste: detects URL vs name and pastes to correct field."""
    try:
        text = root.clipboard_get().strip()
        
        if not text:
            messagebox.showwarning("Warning", "Clipboard is empty")
            return

        # Check if clipboard contains a URL
        is_url = text.lower().startswith(('http://', 'https://', 'www.', 'youtu'))
        
        if is_url:
            # It's a link - paste to URL field
            url_entry.delete(0, tk.END)
            url_entry.insert(0, text)
            status_label.config(text="✔ Link pasted. Now copy and paste the name.")
        else:
            # It's a name - paste to name field
            name_entry.delete(0, tk.END)
            name_entry.insert(0, text)
            status_label.config(text="✔ Name pasted. Ready to download!")

    except tk.TclError:
        messagebox.showerror("Error", "Unable to access clipboard")
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {str(e)}")

def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def progress_hook(d):
    """Update progress bar based on download status."""
    try:
        if d['status'] == 'downloading':
            if '_percent_str' in d:
                percent_str = d['_percent_str'].replace('%', '').strip()
                try:
                    percent = float(percent_str)
                    progress['value'] = percent
                    progress_label.config(text=f"Downloading {int(percent)}%")
                    root.update_idletasks()
                except ValueError:
                    pass

        elif d['status'] == 'finished':
            progress['value'] = 100
            progress_label.config(text="Download Finished ✔")
            root.after(2000, reset_ui)
    except Exception as e:
        print(f"Progress hook error: {str(e)}")

def reset_ui():

    url_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)

    progress.pack_forget()
    progress_label.pack_forget()

def download():
    """Initiate YouTube download process."""
    url = url_entry.get().strip()
    name = name_entry.get().strip()

    # Validation
    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if not name:
        messagebox.showerror("Error", "Please enter a name or playlist folder name")
        return

    # Check if folder exists and is writable
    save_path = folder_var.get().strip()
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create folder: {str(e)}")
            return

    if not os.access(save_path, os.W_OK):
        messagebox.showerror("Error", "No write permission for selected folder")
        return

    progress.pack(pady=15)
    progress_label.pack()

    progress['value'] = 0
    progress_label.config(text="Starting...")

    def run():
        global current_download
        try:
            if playlist_var.get() == "playlist":
                folder = os.path.join(save_path, name)
                os.makedirs(folder, exist_ok=True)
                outtmpl = os.path.join(folder, "%(title)s.%(ext)s")
            else:
                outtmpl = os.path.join(save_path, f"{name}.%(ext)s")

            if media_var.get() == "audio":
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': outtmpl,
                    'progress_hooks': [progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '0'
                    }],
                    'quiet': False,
                    'no_warnings': False
                }
            else:
                quality = quality_var.get()
                ydl_opts = {
                    'format': f"bestvideo[height<={quality}]+bestaudio/best",
                    'merge_output_format': 'mp4',
                    'outtmpl': outtmpl,
                    'progress_hooks': [progress_hook],
                    'quiet': False,
                    'no_warnings': False
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                current_download = ydl
                ydl.download([url])

        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Download Error", f"Error: {str(e)}"))
            root.after(0, reset_ui)
        finally:
            current_download = None

    download_thread = threading.Thread(target=run, daemon=True)
    download_thread.start()

def toggle_quality():

    if media_var.get() == "video":
        quality_frame.pack(pady=5)
    else:
        quality_frame.pack_forget()

def center_window(win, width, height):
    """Center window on screen."""
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")

# UI Initialization
root = tk.Tk()
root.title(APP_TITLE)
center_window(root, WINDOW_WIDTH, WINDOW_HEIGHT)
root.configure(bg=BG_COLOR)

# Style configuration
style = ttk.Style()
style.theme_use("clam")
style.configure(
    "TProgressbar",
    background=ACCENT_COLOR,
    troughcolor=TERTIARY_BG,
    thickness=8
)

# Title Label
title = tk.Label(
    root,
    text=APP_TITLE,
    font=("Segoe UI", 18, "bold"),
    bg=BG_COLOR,
    fg=ACCENT_COLOR
)
title.pack(pady=10)

# Status label
status_label = tk.Label(
    root,
    text="Paste clipboard into Link field",
    bg=BG_COLOR,
    fg=ACCENT_COLOR,
    font=("Segoe UI", 10)  # Changed from 8 to 10
)
status_label.pack(pady=5)

# Link Input
tk.Label(root, text="YouTube Link", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack()

url_entry = tk.Entry(
    root,
    width=60,
    bg=SECONDARY_BG,
    fg=FG_COLOR,
    insertbackground=FG_COLOR,
    relief="flat"
)
url_entry.pack(pady=5)

# Name Input
tk.Label(root, text="Name / Playlist Folder", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack()

name_entry = tk.Entry(
    root,
    width=40,
    bg=SECONDARY_BG,
    fg=FG_COLOR,
    insertbackground=FG_COLOR,
    relief="flat"
)
name_entry.pack(pady=5)

# Paste Button
tk.Button(
    root,
    text="Paste (Auto)",
    command=paste_auto,
    bg=ACCENT_COLOR,
    fg="black",
    width=15
).pack(pady=10)

tk.Label(root, text="Download Type", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack(pady=5)

media_var = tk.StringVar(value="audio")

type_frame = tk.Frame(root, bg=BG_COLOR)
type_frame.pack()

tk.Radiobutton(
    type_frame,
    text="Audio (MP3)",
    variable=media_var,
    value="audio",
    command=toggle_quality,
    bg=BG_COLOR,
    fg=FG_COLOR,
    selectcolor=BG_COLOR
).pack(side="left", padx=15)

tk.Radiobutton(
    type_frame,
    text="Video",
    variable=media_var,
    value="video",
    command=toggle_quality,
    bg=BG_COLOR,
    fg=FG_COLOR,
    selectcolor=BG_COLOR
).pack(side="left", padx=15)

# Quality Selection
quality_var = tk.StringVar(value="720")

quality_frame = tk.Frame(root, bg=BG_COLOR)

tk.Label(quality_frame, text="Video Quality", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack()

quality_menu = ttk.Combobox(
    quality_frame,
    textvariable=quality_var,
    values=["360", "480", "720", "1080"],
    state="readonly",
    width=10
)

quality_menu.pack()

# Download Mode
tk.Label(root, text="Mode", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack(pady=5)

playlist_var = tk.StringVar(value="single")

mode_frame = tk.Frame(root, bg=BG_COLOR)
mode_frame.pack()

tk.Radiobutton(
    mode_frame,
    text="Single",
    variable=playlist_var,
    value="single",
    bg=BG_COLOR,
    fg=FG_COLOR,
    selectcolor=BG_COLOR
).pack(side="left", padx=20)

tk.Radiobutton(
    mode_frame,
    text="Playlist",
    variable=playlist_var,
    value="playlist",
    bg=BG_COLOR,
    fg=FG_COLOR,
    selectcolor=BG_COLOR
).pack(side="left", padx=20)

# Folder Selection
folder_var = tk.StringVar(value=DEFAULT_SAVE)

tk.Label(root, text="Save Folder", bg=BG_COLOR, fg=FG_COLOR, font=("Segoe UI", 10, "bold")).pack(pady=5)

tk.Entry(
    root,
    textvariable=folder_var,
    width=50,
    bg=SECONDARY_BG,
    fg=FG_COLOR,
    insertbackground=FG_COLOR,
    relief="flat"
).pack()

tk.Button(
    root,
    text="Choose Folder",
    command=choose_folder,
    bg=TERTIARY_BG,
    fg=FG_COLOR
).pack(pady=8)

# Download Button
tk.Button(
    root,
    text="Download",
    command=download,
    bg=ACCENT_COLOR,
    fg="black",
    width=20,
    height=2
).pack(pady=15)

# Progress Bar
progress = ttk.Progressbar(root, length=400)

progress_label = tk.Label(root, text="", bg=BG_COLOR, fg=FG_COLOR)

root.mainloop()