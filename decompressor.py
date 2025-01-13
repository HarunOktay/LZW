import os
import re

def lzw_decompress(compressed_data, code_bit_length, max_dict_size=None):
    """
    LZW decompression algorithm implementation.
    
    Parameters:
        compressed_data (List[int]): List of compressed codes
        code_bit_length (int): Number of bits used for each code
        max_dict_size (int, optional): Maximum dictionary size used during compression
    
    Returns:
        str: Decompressed text
    """
    if not compressed_data:
        return ""

    # Initialize dictionary with ASCII characters
    dict_size = 256
    dictionary = {i: chr(i) for i in range(dict_size)}
    
    # Get the first code and its corresponding character
    result = []
    w = chr(compressed_data.pop(0))
    result.append(w)
    
    # Process remaining codes
    for k in compressed_data:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            # Special case for sequence + sequence[0]
            entry = w + w[0]
        else:
            raise ValueError(f"Invalid compressed code: {k}")
            
        # Add decoded entry to result
        result.append(entry)
        
        # Add new sequence to dictionary if size limit not reached
        if max_dict_size is None or dict_size < max_dict_size:
            dictionary[dict_size] = w + entry[0]
            dict_size += 1
            
        w = entry
    
    return ''.join(result)

def read_compressed_file(file, code_bit_length):
    """
    Read and decode a compressed file.
    
    Parameters:
        file: File object or path (supports both Streamlit uploaded files and regular files)
        code_bit_length (int): Number of bits used for each code
    
    Returns:
        List[int]: List of compressed codes
    """
    compressed_data = []
    buffer = 0
    bits_in_buffer = 0
    max_code = (1 << code_bit_length) - 1
    
    # Handle both Streamlit uploaded files and regular files
    if hasattr(file, 'read'):
        # Streamlit uploaded file
        bytes_data = file.read()
    else:
        # Regular file path
        with open(file, 'rb') as f:
            bytes_data = f.read()
    
    # Process each byte
    for byte in bytes_data:
        buffer = (buffer << 8) | byte
        bits_in_buffer += 8
        
        # Extract codes when we have enough bits
        while bits_in_buffer >= code_bit_length:
            bits_in_buffer -= code_bit_length
            code = (buffer >> bits_in_buffer) & max_code
            compressed_data.append(code)
            buffer &= (1 << bits_in_buffer) - 1
    
    return compressed_data

def extract_compression_params(filepath):
    """
    Extract compression parameters from filepath.
    Expected formats: 
    - output_dict<size>_code<bits>bit/filename.lzw
    - output_nodictlimit_code<bits>bit/filename.lzw
    - output_dict<size>_code<bits>bitfilename.lzw (legacy format)
    
    Parameters:
        filepath (str): Path to the compressed file
    
    Returns:
        tuple: (max_dict_size, code_bit_length) or None if parsing fails
    """
    try:
        # Extract the relevant part containing parameters
        if 'output_' not in filepath:
            return None
            
        # Split the path and get the part with parameters
        parts = filepath.split('output_')[1]
        
        # Find where the parameters end
        if '/' in parts:
            params_part = parts.split('/')[0]
        else:
            # Handle legacy format where parameters and filename are together
            # Find 'bit' and consider everything before it + 'bit' as parameters
            if 'bit' in parts:
                bit_index = parts.find('bit') + 3  # +3 to include 'bit'
                params_part = parts[:bit_index]
            else:
                return None
        
        # Parse dictionary size
        if 'nodictlimit' in params_part:
            max_dict_size = None
        else:
            # Extract number after 'dict' and before '_code'
            dict_part = params_part.split('_code')[0]
            max_dict_size = int(dict_part.replace('dict', ''))
        
        # Parse code bit length
        if 'code' not in params_part:
            return None
        code_part = params_part.split('code')[1]
        code_bit_length = int(code_part.replace('bit', ''))
        
        return max_dict_size, code_bit_length
            
    except Exception as e:
        print(f"Error parsing parameters from filepath: {str(e)}")
        return None

def decompress_file(compressed_file, output_file=None, max_dict_size=None, code_bit_length=None):
    """
    Decompress a file and save the result.
    
    Parameters:
        compressed_file: File path or Streamlit uploaded file
        output_file (str, optional): Path to save decompressed file
        max_dict_size (int, optional): Maximum dictionary size
        code_bit_length (int, optional): Number of bits per code
    
    Returns:
        str: Decompressed text content
    """
    try:
        # If parameters not provided, try to extract from filepath
        if max_dict_size is None or code_bit_length is None:
            params = extract_compression_params(
                compressed_file.name if hasattr(compressed_file, 'name') else compressed_file
            )
            if params:
                max_dict_size, code_bit_length = params
            else:
                raise ValueError("Could not determine compression parameters")
        
        # Read and decompress the file
        compressed_data = read_compressed_file(compressed_file, code_bit_length)
        decompressed_text = lzw_decompress(compressed_data, code_bit_length, max_dict_size)
        
        # Save to file if output path provided
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(decompressed_text)
        
        return decompressed_text
        
    except Exception as e:
        raise Exception(f"Decompression failed: {str(e)}")

def validate_compressed_file(file_path):
    """
    Validate that a file appears to be a valid LZW compressed file.
    
    Parameters:
        file_path (str): Path to the compressed file
    
    Returns:
        bool: True if file appears valid, False otherwise
    """
    try:
        # Check file extension
        if not file_path.lower().endswith('.lzw'):
            return False
            
        # Check file size
        if os.path.getsize(file_path) == 0:
            return False
            
        # Check if parameters can be extracted
        params = extract_compression_params(file_path)
        if params is None:
            return False
            
        return True
        
    except Exception:
        return False 