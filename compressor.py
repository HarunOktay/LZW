def lzw_compress(uncompressed, max_dict_size=None):
    """
    LZW compression algorithm implementation
    """
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    
    w = ""
    result = []
    
    for c in uncompressed:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            if max_dict_size is None or dict_size < max_dict_size:
                dictionary[wc] = dict_size
                dict_size += 1
            w = c
    
    if w:
        result.append(dictionary[w])
    return result

def save_compressed_file(filename, compressed_data, code_bit_length, return_data=False):
    """
    Save compressed data to file using bit-packing.
    
    Parameters:
        filename (str): Output file path
        compressed_data (List[int]): Compressed codes
        code_bit_length (int): Number of bits per code
        return_data (bool): If True, return the binary data
        
    Returns:
        bytes: Compressed binary data if return_data is True
    """
    buffer = 0
    bits_in_buffer = 0
    max_code = (1 << code_bit_length) - 1
    output_bytes = bytearray()

    for code in compressed_data:
        if code > max_code:
            raise ValueError(f"Code {code} exceeds maximum value for {code_bit_length} bits")
        buffer = (buffer << code_bit_length) | code
        bits_in_buffer += code_bit_length
        while bits_in_buffer >= 8:
            bits_in_buffer -= 8
            byte = (buffer >> bits_in_buffer) & 0xFF
            output_bytes.append(byte)
            buffer &= (1 << bits_in_buffer) - 1
    
    if bits_in_buffer > 0:
        byte = (buffer << (8 - bits_in_buffer)) & 0xFF
        output_bytes.append(byte)

    # Convert to bytes
    binary_data = bytes(output_bytes)
    
    # Save to file
    with open(filename, 'wb') as f:
        f.write(binary_data)
    
    if return_data:
        return binary_data
