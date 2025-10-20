import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import os
from pathlib import Path
import re

class VideoFrameExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Frame Extractor")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        self.video_path = None
        self.video_duration = 0
        self.fps = 0
        self.total_frames = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="Video Frame Extractor", 
                         font=("Arial", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Video selection
        ttk.Label(main_frame, text="Video File:", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        
        self.video_label = ttk.Label(main_frame, text="No file selected", 
                                     foreground="gray")
        self.video_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        select_btn = ttk.Button(main_frame, text="Select Video", 
                               command=self.select_video)
        select_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Frame rate selection
        ttk.Label(main_frame, text="Frames Per Second (FPS):", 
                 font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.fps_var = tk.StringVar(value="1")
        fps_frame = ttk.Frame(main_frame)
        fps_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        fps_combo = ttk.Combobox(fps_frame, textvariable=self.fps_var, 
                                values=["0.5", "1", "2", "5", "10", "15", "24", "30", "60"], 
                                width=10)
        fps_combo.grid(row=0, column=0, padx=(0, 10))
        fps_combo.bind("<<ComboboxSelected>>", self.update_info)
        fps_combo.bind("<KeyRelease>", self.update_info)
        
        # Use original FPS checkbox
        self.use_original_var = tk.BooleanVar(value=False)
        original_check = ttk.Checkbutton(fps_frame, text="Use Original FPS", 
                                        variable=self.use_original_var,
                                        command=self.toggle_original_fps)
        original_check.grid(row=0, column=1)
        
        # Info display
        self.info_label = ttk.Label(main_frame, text="", 
                                   foreground="blue", font=("Arial", 9))
        self.info_label.grid(row=6, column=0, columnspan=2, pady=15)
        
        # Format selection
        ttk.Label(main_frame, text="Output Format:", 
                 font=("Arial", 10)).grid(row=7, column=0, sticky=tk.W, pady=5)
        
        self.format_var = tk.StringVar(value="png")
        format_combo = ttk.Combobox(main_frame, textvariable=self.format_var, 
                                   values=["png", "jpg"], 
                                   state="readonly", width=10)
        format_combo.grid(row=8, column=0, sticky=tk.W, pady=5)
        
        # Output folder name
        ttk.Label(main_frame, text="Output Folder Name:", 
                 font=("Arial", 10)).grid(row=9, column=0, sticky=tk.W, pady=5)
        
        self.folder_var = tk.StringVar(value="extracted_frames")
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, width=30)
        folder_entry.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Extract button
        self.extract_btn = ttk.Button(main_frame, text="Extract Frames", 
                                     command=self.extract_frames, 
                                     state="disabled")
        self.extract_btn.grid(row=11, column=0, columnspan=2, pady=20)
        
        # Progress
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=300)
        self.progress.grid(row=12, column=0, columnspan=2, pady=5)
        
        self.status_label = ttk.Label(main_frame, text="", foreground="green")
        self.status_label.grid(row=13, column=0, columnspan=2)
        
    def toggle_original_fps(self):
        self.update_info()
        
    def select_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.video_path = file_path
            self.video_label.config(text=os.path.basename(file_path), 
                                   foreground="black")
            self.get_video_info()
            self.update_info()
            self.extract_btn.config(state="normal")
            
    def get_video_info(self):
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate,duration',
                '-of', 'json',
                self.video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            info = json.loads(result.stdout)
            
            stream = info['streams'][0]
            
            # Get FPS
            fps_str = stream['r_frame_rate']
            num, den = map(int, fps_str.split('/'))
            self.fps = num / den
            
            # Get duration
            self.video_duration = float(stream.get('duration', 0))
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not read video info: {str(e)}")
            
    def update_info(self, event=None):
        if self.video_path:
            if self.use_original_var.get():
                extract_fps = self.fps
                info_text = (f"Video: {self.video_duration:.1f} seconds @ {self.fps:.2f} fps\n"
                            f"Will extract ALL frames at original {self.fps:.2f} fps\n"
                            f"Estimated images: ~{int(self.video_duration * self.fps)}")
            else:
                try:
                    extract_fps = float(self.fps_var.get())
                    estimated_images = int(self.video_duration * extract_fps)
                    info_text = (f"Video: {self.video_duration:.1f} seconds @ {self.fps:.2f} fps\n"
                                f"Will extract {extract_fps} frame(s) per second\n"
                                f"Estimated images: ~{estimated_images}")
                except ValueError:
                    info_text = "Please enter a valid FPS value"
                    
            self.info_label.config(text=info_text)
            
    def extract_frames(self):
        if not self.video_path:
            messagebox.showwarning("Warning", "Please select a video file first")
            return
            
        folder_name = self.folder_var.get().strip()
        if not folder_name:
            messagebox.showwarning("Warning", "Please enter a folder name")
            return
            
        # Create output folder in current directory
        output_dir = Path.cwd() / folder_name
        output_dir.mkdir(exist_ok=True)
        
        # Get format
        output_format = self.format_var.get()
        
        # Start extraction
        self.extract_btn.config(state="disabled")
        self.progress.start()
        self.status_label.config(text="Extracting frames...", foreground="blue")
        self.root.update()
        
        try:
            if self.use_original_var.get():
                # Extract all frames at original FPS
                cmd = [
                    'ffmpeg', '-i', self.video_path,
                    str(output_dir / f'frame_%04d.{output_format}')
                ]
            else:
                # Extract at specified FPS
                extract_fps = float(self.fps_var.get())
                cmd = [
                    'ffmpeg', '-i', self.video_path,
                    '-vf', f'fps={extract_fps}',
                    str(output_dir / f'frame_%04d.{output_format}')
                ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Count actual extracted files
            extracted_count = len(list(output_dir.glob(f'frame_*.{output_format}')))
            
            self.progress.stop()
            self.status_label.config(
                text=f"Success! Extracted {extracted_count} frames to '{folder_name}'",
                foreground="green"
            )
            self.extract_btn.config(state="normal")
            
            messagebox.showinfo("Success", 
                              f"Extracted {extracted_count} frames to:\n{output_dir}")
            
        except subprocess.CalledProcessError as e:
            self.progress.stop()
            self.status_label.config(text="Extraction failed", foreground="red")
            self.extract_btn.config(state="normal")
            messagebox.showerror("Error", f"Frame extraction failed:\n{e.stderr}")
        except Exception as e:
            self.progress.stop()
            self.status_label.config(text="Extraction failed", foreground="red")
            self.extract_btn.config(state="normal")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFrameExtractor(root)
    root.mainloop()