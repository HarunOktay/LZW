import os
import sys
import struct
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import openpyxl  # Ensure openpyxl is installed

def lzw_compress(uncompressed, max_dict_size=None):
    """
    Compress a string using the LZW algorithm.

    Parameters:
        uncompressed (str): The input string to compress.
        max_dict_size (int, optional): The maximum size of the dictionary.

    Returns:
        List[int]: The list of output codes.
    """
    # Initialize the dictionary with single-character strings.
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    
    w = ""  # Current sequence
    result = []  # List to store output codes
    for c in uncompressed:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            if max_dict_size is None or dict_size < max_dict_size:
                # Add wc to the dictionary only if max size not reached
                dictionary[wc] = dict_size
                dict_size += 1
            w = c
    if w:
        result.append(dictionary[w])
    return result

def save_compressed_file(filename, compressed_data, code_bit_length):
    """
    Save compressed data to a file using bit-packing.

    Parameters:
        filename (str): The name of the output file.
        compressed_data (List[int]): The compressed data to save.
        code_bit_length (int): Number of bits used to represent each code.
    """
    buffer = 0
    bits_in_buffer = 0
    max_code = (1 << code_bit_length) - 1

    with open(filename, 'wb') as f:
        for code in compressed_data:
            if code > max_code:
                raise ValueError(f"Code {code} exceeds the maximum value for {code_bit_length} bits")
            buffer = (buffer << code_bit_length) | code
            bits_in_buffer += code_bit_length
            while bits_in_buffer >= 8:
                bits_in_buffer -= 8
                byte = (buffer >> bits_in_buffer) & 0xFF
                f.write(bytes([byte]))
                buffer &= (1 << bits_in_buffer) - 1
        if bits_in_buffer > 0:
            byte = (buffer << (8 - bits_in_buffer)) & 0xFF
            f.write(bytes([byte]))

def compress_files(file_paths, max_dict_size, code_bit_length):
    """
    Compress multiple files using the LZW algorithm with specified parameters.

    Parameters:
        file_paths (List[str]): A list of file paths to compress.
        max_dict_size (int): Maximum size of the dictionary.
        code_bit_length (int): Number of bits used to represent each code.
    """
    # Create a list to store compression results
    results = []

    # Create output directory name based on parameters
    dict_size_str = f"dict{max_dict_size}" if max_dict_size else "nodictlimit"
    code_length_str = f"code{code_bit_length}bit"
    output_dir_name = f"output_{dict_size_str}_{code_length_str}"
    output_dir_path = os.path.join(os.getcwd(), output_dir_name)

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir_path, exist_ok=True)

    for input_file in file_paths:
        # Ensure the file exists
        if not os.path.isfile(input_file):
            messagebox.showwarning("File Not Found", f"File not found: {input_file}")
            continue

        # Read the input file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
        except Exception as e:
            messagebox.showerror("Read Error", f"Error reading '{input_file}': {e}")
            continue

        # Compress the data
        compressed = lzw_compress(data, max_dict_size)

        # Generate the output file name (without parameters, since directory includes them)
        base_name = os.path.basename(input_file)
        name, _ = os.path.splitext(base_name)
        compressed_file_name = f"{name}.lzw"
        compressed_file = os.path.join(output_dir_path, compressed_file_name)

        # Save the compressed data
        try:
            save_compressed_file(compressed_file, compressed, code_bit_length)
            # Get file sizes
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(compressed_file)
            compression_ratio = compressed_size / original_size if original_size != 0 else 0
            compression_performance = 100 * (1 - compression_ratio)
            # Add the results to the list
            results.append({
                'File Name': base_name,
                'Compressed File': compressed_file_name,
                'Original Size (bytes)': original_size,
                'Compressed Size (bytes)': compressed_size,
                'Compression Ratio': compression_ratio,
                'Compression Performance (%)': compression_performance,
                'Max Dictionary Size': max_dict_size if max_dict_size else 'No Limit',
                'Code Bit Length': code_bit_length
            })
            messagebox.showinfo("Success",
                                f"Compressed '{input_file}' to '{compressed_file}'\n"
                                f"Original Size: {original_size} bytes\n"
                                f"Compressed Size: {compressed_size} bytes\n"
                                f"Compression Ratio: {compression_ratio:.4f}\n"
                                f"Compression Performance: {compression_performance:.2f}%")
        except Exception as e:
            messagebox.showerror("Write Error", f"Error writing '{compressed_file}': {e}")

    # After processing all files, save the results to an Excel file in the output directory
    if results:
        save_results_to_excel(results, output_dir_path, dict_size_str, code_length_str)

