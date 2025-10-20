import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import json
import os
from pathlib import Path
import shutil

class VideoFrameExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Frame Extractor")
        self.root.geometry("600x600")
        self.root.resizable(True, True)

        self.video_path = None
        self.video_duration = 0.0
        self.fps = 0.0

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title = ttk.Label(main_frame, text="Video Frame Extractor", font=("Arial", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(main_frame, text="Video File:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.video_label = ttk.Label(main_frame, text="No file selected", foreground="gray")
        self.video_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        select_btn = ttk.Button(main_frame, text="Select Video", command=self.select_video)
        select_btn.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Label(main_frame, text="Frames Per Second (FPS):", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.StringVar(value="1")
        fps_frame = ttk.Frame(main_frame)
        fps_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)

        fps_combo = ttk.Combobox(fps_frame, textvariable=self.fps_var,
                                 values=["0.5", "1", "2", "5", "10", "15", "24", "30", "60"],
                                 width=10)
        fps_combo.grid(row=0, column=0, padx=(0, 10))
        fps_combo.bind("<<ComboboxSelected>>", self.update_info)
        fps_combo.bind("<KeyRelease>", self.update_info)

        self.use_original_var = tk.BooleanVar(value=False)
        original_check = ttk.Checkbutton(fps_frame, text="Use Original FPS",
                                         variable=self.use_original_var,
                                         command=self.toggle_original_fps)
        original_check.grid(row=0, column=1)

        self.info_label = ttk.Label(main_frame, text="", foreground="blue", font=("Arial", 9))
        self.info_label.grid(row=6, column=0, columnspan=2, pady=15)

        # Format selection
        ttk.Label(main_frame, text="Output Format:", font=("Arial", 10)).grid(row=7, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="png")
        format_combo = ttk.Combobox(main_frame, textvariable=self.format_var,
                                    values=["png", "jpg"], state="readonly", width=10)
        format_combo.grid(row=8, column=0, sticky=tk.W, pady=5)

        # Target file size (KB)
        ttk.Label(main_frame, text="Target File Size (KB, approximate):", font=("Arial", 10)).grid(row=9, column=0, sticky=tk.W, pady=5)
        self.size_var = tk.StringVar(value="")
        size_entry = ttk.Entry(main_frame, textvariable=self.size_var, width=20)
        size_entry.grid(row=10, column=0, sticky=tk.W, pady=5)

        # Output folder name
        ttk.Label(main_frame, text="Output Folder Name:", font=("Arial", 10)).grid(row=11, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar(value="extracted_frames")
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, width=30)
        folder_entry.grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Extract button
        self.extract_btn = ttk.Button(main_frame, text="Extract Frames", command=self.extract_frames, state="disabled")
        self.extract_btn.grid(row=13, column=0, columnspan=2, pady=20)

        # Progress bar (changed to determinate mode)
        self.progress = ttk.Progressbar(main_frame, mode='determinate', length=300)
        self.progress.grid(row=14, column=0, columnspan=2, pady=5)
        
        # Status label with larger, more visible text
        self.status_label = ttk.Label(main_frame, text="", foreground="green", font=("Arial", 10, "bold"))
        self.status_label.grid(row=15, column=0, columnspan=2)

    def toggle_original_fps(self):
        self.update_info()

    def select_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), ("All files", "*.*")]
        )
        if file_path:
            self.video_path = file_path
            self.video_label.config(text=os.path.basename(file_path), foreground="black")
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
            fps_str = stream.get('r_frame_rate', "0/1")
            num, den = map(int, fps_str.split('/'))
            self.fps = num / den if den != 0 else 0.0
            self.video_duration = float(stream.get('duration', 0.0))
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

            if self.size_var.get().strip():
                info_text += f"\nTarget file size: ~{self.size_var.get().strip()} KB per frame"

            self.info_label.config(text=info_text)

    def extract_frames(self):
        if not self.video_path:
            messagebox.showwarning("Warning", "Please select a video file first")
            return

        folder_name = self.folder_var.get().strip()
        if not folder_name:
            messagebox.showwarning("Warning", "Please enter a folder name")
            return

        # Determine output format. If user requested PNG but also target size, switch to JPG and warn
        requested_format = self.format_var.get().lower()
        target_kb_str = self.size_var.get().strip()
        use_target_size = False
        target_kb = None

        if target_kb_str:
            try:
                target_kb = float(target_kb_str)
                if target_kb <= 0:
                    raise ValueError()
                use_target_size = True
            except Exception:
                messagebox.showwarning("Warning", "Invalid target file size; ignoring size setting")
                use_target_size = False
                target_kb = None

        output_format = requested_format
        if use_target_size and requested_format == "png":
            output_format = "jpg"
            messagebox.showinfo("Note", "PNG chosen with target size. Will convert frames to JPEG to meet size target.")

        output_dir = Path.cwd() / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Start progress
        self.extract_btn.config(state="disabled")
        self.progress['value'] = 0
        self.progress['maximum'] = 100
        self.status_label.config(text="Extracting frames...", foreground="blue")
        self.root.update()

        try:
            # Build fps filter
            if self.use_original_var.get():
                fps_filter = []
            else:
                extract_fps = float(self.fps_var.get())
                fps_filter = ['-vf', f'fps={extract_fps}']

            # Initial extraction
            temp_ext = output_format
            initial_args = []
            if use_target_size:
                temp_ext = 'jpg'
                initial_args = ['-q:v', '2']
            else:
                if output_format == 'jpg':
                    initial_args = ['-q:v', '2']
                elif output_format == 'png':
                    initial_args = ['-compression_level', '6']

            cmd = ['ffmpeg', '-y', '-i', self.video_path, *fps_filter, *initial_args, str(output_dir / f'frame_%04d.{temp_ext}')]
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Update progress after initial extraction
            self.progress['value'] = 50 if use_target_size else 100
            self.root.update()

            # Re-encode each frame to meet target size
            if use_target_size:
                target_bytes = int(target_kb * 1024)
                frame_files = sorted(output_dir.glob('frame_*.jpg'))
                total = len(frame_files)
                if total == 0:
                    raise RuntimeError("No frames were produced during extraction")

                self.status_label.config(text=f"Adjusting to ~{int(target_kb)} KB per frame...", foreground="blue")
                self.root.update()

                for idx, src_path in enumerate(frame_files, start=1):
                    low_q, high_q = 2, 31
                    best_tmp = None
                    best_diff = None

                    for _ in range(6):  # binary search for q:v
                        mid_q = (low_q + high_q) // 2
                        tmp_path = output_dir / f'.tmp_{src_path.name}'
                        cmd_re = ['ffmpeg', '-y', '-i', str(src_path), '-q:v', str(mid_q), str(tmp_path)]
                        subprocess.run(cmd_re, capture_output=True)
                        if not tmp_path.exists():
                            break
                        size_mid = tmp_path.stat().st_size
                        diff = abs(size_mid - target_bytes)
                        if best_diff is None or diff < best_diff:
                            if best_tmp and best_tmp.exists():
                                best_tmp.unlink(missing_ok=True)
                            best_tmp = tmp_path
                            best_diff = diff
                        else:
                            tmp_path.unlink(missing_ok=True)

                        if size_mid > target_bytes:
                            low_q = mid_q + 1
                        else:
                            high_q = mid_q - 1

                    if best_tmp and best_tmp.exists():
                        final_path = src_path.with_suffix(f'.{output_format}')
                        shutil.move(str(best_tmp), str(final_path))
                        if final_path != src_path:
                            src_path.unlink(missing_ok=True)

                    # Update progress bar
                    progress_percent = 50 + int((idx / total) * 50)
                    self.progress['value'] = progress_percent
                    self.status_label.config(text=f"Adjusting frames: {idx}/{total} ({progress_percent}%)")
                    self.root.update()

            # --- Count actual extracted files and show completion ---
            final_ext = output_format
            extracted_count = len(list(output_dir.glob(f'frame_*.{final_ext}')))

            # Make completion VERY obvious
            self.progress['value'] = 100
            self.status_label.config(
                text=f"✅ COMPLETE! {extracted_count} frames extracted successfully ✅",
                foreground="green",
                font=("Arial", 12, "bold")
            )
            self.root.update()

            # Re-enable extract button
            self.extract_btn.config(state="normal")
            
            # Show popup
            messagebox.showinfo(
                "Extraction Complete! ✅",
                f"Successfully extracted {extracted_count} frames!\n\nSaved to: {output_dir}\n\nYou can now extract more frames or close the application."
            )
            
            # Reset progress bar after user closes the popup
            self.progress['value'] = 0

        except subprocess.CalledProcessError as e:
            self.progress['value'] = 0
            self.status_label.config(text="❌ Extraction failed", foreground="red", font=("Arial", 11, "bold"))
            self.extract_btn.config(state="normal")
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            messagebox.showerror("Error", f"Frame extraction failed:\n{err}")
        except Exception as e:
            self.progress['value'] = 0
            self.status_label.config(text="❌ Extraction failed", foreground="red", font=("Arial", 11, "bold"))
            self.extract_btn.config(state="normal")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFrameExtractor(root)
    root.mainloop()