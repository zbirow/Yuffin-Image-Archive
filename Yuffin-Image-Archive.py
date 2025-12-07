import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import struct
import os
from pathlib import Path
import threading
import re

# --- File Format Constants (v3.1) ---
MAGIC_HEADER = b'Yuffin'
MAGIC_BLOCK = b'ZBIR'
VERSION = 3.1
ALIGNMENT = 16
MAX_FILE_SIZE_32BIT = 2**32 - 1 

# --- Struct Format Strings (v3.0) ---
HEADER_FORMAT_V3 = '<6sfQIQQ'
BLOCK_PREFIX_FORMAT = '<4sI'
FILE_INDEX_ENTRY_FORMAT_V3 = '<IH2s'

# --- Natural Sorting Function ---
def natural_sort_key(s):
    """Sortuje liczby numerycznie, a nie leksykograficznie."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', str(s))]

# --- Core Logic Functions (v3.1) ---

def pack_images_v3(source_dir, output_file, log_callback):
    """Packs images recursively from a source directory into a single v3 .yufi file."""
    try:
        source_path = Path(source_dir).resolve()
        log_callback(f"Scanning '{source_path.name}'...")
        
        image_files = [p for p in source_path.rglob('*') if p.is_file()]
        # Wykluczamy pliki .yufi z pakowania samych siebie, jeśli są w folderze źródłowym
        image_files = [p for p in image_files if p.suffix != '.yufi']
        image_files = sorted(image_files, key=lambda x: natural_sort_key(x.relative_to(source_path)))
        
        if not image_files:
            log_callback(f"No files found in '{source_dir}'. Skipping.")
            return

        dir_to_id = {}
        next_dir_id = 0
        for p in image_files:
            relative_parent = p.relative_to(source_path).parent
            if relative_parent not in dir_to_id:
                dir_to_id[relative_parent] = next_dir_id
                next_dir_id += 1
        
        sorted_dirs = sorted(dir_to_id.items(), key=lambda item: item[1])
        
        output_file_path = Path(output_file)
        output_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'wb') as f:
            f.write(b'\0' * struct.calcsize(HEADER_FORMAT_V3))
            
            directory_table_offset = f.tell()
            for path_obj, dir_id in sorted_dirs:
                dir_name = path_obj.as_posix()
                if dir_name == '.': dir_name = '' 
                f.write(dir_name.encode('utf-8') + b'\0')
            
            current_pos = f.tell()
            if current_pos % ALIGNMENT != 0:
                f.write(b'\0' * (ALIGNMENT - (current_pos % ALIGNMENT)))
            
            file_index_offset = f.tell()
            f.write(b'\0' * (len(image_files) * struct.calcsize(FILE_INDEX_ENTRY_FORMAT_V3)))

            file_index_entries = []
            for i, image_path in enumerate(image_files):
                if len(image_files) < 20 or i % 10 == 0:
                    relative_path_str = str(image_path.relative_to(source_path))
                
                current_pos = f.tell()
                if current_pos % ALIGNMENT != 0:
                    f.write(b'\0' * (ALIGNMENT - (current_pos % ALIGNMENT)))
                
                block_start_offset = f.tell()
                if block_start_offset >= MAX_FILE_SIZE_32BIT: raise MemoryError("Archive size exceeds 4GB limit!")
                
                image_data = image_path.read_bytes()
                f.write(struct.pack(BLOCK_PREFIX_FORMAT, MAGIC_BLOCK, len(image_data)))
                f.write(image_data)
                
                relative_parent = image_path.relative_to(source_path).parent
                dir_id = dir_to_id[relative_parent]
                file_index_entries.append((block_start_offset, dir_id))

            f.seek(file_index_offset)
            for offset, dir_id in file_index_entries:
                f.write(struct.pack(FILE_INDEX_ENTRY_FORMAT_V3, offset, dir_id, b'\0\0'))

            f.seek(0)
            final_header = struct.pack(HEADER_FORMAT_V3, MAGIC_HEADER, VERSION, len(image_files), len(dir_to_id), directory_table_offset, file_index_offset)
            f.write(final_header)

        log_callback(f"-> Created: {Path(output_file).name} ({len(image_files)} files)")
    except Exception as e:
        log_callback(f"\nERROR in {Path(source_dir).name}: {e}")

def pack_images_multi(root_source_dir, log_callback):
    """Iterates over subdirectories in root_source_dir and packs them individually."""
    try:
        root_path = Path(root_source_dir).resolve()
        log_callback(f"--- Starting Multi-Pack in: {root_path} ---")
        
        subdirs = [d for d in root_path.iterdir() if d.is_dir()]
        subdirs = sorted(subdirs, key=lambda x: natural_sort_key(x.name))
        
        if not subdirs:
            log_callback("No subdirectories found to pack.")
            return

        for i, subdir in enumerate(subdirs):
            archive_name = f"{subdir.name}.yufi"
            output_path = root_path / archive_name
            
            log_callback(f"\nProcessing [{i+1}/{len(subdirs)}]: {subdir.name}")
            pack_images_v3(subdir, output_path, log_callback)
            
        log_callback("\n--- Multi-Pack Finished Successfully ---")
        
    except Exception as e:
        log_callback(f"CRITICAL ERROR: {e}")

def unpack_images_v3(pack_file, output_dir, log_callback):
    """Unpacks images from a v3 .yufi file."""
    try:
        output_path = Path(output_dir)
        
        with open(pack_file, 'rb') as f:
            header_size = struct.calcsize(HEADER_FORMAT_V3)
            header_data = f.read(header_size)
            magic, version, img_count, dir_count, dir_table_offset, file_index_offset = struct.unpack(HEADER_FORMAT_V3, header_data)
            
            if magic != MAGIC_HEADER: raise ValueError("This is not a valid Yuffin file.")
            
            log_callback(f"Unpacking: {Path(pack_file).name} (v{version:.1f}, Files: {img_count})")
            
            f.seek(dir_table_offset)
            dir_table_data = f.read(file_index_offset - dir_table_offset)
            directories = [d.decode('utf-8') for d in dir_table_data.split(b'\0')[:-1]]
            
            f.seek(file_index_offset)
            for i in range(img_count):
                entry_data = f.read(struct.calcsize(FILE_INDEX_ENTRY_FORMAT_V3))
                offset, dir_id, _ = struct.unpack(FILE_INDEX_ENTRY_FORMAT_V3, entry_data)
                
                f_current_pos = f.tell()
                f.seek(offset)
                
                prefix_data = f.read(struct.calcsize(BLOCK_PREFIX_FORMAT))
                block_magic, image_size = struct.unpack(BLOCK_PREFIX_FORMAT, prefix_data)
                
                if block_magic != MAGIC_BLOCK:
                    f.seek(f_current_pos)
                    continue
                    
                image_data = f.read(image_size)
                
                extension = ".dat"
                if image_data.startswith(b'\xff\xd8'): extension = ".jpg"
                elif image_data.startswith(b'\x89PNG\r\n\x1a\n'): extension = ".png"
                elif image_data.startswith(b'GIF'): extension = ".gif"
                
                dir_name = directories[dir_id] if dir_id < len(directories) else ''
                final_dir = output_path / dir_name
                final_dir.mkdir(parents=True, exist_ok=True)
                
                output_filename = final_dir / f"image_{i+1:06d}{extension}"
                output_filename.write_bytes(image_data)
                
                f.seek(f_current_pos)
            
        log_callback(f"Done extracting to '{output_dir}'.")
    except Exception as e:
        log_callback(f"\nERROR: {e}")
        
class YuffinPackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yuffin Image Archive")
        self.root.geometry("650x500")

        self.pack_source_dir = tk.StringVar()
        self.pack_output_file = tk.StringVar()
        self.unpack_source_file = tk.StringVar()
        self.unpack_output_dir = tk.StringVar()
        
        self.is_multipack = tk.BooleanVar(value=False)

        # --- PACK FRAME ---
        pack_frame = tk.LabelFrame(root, text="Pack Images", padx=10, pady=10)
        pack_frame.pack(padx=10, pady=10, fill="x")
        
        # Source Row
        tk.Label(pack_frame, text="Source Folder:").grid(row=0, column=0, sticky="w")
        tk.Entry(pack_frame, textvariable=self.pack_source_dir, width=50).grid(row=0, column=1)
        tk.Button(pack_frame, text="Browse...", command=self.select_pack_source).grid(row=0, column=2, padx=5)
        
        # Multi-Pack Checkbox
        tk.Checkbutton(pack_frame, text="Multi-Packer Mode (Create separate .yufi for each subfolder)", 
                       variable=self.is_multipack, command=self.toggle_pack_mode).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        # Output Row (will be disabled in multi mode)
        tk.Label(pack_frame, text="Output File:").grid(row=2, column=0, sticky="w")
        self.entry_output = tk.Entry(pack_frame, textvariable=self.pack_output_file, width=50)
        self.entry_output.grid(row=2, column=1)
        self.btn_output = tk.Button(pack_frame, text="Save As...", command=self.select_pack_dest)
        self.btn_output.grid(row=2, column=2, padx=5)
        
        # Pack Button
        tk.Button(pack_frame, text="PACK", command=self.run_pack, font=('Arial', 10, 'bold'), bg="#dddddd").grid(row=3, column=1, pady=10)

        # --- UNPACK FRAME ---
        unpack_frame = tk.LabelFrame(root, text="Unpack Archive", padx=10, pady=10)
        unpack_frame.pack(padx=10, pady=10, fill="x")
        tk.Label(unpack_frame, text="Archive File:").grid(row=0, column=0, sticky="w")
        tk.Entry(unpack_frame, textvariable=self.unpack_source_file, width=50).grid(row=0, column=1)
        tk.Button(unpack_frame, text="Browse...", command=self.select_unpack_source).grid(row=0, column=2, padx=5)
        tk.Label(unpack_frame, text="Output Folder:").grid(row=1, column=0, sticky="w")
        tk.Entry(unpack_frame, textvariable=self.unpack_output_dir, width=50).grid(row=1, column=1)
        tk.Button(unpack_frame, text="Browse...", command=self.select_unpack_dest).grid(row=1, column=2, padx=5)
        tk.Button(unpack_frame, text="UNPACK", command=self.run_unpack, font=('Arial', 10, 'bold'), bg="#dddddd").grid(row=2, column=1, pady=10)

        # --- LOG FRAME ---
        log_frame = tk.LabelFrame(root, text="Log", padx=10, pady=10)
        log_frame.pack(padx=10, pady=5, fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=10)
        self.log_text.pack(fill="both", expand=True)
        
    def toggle_pack_mode(self):
        """Włącza/wyłącza pole wyboru pliku wyjściowego w zależności od trybu Multi-Packer"""
        if self.is_multipack.get():
            self.entry_output.config(state='disabled')
            self.btn_output.config(state='disabled')
            self.pack_output_file.set("(Auto-generated filenames)")
        else:
            self.entry_output.config(state='normal')
            self.btn_output.config(state='normal')
            self.pack_output_file.set("")

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def select_pack_source(self):
        dir_path = filedialog.askdirectory(title="Select Source Folder")
        if dir_path: self.pack_source_dir.set(dir_path)

    def select_pack_dest(self):
        if self.is_multipack.get(): return
        file_path = filedialog.asksaveasfilename(title="Save Archive As", defaultextension=".yufi", filetypes=[("Yuffin Archive", "*.yufi")])
        if file_path: self.pack_output_file.set(file_path)

    def select_unpack_source(self):
        file_path = filedialog.askopenfilename(title="Select Archive File", filetypes=[("Yuffin Archive", "*.yufi")])
        if file_path: self.unpack_source_file.set(file_path)

    def select_unpack_dest(self):
        dir_path = filedialog.askdirectory(title="Select Output Folder")
        if dir_path: self.unpack_output_dir.set(dir_path)

    def run_pack(self):
        src = self.pack_source_dir.get()
        is_multi = self.is_multipack.get()
        
        if not src:
            messagebox.showerror("Error", "Please select a source folder!")
            return

        self.log_text.config(state='normal'); self.log_text.delete(1.0, tk.END); self.log_text.config(state='disabled')

        if is_multi:
            thread = threading.Thread(target=pack_images_multi, args=(src, self.log))
            thread.start()
        else:
            dest = self.pack_output_file.get()
            if not dest or dest == "(Auto-generated filenames)":
                messagebox.showerror("Error", "Please select an output file!")
                return
            thread = threading.Thread(target=pack_images_v3, args=(src, dest, self.log))
            thread.start()

    def run_unpack(self):
        src = self.unpack_source_file.get()
        dest = self.unpack_output_dir.get()
        if not src or not dest: messagebox.showerror("Error", "Please select an archive file and an output folder!"); return
        self.log_text.config(state='normal'); self.log_text.delete(1.0, tk.END); self.log_text.config(state='disabled')
        thread = threading.Thread(target=unpack_images_v3, args=(src, dest, self.log))
        thread.start()

if __name__ == "__main__":
    main_root = tk.Tk()
    app = YuffinPackerApp(main_root)
    main_root.mainloop()
