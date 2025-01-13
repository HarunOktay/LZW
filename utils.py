import os
import pandas as pd
import streamlit as st
from compressor import lzw_compress, save_compressed_file

def process_files(uploaded_files, dict_size, code_bit_length, output_dir):
    """
    Process uploaded files and save results to Excel
    
    Returns:
        tuple: (compressed_data_dict, results_list) where compressed_data_dict maps filenames to their compressed data
    """
    results = []
    compressed_files = {}
    
    for uploaded_file in uploaded_files:
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            original_size = len(content.encode('utf-8'))
            
            # Compress data
            compressed = lzw_compress(content, dict_size)
            
            # Generate output filename with parameters in the path
            base_name = os.path.splitext(uploaded_file.name)[0]
            # Format: output_dict<size>_code<bits>bit/filename.lzw
            dict_size_str = f"dict{dict_size}" if dict_size else "nodictlimit"
            code_length_str = f"code{code_bit_length}bit"
            output_subdir = f"output_{dict_size_str}_code{code_bit_length}bit"
            compressed_file = os.path.join(output_subdir, f"{base_name}.lzw")
            
            # Ensure output directory exists
            os.makedirs(output_subdir, exist_ok=True)
            
            # Save compressed file and get the binary data
            compressed_data = save_compressed_file(compressed_file, compressed, code_bit_length, return_data=True)
            # Store with the full path for download
            compressed_files[compressed_file] = compressed_data
            
            # Calculate metrics
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size
            compression_performance = 100 * (1 - compression_ratio)
            
            result = {
                'File Name': uploaded_file.name,
                'Compressed File': compressed_file,  # Store full path
                'Original Size (bytes)': original_size,
                'Compressed Size (bytes)': compressed_size,
                'Compression Ratio': compression_ratio,
                'Compression Performance (%)': compression_performance,
                'Max Dictionary Size': 'No Limit' if dict_size is None else dict_size,
                'Code Bit Length': code_bit_length
            }
            results.append(result)
            
        except Exception as e:
            raise Exception(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Save results to Excel in the last used output directory
    if results:
        df = pd.DataFrame(results)
        excel_file = os.path.join(output_subdir, 'compression_results.xlsx')
        df.to_excel(excel_file, index=False)
    
    return compressed_files, results
@st.cache_data
def load_results():
    """
    Load and cache compression results from Excel files
    """
    try:
        excel_file = 'Aggregated_Compression_Results.xlsx'
        if os.path.exists(excel_file):
            return pd.read_excel(excel_file)
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
    return None
