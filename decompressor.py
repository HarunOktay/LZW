import os
import sys
import struct
import tkinter as tk
from tkinter import filedialog, messagebox

def lzw_decompress(compressed_data, code_bit_length, max_dict_size=None):
    """
    Decompress a list of output codes to a string using the LZW algorithm.

    Parameters:
        compressed_data (List[int]): The list of compressed codes.
        code_bit_length (int): Number of bits used to represent each code.
        max_dict_size (int, optional): The maximum size of the dictionary.
                                        If None, the dictionary can grow indefinitely.

    Returns:
        str: The decompressed string.
    """
    # Reconstruct the dictionary.
    dict_size = 256
    max_code = (1 << code_bit_length) - 1
    dictionary = {i: chr(i) for i in range(dict_size)}

    result = []

    w = chr(compressed_data.pop(0))
    result.append(w)
    for k in compressed_data:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0]
        else:
            raise ValueError(f"Bad compressed k: {k}")
        result.append(entry)

        # Add w+entry[0] to the dictionary.
        if max_dict_size is None or dict_size < max_dict_size:
            dictionary[dict_size] = w + entry[0]
            dict_size += 1

        w = entry
    return ''.join(result)

def read_compressed_file(filename, code_bit_length):
    """
    Read compressed data from a file using bit-packing.

    Parameters:
        filename (str): The name of the compressed file.
        code_bit_length (int): Number of bits used to represent each code.

    Returns:
        List[int]: The list of compressed codes.
    """
    compressed_data = []
    bits_in_buffer = 0
    buffer = 0
    max_code = (1 << code_bit_length) - 1

    with open(filename, 'rb') as f:
        byte = f.read(1)
        while byte:
            buffer = (buffer << 8) | ord(byte)
            bits_in_buffer += 8
            while bits_in_buffer >= code_bit_length:
                bits_in_buffer -= code_bit_length
                code = (buffer >> bits_in_buffer) & max_code
                compressed_data.append(code)
                buffer &= (1 << bits_in_buffer) - 1
            byte = f.read(1)
    return compressed_data

def decompress_files(file_paths):
    """
    Decompress multiple files using the LZW algorithm.

    Parameters:
        file_paths (List[str]): A list of compressed file paths to decompress.
    """
    for compressed_file in file_paths:
        try:
            # Extract parameters from the directory name
            dir_path = os.path.dirname(compressed_file)
            dir_name = os.path.basename(dir_path)
            # Expected format: output_dict<max_dict_size>_code<code_bit_length>bit
            import re
            match = re.match(r'output_(dict\d+|nodictlimit)_code(\d+)bit', dir_name)
            if match:
                dict_size_str = match.group(1)
                code_length_str = match.group(2)

                # Convert parameters to appropriate types
                max_dict_size = None if dict_size_str == 'nodictlimit' else int(dict_size_str.replace('dict', ''))
                code_bit_length = int(code_length_str)
            else:
                messagebox.showerror("Error", f"Cannot extract parameters from directory name: {dir_name}")
                continue

            # Read the compressed data
            compressed_data = read_compressed_file(compressed_file, code_bit_length)

            # Decompress the data
            decompressed_data = lzw_decompress(compressed_data, code_bit_length, max_dict_size)

            # Save the decompressed file
            base_name = os.path.basename(compressed_file)
            name, _ = os.path.splitext(base_name)
            decompressed_file_name = f"{name}_decompressed.txt"
            decompressed_file_path = os.path.join(dir_path, decompressed_file_name)

            with open(decompressed_file_path, 'w', encoding='utf-8') as f:
                f.write(decompressed_data)

            messagebox.showinfo("Success",
                                f"Decompressed '{compressed_file}' to '{decompressed_file_path}'")
        except Exception as e:
            messagebox.showerror("Decompression Error", f"An error occurred while decompressing '{compressed_file}': {e}")

def select_files():
    """
    Open a file dialog to select multiple compressed files for decompression.
    """
    file_paths = filedialog.askopenfilenames(title="Select Compressed Files to Decompress",
                                             filetypes=[("LZW Compressed Files", "*.lzw"), ("All Files", "*.*")])
    if file_paths:
        decompress_files(file_paths)

def create_ui():
    """
    Create the main user interface for the decompressor.
    """
    root = tk.Tk()
    root.title("LZW Decompressor")

    # Set window size and position
    window_width = 400
    window_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Prevent resizing
    root.resizable(False, False)

    # Create a label
    label = tk.Label(root, text="LZW Decompression Tool", font=("Arial", 16))
    label.pack(pady=20)

    # Create a button to select files
    select_button = tk.Button(root, text="Select Files to Decompress",
                              command=select_files)
    select_button.pack(pady=20)

    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    create_ui()