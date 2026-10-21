import os
import sys
import shutil
import string
import ctypes
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image

def get_default_usb_drive():
    """Detects the first connected removable USB drive on macOS or Windows."""
    if sys.platform == "win32":
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(drive) == 2:
                return drive
    elif sys.platform == "darwin":
        volumes_dir = "/Volumes"
        if os.path.exists(volumes_dir):
            for vol in os.listdir(volumes_dir):
                full_path = os.path.join(volumes_dir, vol)
                if os.path.isdir(full_path) and not vol.startswith(".") and vol != "Macintosh HD":
                    return full_path
    return None

def copy_file_with_progress(src, dst, progress_callback=None):
    """Copies a file in 1 MB chunks and reports progress back to the UI."""
    total_size = os.path.getsize(src)
    copied = 0
    chunk_size = 1024 * 1024  # 1 MB buffer

    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            buf = fsrc.read(chunk_size)
            if not buf:
                break
            fdst.write(buf)
            copied += len(buf)
            if progress_callback:
                percent_copied = (copied / total_size)
                # Map file copying to 0% - 80% of total progress bar
                overall_progress = percent_copied * 80
                progress_callback(overall_progress, f"Copying video file... {int(percent_copied * 100)}%")

    shutil.copystat(src, dst)

def generate_autoplay_folder(video_path, destination_base_dir, status_callback=None):
    file_size = os.path.getsize(video_path)
    filename_with_ext = os.path.basename(video_path)
    filename_no_ext = os.path.splitext(filename_with_ext)[0]

    output_dir = os.path.join(destination_base_dir, "AutoPlay")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Chunked video copy with progress tracking
    dest_video_path = os.path.join(output_dir, filename_with_ext)
    copy_file_with_progress(video_path, dest_video_path, status_callback)

    # 2. Extract video frame & generate thumbnails
    if status_callback:
        status_callback(85, "Extracting video frame & creating thumbnails...")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open selected video file.")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = int(round(frame_count / fps)) if fps > 0 else 0

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise ValueError("Failed to extract the first frame from the video.")

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)

    # Save video_thumb.png
    video_thumb_path = os.path.join(output_dir, "video_thumb.png")
    img.save(video_thumb_path, "PNG")

    # Save canvasthumb_401.png (914x433 px)
    canvas_thumb_path = os.path.join(output_dir, "canvasthumb_401.png")
    canvas_img = img.resize((914, 433), Image.LANCZOS)
    canvas_img.save(canvas_thumb_path, "PNG")

    # 3. Create Playlist.pcts & ExportPlaylist.cpls
    if status_callback:
        status_callback(95, "Generating playlist XML files...")

    pcts_content = f'''<Canvas Duration="{duration}" Idx="401" isSimpleEditor="true" Name="{filename_no_ext}" PlayerType="TV" Type="NORMAL">
    <Region Height="{height}" Name="background" Width="{width}" X="0" Y="0" Z="1">
        <Media Type="Window">
            <BkColor>0</BkColor>
        </Media>
    </Region>
    <Region Height="{height}" Name="Movie" Width="{width}" X="0" Y="0" Z="2">
        <Media Type="Movie">
            <BkColor>4278190080</BkColor>
            <Content Duration="{duration}" StartTime="0">
                <Aspect>FULL</Aspect>
                <Name>{filename_with_ext}</Name>
                <ContentVolumeSet>false</ContentVolumeSet>
                <FileId>-1</FileId>
                <FileSize>{file_size}</FileSize>
                <Height>{height}</Height>
                <LineSpace>0</LineSpace>
                <MediaFolderIdx>9000</MediaFolderIdx>
                <MediaFormatIdx>15</MediaFormatIdx>
                <Mediaidx>1903</Mediaidx>
                <MediaTypeId>1</MediaTypeId>
                <Mute>false</Mute>
                <PlayTime>{duration}</PlayTime>
                <Signature></Signature>
                <ThumbnailFileId>-1</ThumbnailFileId>
                <ThumbnailHeight>{height}</ThumbnailHeight>
                <ThumbnailIdx>5017</ThumbnailIdx>
                <ThumbnailName>video_thumb.png</ThumbnailName>
                <ThumbnailWidth>{width}</ThumbnailWidth>
                <TrEffect>0</TrEffect>
                <Volume>10</Volume>
                <Width>{width}</Width>
            </Content>
            <Repeat>INFINITE</Repeat>
        </Media>
    </Region>
</Canvas>'''

    cpls_content = f'''<Playlist Duration="{duration}" Height="{height}" ItemCount="1" Name="ExportPlaylist" PlayerType="TV" Repeat="true" Size="{file_size}" Type="Normal" Width="{width}">
    <Canvas Duration="{duration}" EndTime="{duration}" Index="401" Name="Playlist.pcts" Size="{file_size}" StartTime="0"/>
</Playlist>'''

    with open(os.path.join(output_dir, "Playlist.pcts"), "w", encoding="utf-8") as f:
        f.write(pcts_content)

    with open(os.path.join(output_dir, "ExportPlaylist.cpls"), "w", encoding="utf-8") as f:
        f.write(cpls_content)

    if status_callback:
        status_callback(100, "Done!")

    return output_dir

class AutoPlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LG AutoPlay Generator")
        self.root.geometry("520x310")
        self.root.resizable(False, False)

        # Apply app icon if icon.png is present in working directory
        try:
            icon_img = tk.PhotoImage(file="icon.png")
            self.root.iconphoto(False, icon_img)
        except Exception:
            pass

        self.selected_video = tk.StringVar()
        self.selected_output = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        usb_path = get_default_usb_drive()
        if usb_path:
            self.selected_output.set(usb_path)

        frame = ttk.Frame(root, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Video File Selection
        ttk.Label(frame, text="1. Select Video File:").pack(anchor=tk.W)
        v_frame = ttk.Frame(frame)
        v_frame.pack(fill=tk.X, pady=(2, 10))
        ttk.Entry(v_frame, textvariable=self.selected_video).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(v_frame, text="Browse...", command=self.browse_video).pack(side=tk.RIGHT)

        # Save Location Selection
        ttk.Label(frame, text="2. Save AutoPlay Folder To:").pack(anchor=tk.W)
        o_frame = ttk.Frame(frame)
        o_frame.pack(fill=tk.X, pady=(2, 12))
        ttk.Entry(o_frame, textvariable=self.selected_output).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(o_frame, text="Browse...", command=self.browse_output).pack(side=tk.RIGHT)

        # Progress Bar & Button
        self.generate_btn = ttk.Button(frame, text="Generate & Copy AutoPlay Folder", command=self.start_processing_thread)
        self.generate_btn.pack(fill=tk.X, pady=(5, 10))

        self.progress_bar = ttk.Progressbar(frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.progress_label = ttk.Label(frame, textvariable=self.status_text, font=("TkDefaultFont", 9, "italic"))
        self.progress_label.pack(anchor=tk.W)

    def browse_video(self):
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video Files", "*.mp4 *.mov *.avi *.mkv *.wmv"), ("All Files", "*.*")]
        )
        if filepath:
            self.selected_video.set(filepath)
            if not self.selected_output.get():
                self.selected_output.set(os.path.dirname(filepath))

    def browse_output(self):
        folderpath = filedialog.askdirectory(title="Select Destination Folder / USB Drive")
        if folderpath:
            self.selected_output.set(folderpath)

    def update_status(self, progress_val, message):
        self.progress_bar['value'] = progress_val
        self.status_text.set(message)
        self.root.update_idletasks()

    def start_processing_thread(self):
        video_path = self.selected_video.get()
        out_dir = self.selected_output.get()

        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("Error", "Please select a valid video file.")
            return

        if not out_dir or not os.path.exists(out_dir):
            messagebox.showerror("Error", "Please select a valid output destination folder.")
            return

        self.generate_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        
        threading.Thread(target=self.process, args=(video_path, out_dir), daemon=True).start()

    def process(self, video_path, out_dir):
        try:
            output_dir = generate_autoplay_folder(video_path, out_dir, status_callback=self.update_status)
            messagebox.showinfo("Success", f"AutoPlay folder successfully generated at:\n{output_dir}")
        except Exception as e:
            self.update_status(0, "Failed!")
            messagebox.showerror("Error", f"Failed to process request:\n{str(e)}")
        finally:
            self.generate_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoPlayApp(root)
    root.mainloop()