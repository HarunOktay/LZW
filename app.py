import streamlit as st
import os
import pandas as pd
from compressor import lzw_compress, save_compressed_file
from decompressor import lzw_decompress, read_compressed_file, extract_compression_params, decompress_file
from visualizer import create_performance_chart
from utils import process_files, load_results
from parameter_tester import test_parameters
import numpy as np

def main():
    st.set_page_config(page_title="LZW Compression Tool", layout="wide")
    st.title("LZW Compression Tool")

    # Sidebar for compression parameters
    with st.sidebar:
        st.header("Compression Parameters")
        
        # Code bit length input first (since dictionary size depends on it)
        code_bit_length = st.select_slider(
            "Code Bit Length",
            options=[9, 12, 16, 20, 24],
            value=12,
            help="Number of bits used to represent each code"
        )

        # Calculate maximum possible dictionary size for selected bit length
        max_possible_dict_size = (1 << code_bit_length) - 1
        
        # Dictionary size input with slider
        dict_size = st.slider(
            "Max Dictionary Size",
            min_value=256,
            max_value=max_possible_dict_size,
            value=min(4096, max_possible_dict_size),
            step=256,
            help=f"Maximum value limited by Code Bit Length (current max: {max_possible_dict_size})"
        )
        
        no_limit = st.checkbox("No Dictionary Size Limit")
        if no_limit:
            dict_size = None

    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "Manual Compression", 
        "File Decompression",
        "Parameter Testing"
    ])

    with tab1:
        st.header("Manual Compression")
        uploaded_files = st.file_uploader(
            "Choose text files to compress",
            accept_multiple_files=True,
            type=['txt']
        )

        if uploaded_files and st.button("Compress Selected Files"):
            try:
                # Process files and get compressed data
                compressed_files, results = process_files(uploaded_files, dict_size, code_bit_length, ".")
                
                if compressed_files and results:
                    st.success("Compression completed successfully!")
                    st.dataframe(pd.DataFrame(results))
                    
                    # Offer compressed file downloads
                    st.subheader("Download Compressed Files")
                    for filepath, compressed_data in compressed_files.items():
                        # Extract just the filename for display
                        filename = os.path.basename(filepath)
                        directory = os.path.dirname(filepath)
                        
                        st.markdown(f"**Directory:** `{directory}`")
                        st.download_button(
                            label=f"Download {filename}",
                            data=compressed_data,
                            file_name=filepath,  # Use full path as filename
                            mime="application/octet-stream",
                            key=filepath  # Unique key for each button
                        )
                        st.markdown("---")
                    
            except Exception as e:
                st.error(f"Compression error: {str(e)}")

    with tab2:
        st.header("File Decompression")
        uploaded_compressed_files = st.file_uploader(
            "Choose compressed files to decompress",
            accept_multiple_files=True,
            type=['lzw']
        )

        if uploaded_compressed_files and st.button("Decompress Selected Files"):
            for compressed_file in uploaded_compressed_files:
                try:
                    # Get directory name from file path
                    file_path = compressed_file.name
                    
                    # Extract parameters from filename
                    params = extract_compression_params(file_path)
                    if params:
                        dict_size, code_bit_length = params
                        
                        # Decompress the file
                        decompressed_data = decompress_file(
                            compressed_file,
                            max_dict_size=dict_size,
                            code_bit_length=code_bit_length
                        )
                        
                        # Create download button for decompressed file
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        # Remove the output_dictXXXX_codeXXbit prefix if present
                        if base_name.startswith('output_'):
                            base_name = base_name.split('/')[-1]
                        
                        st.download_button(
                            label=f"Download decompressed {base_name}",
                            data=decompressed_data,
                            file_name=f"{base_name}_decompressed.txt",
                            mime="text/plain",
                            key=f"decomp_{base_name}"
                        )
                        
                        # Show success message with file details
                        st.success(f"""
                        Successfully decompressed {base_name}
                        - Dictionary Size: {'No Limit' if dict_size is None else dict_size}
                        - Code Bit Length: {code_bit_length}
                        - Decompressed Size: {len(decompressed_data.encode('utf-8'))} bytes
                        """)
                        
                    else:
                        st.error(f"Could not extract parameters from filename: {file_path}")
                except Exception as e:
                    st.error(f"Error decompressing {compressed_file.name}: {str(e)}")

    with tab3:
        st.header("Parameter Testing")
        test_file = st.file_uploader(
            "Choose a file to test parameters",
            type=['txt']
        )
        
        if test_file:
            col1, col2 = st.columns(2)
            
            with col1:
                test_mode = st.radio(
                    "Testing Mode",
                    ["Quick Test", "Custom Test"]
                )
                
            if test_mode == "Quick Test":
                # Let user select which bit lengths to test
                selected_bits = st.multiselect(
                    "Select Code Bit Lengths to Test",
                    [9, 12, 16, 20, 24],
                    default=[12, 16]
                )
                
                if selected_bits:
                    # Generate comprehensive test parameters for each bit length
                    test_params = {}
                    for bit_length in selected_bits:
                        max_size = (1 << bit_length) - 1
                        
                        # Generate logarithmically spaced dictionary sizes
                        # Using numpy's logspace to create exponentially increasing values
                        log_sizes = np.logspace(
                            np.log10(256),  # start from 256
                            np.log10(max_size),  # up to max_size
                            100,  # number of points
                            dtype=int
                        )
                        
                        # Convert to list and remove duplicates
                        sizes = list(dict.fromkeys(log_sizes))
                        
                        # Ensure important values are included
                        important_sizes = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
                        sizes.extend([size for size in important_sizes if size <= max_size])
                        
                        # Remove duplicates and sort
                        sizes = sorted(list(set(sizes)))
                        
                        # Add None (No Limit) option at the end
                        sizes.append(None)
                        
                        # Show distribution of test points
                        if len(sizes) > 1:
                            numeric_sizes = [s for s in sizes if s is not None]
                            intervals = [numeric_sizes[i+1] - numeric_sizes[i] for i in range(len(numeric_sizes)-1)]
                            avg_interval_start = sum(intervals[:5]) / 5
                            avg_interval_end = sum(intervals[-5:]) / 5
                            
                            st.info(f"""
                            For {bit_length}-bit encoding:
                            - Number of test points: {len(sizes)}
                            - Average interval at start: {avg_interval_start:.0f}
                            - Average interval at end: {avg_interval_end:.0f}
                            - Ratio (end/start): {avg_interval_end/avg_interval_start:.1f}x
                            """)
                        
                        test_params[bit_length] = sizes
                    
                    # Show test configuration
                    total_tests = sum(len(sizes) for sizes in test_params.values())
                    st.info(f"""
                    Overall Test Configuration:
                    - Total number of tests: {total_tests}
                    - Bit lengths to test: {selected_bits}
                    - Tests per bit length: ~{total_tests // len(selected_bits)}
                    """)
                    
                    if st.button("Run Comprehensive Test"):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Flatten parameters for testing
                        all_dict_sizes = []
                        all_bit_lengths = []
                        for bit_length, dict_sizes in test_params.items():
                            all_dict_sizes.extend(dict_sizes)
                            all_bit_lengths.extend([bit_length] * len(dict_sizes))
                        
                        with st.spinner("Testing parameters..."):
                            # Update progress as tests run
                            test_results = test_parameters(
                                test_file, 
                                all_dict_sizes, 
                                all_bit_lengths,
                                progress_callback=lambda p: (
                                    progress_bar.progress(p),
                                    status_text.text(f"Testing: {int(p * 100)}% complete")
                                )
                            )
                            
                            progress_bar.progress(100)
                            status_text.text("Testing completed!")
                            
                            # Show results
                            st.success("Parameter testing completed!")
                            
                            # Show best results for each bit length
                            st.subheader("Best Results by Bit Length")
                            for bit_length in selected_bits:
                                bit_results = test_results[test_results['Code Bit Length'] == bit_length]
                                best_result = bit_results.loc[bit_results['Compression Performance (%)'].idxmax()]
                                
                                st.markdown(f"""
                                **{bit_length}-bit encoding:**
                                - Best Dictionary Size: {best_result['Max Dictionary Size']}
                                - Compression Performance: {best_result['Compression Performance (%)']:.2f}%
                                - Compression Ratio: {best_result['Compression Ratio']:.3f}
                                """)
                            
                            # Show detailed results in a dataframe
                            st.subheader("All Test Results")
                            st.dataframe(test_results)
                            
                            # Create and show visualization
                            st.subheader("Performance Visualization")
                            fig = create_performance_chart(test_results)
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Please select at least one bit length to test")
                    
            else:  # Custom Test
                with col1:
                    selected_bit_length = st.selectbox(
                        "Select Code Bit Length",
                        [9, 12, 16, 20, 24],
                        index=1
                    )
                    
                    max_possible_size = (1 << selected_bit_length) - 1
                    st.info(f"Maximum possible dictionary size: {max_possible_size}")
                    
                    custom_dict_sizes = st.text_input(
                        "Enter Dictionary Sizes (comma-separated)",
                        "256, 512, 1024, 2048, 4096, None"
                    )
                    
                    try:
                        dict_sizes = [
                            None if size.strip().lower() == 'none' 
                            else int(size.strip()) 
                            for size in custom_dict_sizes.split(',')
                        ]
                    except ValueError:
                        st.error("Invalid dictionary sizes")
                        dict_sizes = []
                
                if st.button("Run Custom Test"):
                    if dict_sizes:
                        with st.spinner("Testing parameters..."):
                            test_results = test_parameters(
                                test_file, 
                                dict_sizes, 
                                [selected_bit_length]
                            )
                            show_test_results(test_results)
                    else:
                        st.error("Please enter valid dictionary sizes")

def show_test_results(test_results):
    """Display test results and visualizations"""
    st.subheader("Test Results")
    st.dataframe(test_results)
    
    # Show best parameters
    best_result = test_results.loc[test_results['Compression Performance (%)'].idxmax()]
    st.success(f"""
    Best parameters found:
    - Dictionary Size: {best_result['Max Dictionary Size']}
    - Code Bit Length: {best_result['Code Bit Length']}
    - Compression Performance: {best_result['Compression Performance (%)']:.2f}%
    """)
    
    # Create and show visualization
    st.subheader("Performance Visualization")
    fig = create_performance_chart(test_results)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
