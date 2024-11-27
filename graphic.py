import os
import pandas as pd
import matplotlib.pyplot as plt

def create_charts():
    # Excel dosyasını okuma
    excel_file = 'Aggregated_Compression_Results.xlsx'
    if not os.path.exists(excel_file):
        print(f"Excel dosyası '{excel_file}' bulunamadı.")
        return

    df = pd.read_excel(excel_file)

    # 'Max Dictionary Size' sütunundaki 'No Limit' değerlerini uygun şekilde işleme
    df['Max Dictionary Size'] = df['Max Dictionary Size'].replace('No Limit', float('inf'))
    df['Max Dictionary Size'] = df['Max Dictionary Size'].astype(float)

    # Klasör oluşturma
    output_dir = 'Charts'
    os.makedirs(output_dir, exist_ok=True)

    # Tüm benzersiz dosya adları için döngü
    for file_name in df['File Name'].unique():
        df_file = df[df['File Name'] == file_name]

        # Tüm benzersiz Code Bit Length değerleri için döngü
        for code_bit_length in df_file['Code Bit Length'].unique():
            df_cbl = df_file[df_file['Code Bit Length'] == code_bit_length]

            # Max Dictionary Size'a göre sıralama
            df_cbl_sorted = df_cbl.sort_values('Max Dictionary Size')

            # Grafik oluşturma
            plt.figure(figsize=(10, 6))
            plt.plot(df_cbl_sorted['Max Dictionary Size'], df_cbl_sorted['Compression Performance (%)'], marker='o')

            # Başlık ve etiketler
            plt.title(f"{file_name} - Code Bit Length: {code_bit_length}")
            plt.xlabel('Max Dictionary Size')
            plt.ylabel('Compression Performance (%)')
            plt.grid(True)

            # Grafiği kaydetme
            sanitized_file_name = file_name.replace(' ', '_').replace('.', '_')
            chart_filename = f"{sanitized_file_name}_CodeBitLength_{code_bit_length}.png"
            chart_filepath = os.path.join(output_dir, chart_filename)
            plt.savefig(chart_filepath)
            plt.close()

            print(f"Grafik oluşturuldu ve kaydedildi: {chart_filepath}")

if __name__ == "__main__":
    create_charts()