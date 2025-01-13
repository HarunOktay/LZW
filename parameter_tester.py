import pandas as pd
from compressor import lzw_compress, save_compressed_file
import tempfile
import os

def test_parameters(test_file, dict_sizes, bit_lengths, progress_callback=None):
    """
    Test different compression parameters on a file and return results with theoretical dictionary storage impact
    """
    results = []
    content = test_file.getvalue().decode('utf-8')
    original_size = len(content.encode('utf-8'))
    total_tests = len(dict_sizes)
    
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        for i, (dict_size, bit_length) in enumerate(zip(dict_sizes, bit_lengths)):
            try:
                # Skip invalid combinations
                if dict_size and dict_size > (1 << bit_length):
                    continue
                    
                # Compress with current parameters
                compressed = lzw_compress(content, dict_size)
                
                # Save to temporary file
                temp_file = os.path.join(temp_dir, "temp.lzw")
                save_compressed_file(temp_file, compressed, bit_length, return_data=True)
                
                # Calculate actual compression metrics
                compressed_size = os.path.getsize(temp_file)
                
                # Calculate theoretical dictionary storage size
                if dict_size is None:
                    actual_dict_size = len(set(compressed))  # Number of unique codes used
                else:
                    actual_dict_size = min(dict_size, len(set(compressed)))
                
                # Each dictionary entry needs: 
                # - character (8 bits)
                # - code value (bit_length bits)
                theoretical_dict_size = actual_dict_size * (8 + bit_length) // 8  # in bytes
                
                # Total size including dictionary
                total_size_with_dict = compressed_size + theoretical_dict_size
                
                # Calculate both compression ratios
                compression_ratio = compressed_size / original_size
                compression_ratio_with_dict = total_size_with_dict / original_size
                
                # Calculate both compression performances
                compression_performance = 100 * (1 - compression_ratio)
                compression_performance_with_dict = 100 * (1 - compression_ratio_with_dict)
                
                results.append({
                    'Max Dictionary Size': 'No Limit' if dict_size is None else dict_size,
                    'Code Bit Length': bit_length,
                    'Original Size (bytes)': original_size,
                    'Compressed Size (bytes)': compressed_size,
                    'Dictionary Size (bytes)': theoretical_dict_size,
                    'Total Size with Dict (bytes)': total_size_with_dict,
                    'Compression Ratio': compression_ratio,
                    'Compression Ratio with Dict': compression_ratio_with_dict,
                    'Compression Performance (%)': compression_performance,
                    'Compression Performance with Dict (%)': compression_performance_with_dict,
                    'Max Possible Dict Size': (1 << bit_length) - 1
                })
                
                # Update progress
                if progress_callback:
                    progress_callback((i + 1) / total_tests)
                    
            except Exception as e:
                print(f"Error testing parameters (dict_size={dict_size}, bit_length={bit_length}): {str(e)}")
                continue
    
    return pd.DataFrame(results) 