def save_results_to_excel(results, output_dir_path, dict_size_str, code_length_str):
    """
    Save the compression results to an Excel file in the output directory.
    """
    # Create a new Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Compression Results"

    # Write the headers
    headers = [
        'File Name',
        'Compressed File',
        'Original Size (bytes)',
        'Compressed Size (bytes)',
        'Compression Ratio',
        'Compression Performance (%)',
        'Max Dictionary Size',
        'Code Bit Length'
    ]
    ws.append(headers)

    # Write each result row
    for result in results:
        ws.append([
            result['File Name'],
            result['Compressed File'],
            result['Original Size (bytes)'],
            result['Compressed Size (bytes)'],
            f"{result['Compression Ratio']:.4f}",
            f"{result['Compression Performance (%)']:.2f}",
            result['Max Dictionary Size'],
            result['Code Bit Length']
        ])

    # Generate Excel file name with parameters
    excel_file_name = f"Compression_Results_{dict_size_str}_{code_length_str}.xlsx"
    excel_file_path = os.path.join(output_dir_path, excel_file_name)

    # Save the workbook
    try:
        wb.save(excel_file_path)
        messagebox.showinfo("Excel File Saved", f"Results saved to '{excel_file_path}'")
    except Exception as e:
        messagebox.showerror("Excel Save Error", f"Error saving Excel file: {e}")

def select_files(entry_dict_size, entry_code_length):
    """
    Open a file dialog to select multiple files for compression and get parameters.

    Parameters:
        entry_dict_size (tk.Entry): Entry widget for max dictionary size.
        entry_code_length (tk.Entry): Entry widget for code bit length.
    """
    # Get parameters
    try:
        max_dict_size = int(entry_dict_size.get()) if entry_dict_size.get() else None
        code_bit_length = int(entry_code_length.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numbers for the parameters.")
        return

    if code_bit_length < 9 or code_bit_length > 24:
        messagebox.showerror("Invalid Code Bit Length", "Code bit length must be between 9 and 24.")
        return

    if max_dict_size and max_dict_size > (1 << code_bit_length):
        messagebox.showerror("Invalid Parameters",
                             "Max Dictionary Size cannot exceed 2^Code Bit Length.")
        return

    file_paths = filedialog.askopenfilenames(title="Select Files to Compress",
                                             filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if file_paths:
        compress_files(file_paths, max_dict_size, code_bit_length)

def create_ui():
    """
    Create the main user interface with parameter inputs.
    """
    root = tk.Tk()
    root.title("LZW Compressor with Parameters")

    # Set window size and position
    window_width = 400
    window_height = 300
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (window_width // 2)
    y_position = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    # Prevent resizing
    root.resizable(False, False)

    # Create a label
    label = tk.Label(root, text="LZW Compression Tool", font=("Arial", 16))
    label.pack(pady=10)

    # Parameter frames
    frame_params = tk.Frame(root)
    frame_params.pack(pady=10)

    # Max Dictionary Size
    label_dict_size = tk.Label(frame_params, text="Max Dictionary Size (Optional):")
    label_dict_size.grid(row=0, column=0, sticky='e', padx=5, pady=5)
    entry_dict_size = tk.Entry(frame_params)
    entry_dict_size.grid(row=0, column=1, padx=5, pady=5)

    # Code Bit Length
    label_code_length = tk.Label(frame_params, text="Code Bit Length (9-24 bits):")
    label_code_length.grid(row=1, column=0, sticky='e', padx=5, pady=5)
    entry_code_length = tk.Entry(frame_params)
    entry_code_length.insert(0, "12")  # Default value
    entry_code_length.grid(row=1, column=1, padx=5, pady=5)

    # Create a button to select files
    select_button = tk.Button(root, text="Select Files to Compress",
                              command=lambda: select_files(entry_dict_size, entry_code_length))
    select_button.pack(pady=20)

    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    create_ui()