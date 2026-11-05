import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from pathlib import Path

import organizer
import toolbox
import reader

ctk.set_default_color_theme("blue")


class SuitcaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Suitcase — Safe File Workspace")
        self.geometry("1060x700")
        self.minsize(920, 620)

        # Load persisted settings from config
        self.config_data = organizer.load_config()
        initial_theme = self.config_data.get("theme", "dark").capitalize()
        ctk.set_appearance_mode(initial_theme)

        # Reader session state
        self.doc_pages = []
        self.current_page_idx = 0
        self.current_doc_type = ""

        # Main window layout: fixed sidebar + responsive main body
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_frames()
        self.show_frame("organizer")

    # ------------------ Sidebar Navigation ------------------ #
    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="💼 SUITCASE",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(25, 20), sticky="w")

        self.btn_nav_organizer = ctk.CTkButton(
            self.sidebar_frame,
            text="📁  Organizer",
            anchor="w",
            font=ctk.CTkFont(size=14),
            command=lambda: self.show_frame("organizer")
        )
        self.btn_nav_organizer.grid(row=1, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_toolbox = ctk.CTkButton(
            self.sidebar_frame,
            text="🧰  Toolbox",
            anchor="w",
            font=ctk.CTkFont(size=14),
            command=lambda: self.show_frame("toolbox")
        )
        self.btn_nav_toolbox.grid(row=2, column=0, padx=15, pady=6, sticky="ew")

        self.btn_nav_reader = ctk.CTkButton(
            self.sidebar_frame,
            text="📖  Reader",
            anchor="w",
            font=ctk.CTkFont(size=14),
            command=lambda: self.show_frame("reader")
        )
        self.btn_nav_reader.grid(row=3, column=0, padx=15, pady=6, sticky="ew")

        # Bottom section: Theme Switcher
        self.theme_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance:", anchor="w")
        self.theme_label.grid(row=5, column=0, padx=20, pady=(0, 2), sticky="w")

        current_theme = self.config_data.get("theme", "dark").capitalize()
        self.theme_dropdown = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light"],
            command=self.change_theme
        )
        self.theme_dropdown.set(current_theme)
        self.theme_dropdown.grid(row=6, column=0, padx=15, pady=(0, 25), sticky="ew")

    def change_theme(self, new_theme: str):
        ctk.set_appearance_mode(new_theme)
        self.config_data["theme"] = new_theme.lower()
        organizer.save_config(self.config_data)

    def _build_content_frames(self):
        # ------------------ Frame 1: Organizer ------------------ #
        self.frame_organizer = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_organizer.grid_columnconfigure(0, weight=1)
        self.frame_organizer.grid_rowconfigure(1, weight=1)

        self.org_top_bar = ctk.CTkFrame(self.frame_organizer)
        self.org_top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.org_top_bar.grid_columnconfigure(0, weight=1)

        self.lbl_selected_dir = ctk.CTkEntry(
            self.org_top_bar,
            placeholder_text="Select a directory to organize...",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_selected_dir.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        self.btn_browse = ctk.CTkButton(self.org_top_bar, text="Browse", width=100, command=self.browse_folder)
        self.btn_browse.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.txt_preview = ctk.CTkTextbox(
            self.frame_organizer,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none"
        )
        self.txt_preview.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.txt_preview.insert("0.0", "Select a folder above and click 'Scan & Preview' to inspect actions.\n")

        self.org_bottom_bar = ctk.CTkFrame(self.frame_organizer)
        self.org_bottom_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        self.btn_scan = ctk.CTkButton(self.org_bottom_bar, text="Scan & Preview", command=self.run_preview)
        self.btn_scan.pack(side="left", padx=10, pady=10)

        self.btn_execute = ctk.CTkButton(
            self.org_bottom_bar,
            text="Organize Files",
            fg_color="#059669",
            hover_color="#047857",
            command=self.run_execution
        )
        self.btn_execute.pack(side="left", padx=10, pady=10)

        self.btn_undo = ctk.CTkButton(
            self.org_bottom_bar,
            text="Undo Last Run",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self.run_undo
        )
        self.btn_undo.pack(side="right", padx=10, pady=10)

        # ------------------ Frame 2: Toolbox ------------------ #
        self.frame_toolbox = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_toolbox.grid_columnconfigure(0, weight=1)
        self.frame_toolbox.grid_rowconfigure(1, weight=1)

        self.tb_top = ctk.CTkFrame(self.frame_toolbox)
        self.tb_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.tb_top.grid_columnconfigure(0, weight=1)

        self.lbl_tb_file = ctk.CTkEntry(
            self.tb_top,
            placeholder_text="Select image file...",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_tb_file.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        self.btn_tb_browse = ctk.CTkButton(self.tb_top, text="Browse", width=100, command=self.browse_toolbox_file)
        self.btn_tb_browse.grid(row=0, column=1, padx=(0, 10), pady=10)

        self.tb_controls = ctk.CTkFrame(self.frame_toolbox)
        self.tb_controls.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        self.lbl_transcode = ctk.CTkLabel(self.tb_controls, text="Convert Format:", font=ctk.CTkFont(weight="bold"))
        self.lbl_transcode.grid(row=0, column=0, padx=20, pady=(25, 10), sticky="w")

        self.opt_format = ctk.CTkOptionMenu(self.tb_controls, values=["JPG", "PNG", "WEBP", "BMP"])
        self.opt_format.grid(row=0, column=1, padx=20, pady=(25, 10), sticky="w")

        self.btn_convert = ctk.CTkButton(self.tb_controls, text="Run Conversion", command=self.run_conversion)
        self.btn_convert.grid(row=0, column=2, padx=20, pady=(25, 10), sticky="w")

        self.lbl_scale = ctk.CTkLabel(self.tb_controls, text="Resize / Elongate (px):", font=ctk.CTkFont(weight="bold"))
        self.lbl_scale.grid(row=1, column=0, padx=20, pady=20, sticky="w")

        self.entry_width = ctk.CTkEntry(self.tb_controls, placeholder_text="Width (px)", width=120)
        self.entry_width.grid(row=1, column=1, padx=20, pady=20, sticky="w")

        self.entry_height = ctk.CTkEntry(self.tb_controls, placeholder_text="Height (px)", width=120)
        self.entry_height.grid(row=1, column=2, padx=20, pady=20, sticky="w")

        self.btn_resize = ctk.CTkButton(self.tb_controls, text="Apply Size", command=self.run_resize)
        self.btn_resize.grid(row=1, column=3, padx=20, pady=20, sticky="w")

        self.tb_status = ctk.CTkLabel(self.tb_controls, text="", font=ctk.CTkFont(size=13))
        self.tb_status.grid(row=2, column=0, columnspan=4, padx=20, pady=20, sticky="w")

        # ------------------ Frame 3: Document & Slide Reader ------------------ #
        self.frame_reader = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_reader.grid_columnconfigure(0, weight=1)
        self.frame_reader.grid_rowconfigure(1, weight=1)

        # Reader Top Bar
        self.reader_top = ctk.CTkFrame(self.frame_reader)
        self.reader_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.reader_top.grid_columnconfigure(0, weight=1)

        self.lbl_reader_file = ctk.CTkEntry(
            self.reader_top,
            placeholder_text="Select a PPTX, PDF, or Code/Text document...",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_reader_file.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="ew")

        self.btn_reader_browse = ctk.CTkButton(self.reader_top, text="Open File", width=100, command=self.browse_reader_file)
        self.btn_reader_browse.grid(row=0, column=1, padx=(0, 10), pady=10)

        # Reader Main Content Display Area
        self.txt_reader_view = ctk.CTkTextbox(
            self.frame_reader,
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word"
        )
        self.txt_reader_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.txt_reader_view.insert("0.0", "Open a PPTX presentation, PDF document, or code file to read its contents.\n")

        # Reader Bottom Pagination Bar
        self.reader_nav_bar = ctk.CTkFrame(self.frame_reader)
        self.reader_nav_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

        self.btn_prev_page = ctk.CTkButton(self.reader_nav_bar, text="◀ Previous", width=90, command=self.prev_page)
        self.btn_prev_page.pack(side="left", padx=10, pady=10)

        self.lbl_page_indicator = ctk.CTkLabel(
            self.reader_nav_bar,
            text="No document active",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_page_indicator.pack(side="left", expand=True)

        self.btn_next_page = ctk.CTkButton(self.reader_nav_bar, text="Next ▶", width=90, command=self.next_page)
        self.btn_next_page.pack(side="right", padx=10, pady=10)

    # ------------------ Screen Switching ------------------ #
    def show_frame(self, frame_name: str):
        self.frame_organizer.grid_forget()
        self.frame_toolbox.grid_forget()
        self.frame_reader.grid_forget()

        if frame_name == "organizer":
            self.frame_organizer.grid(row=0, column=1, sticky="nsew")
        elif frame_name == "toolbox":
            self.frame_toolbox.grid(row=0, column=1, sticky="nsew")
        elif frame_name == "reader":
            self.frame_reader.grid(row=0, column=1, sticky="nsew")

    # ------------------ Organizer Logic ------------------ #
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.lbl_selected_dir.delete(0, tk.END)
            self.lbl_selected_dir.insert(0, folder)

    def run_preview(self):
        folder_str = self.lbl_selected_dir.get().strip()
        if not folder_str or not Path(folder_str).is_dir():
            messagebox.showwarning("Invalid Path", "Please select a valid directory first.")
            return

        target_dir = Path(folder_str)
        categories = self.config_data.get("categories", organizer.DEFAULT_CONFIG["categories"])
        logger = organizer.setup_logger(target_dir)
        normal_moves, duplicate_moves = organizer.plan_moves(target_dir, logger, categories)

        self.txt_preview.delete("0.0", tk.END)
        self.txt_preview.insert("end", f"--- SCAN PREVIEW FOR: {target_dir} ---\n\n")

        if not normal_moves and not duplicate_moves:
            self.txt_preview.insert("end", "No loose files found to organize.\n")
            return

        if normal_moves:
            self.txt_preview.insert("end", f"Categorized Files ({len(normal_moves)}):\n")
            for src, dst in normal_moves:
                self.txt_preview.insert("end", f"  {src.name:<30} -> {dst.parent.name}/{dst.name}\n")

        if duplicate_moves:
            self.txt_preview.insert("end", f"\nExact Duplicates Flagged ({len(duplicate_moves)}):\n")
            for src, dst in duplicate_moves:
                self.txt_preview.insert("end", f"  [DUP] {src.name:<24} -> Duplicates/{dst.name}\n")

        self.txt_preview.insert("end", f"\nTotal operations planned: {len(normal_moves) + len(duplicate_moves)}\n")

    def run_execution(self):
        folder_str = self.lbl_selected_dir.get().strip()
        if not folder_str or not Path(folder_str).is_dir():
            messagebox.showwarning("Invalid Path", "Please select a valid directory first.")
            return

        if messagebox.askyesno("Confirm Organize", "Execute planned file moves?"):
            organizer.organize(Path(folder_str), dry_run_only=False, auto_confirm=True)
            messagebox.showinfo("Success", "Files successfully organized.")
            self.run_preview()

    def run_undo(self):
        folder_str = self.lbl_selected_dir.get().strip()
        if not folder_str or not Path(folder_str).is_dir():
            messagebox.showwarning("Invalid Path", "Please select a valid directory first.")
            return

        if messagebox.askyesno("Confirm Undo", "Revert previous organization run?"):
            organizer.undo(Path(folder_str), auto_confirm=True)
            messagebox.showinfo("Reverted", "Directory restored from manifest.")
            self.run_preview()

    # ------------------ Toolbox Logic ------------------ #
    def browse_toolbox_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if file_path:
            self.lbl_tb_file.delete(0, tk.END)
            self.lbl_tb_file.insert(0, file_path)
            self.tb_status.configure(text="")

    def run_conversion(self):
        file_str = self.lbl_tb_file.get().strip()
        if not file_str or not Path(file_str).is_file():
            messagebox.showwarning("Invalid File", "Please select a valid image file first.")
            return

        fmt = self.opt_format.get()
        try:
            out = toolbox.convert_image_format(Path(file_str), fmt)
            self.tb_status.configure(text=f"Converted: {out.name}", text_color="#10b981")
        except Exception as e:
            self.tb_status.configure(text=f"Error: {e}", text_color="#ef4444")

    def run_resize(self):
        file_str = self.lbl_tb_file.get().strip()
        if not file_str or not Path(file_str).is_file():
            messagebox.showwarning("Invalid File", "Please select a valid image file first.")
            return

        try:
            w = int(self.entry_width.get().strip()) if self.entry_width.get().strip() else None
            h = int(self.entry_height.get().strip()) if self.entry_height.get().strip() else None
            if not w and not h:
                messagebox.showwarning("Missing Input", "Provide width, height, or both.")
                return

            out = toolbox.resize_or_elongate_image(Path(file_str), width=w, height=h)
            self.tb_status.configure(text=f"Resized: {out.name}", text_color="#10b981")
        except ValueError:
            messagebox.showerror("Invalid Dimensions", "Width and Height must be integers.")
        except Exception as e:
            self.tb_status.configure(text=f"Error: {e}", text_color="#ef4444")

    # ------------------ Reader Logic ------------------ #
    def browse_reader_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("All Supported Files", "*.pptx *.pdf *.txt *.py *.c *.cpp *.h *.json *.md *.html"),
                ("Presentations", "*.pptx"),
                ("PDF Documents", "*.pdf"),
                ("Code & Text", "*.txt *.py *.c *.cpp *.h *.json *.md *.html")
            ]
        )
        if not file_path:
            return

        path_obj = Path(file_path)
        self.lbl_reader_file.delete(0, tk.END)
        self.lbl_reader_file.insert(0, file_path)

        ext = path_obj.suffix.lower()
        try:
            if ext == ".pptx":
                self.current_doc_type = "pptx"
                self.doc_pages = reader.extract_pptx_slides(path_obj)
            elif ext == ".pdf":
                self.current_doc_type = "pdf"
                self.doc_pages = reader.extract_pdf_pages(path_obj)
            else:
                self.current_doc_type = "text"
                raw_text = reader.read_text_file(path_obj)
                self.doc_pages = [raw_text]

            self.current_page_idx = 0
            self._render_reader_content()
        except Exception as e:
            messagebox.showerror("Read Error", f"Unable to parse file: {e}")

    def _render_reader_content(self):
        if not self.doc_pages:
            self.lbl_page_indicator.configure(text="No document active")
            return

        total_pages = len(self.doc_pages)
        current = self.current_page_idx + 1

        self.txt_reader_view.delete("0.0", tk.END)

        if self.current_doc_type == "pptx":
            slide = self.doc_pages[self.current_page_idx]
            self.lbl_page_indicator.configure(text=f"Slide {current} of {total_pages}")

            content = f"SLIDE {slide['slide_num']}: {slide['title']}\n"
            content += "=" * 60 + "\n\n"
            if slide["body"]:
                for bullet in slide["body"]:
                    content += f"•  {bullet}\n"
            else:
                content += "[No bullet points or text body on this slide]\n"

            if slide["notes"]:
                content += "\n" + "-" * 30 + " SPEAKER NOTES " + "-" * 30 + "\n"
                content += slide["notes"] + "\n"

            self.txt_reader_view.insert("0.0", content)

        elif self.current_doc_type == "pdf":
            self.lbl_page_indicator.configure(text=f"Page {current} of {total_pages}")
            page_text = self.doc_pages[self.current_page_idx]
            header = f"--- PDF PAGE {current} OF {total_pages} ---\n\n"
            self.txt_reader_view.insert("0.0", header + page_text)

        else:
            self.lbl_page_indicator.configure(text=f"Single Document ({len(self.doc_pages[0].splitlines())} lines)")
            self.txt_reader_view.insert("0.0", self.doc_pages[0])

    def prev_page(self):
        if self.doc_pages and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self._render_reader_content()

    def next_page(self):
        if self.doc_pages and self.current_page_idx < len(self.doc_pages) - 1:
            self.current_page_idx += 1
            self._render_reader_content()


if __name__ == "__main__":
    app = SuitcaseApp()
    app.mainloop()