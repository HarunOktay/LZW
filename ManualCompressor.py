import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def lzw_compress(uncompressed, max_dict_size=None):
    """LZW sıkıştırma algoritması"""
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

def save_compressed_file(filename, compressed_data, code_bit_length):
    """Sıkıştırılmış veriyi dosyaya kaydet"""
    buffer = 0
    bits_in_buffer = 0
    max_code = (1 << code_bit_length) - 1

    with open(filename, 'wb') as f:
        for code in compressed_data:
            if code > max_code:
                raise ValueError(f"Kod {code}, {code_bit_length} bit için çok büyük")
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

class LZWCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LZW Sıkıştırma Programı")
        
        # Pencere boyutu ve konumu
        window_width = 500
        window_height = 400
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Ana frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Sözlük boyutu seçimi
        ttk.Label(main_frame, text="Maksimum Sözlük Boyutu:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.dict_size_var = tk.StringVar(value="4096")
        dict_size_entry = ttk.Entry(main_frame, textvariable=self.dict_size_var)
        dict_size_entry.grid(row=0, column=1, pady=5, sticky=tk.W)
        
        # Bit uzunluğu seçimi
        ttk.Label(main_frame, text="Kod Bit Uzunluğu:").grid(row=1, column=0, pady=5, sticky=tk.W)
        self.bit_length_var = tk.StringVar(value="12")
        bit_choices = ["12", "16", "20", "24"]
        bit_length_combo = ttk.Combobox(main_frame, textvariable=self.bit_length_var, values=bit_choices, state="readonly")
        bit_length_combo.grid(row=1, column=1, pady=5, sticky=tk.W)
        
        # Dosya seçim düğmesi
        ttk.Button(main_frame, text="Dosya Seç ve Sıkıştır", command=self.compress_file).grid(row=2, column=0, columnspan=2, pady=20)
        
        # Durum mesajları için metin kutusu
        self.status_text = tk.Text(main_frame, height=10, width=50)
        self.status_text.grid(row=3, column=0, columnspan=2, pady=5)
        
    def compress_file(self):
        # Dosya seç
        input_file = filedialog.askopenfilename(
            title="Sıkıştırılacak Dosyayı Seçin",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        
        if not input_file:
            return
            
        try:
            # Parametreleri al
            max_dict_size = int(self.dict_size_var.get())
            code_bit_length = int(self.bit_length_var.get())
            
            # Dosyayı oku
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
            
            # Sıkıştır
            compressed = lzw_compress(data, max_dict_size)
            
            # Çıktı dosya adını oluştur
            dir_path = os.path.dirname(input_file)
            base_name = os.path.basename(input_file)
            name, _ = os.path.splitext(base_name)
            output_dir = f"output_dict{max_dict_size}_code{code_bit_length}bit"
            os.makedirs(os.path.join(dir_path, output_dir), exist_ok=True)
            compressed_file = os.path.join(dir_path, output_dir, f"{name}.lzw")
            
            # Sıkıştırılmış veriyi kaydet
            save_compressed_file(compressed_file, compressed, code_bit_length)
            
            # Sonuçları göster
            original_size = os.path.getsize(input_file)
            compressed_size = os.path.getsize(compressed_file)
            ratio = compressed_size / original_size
            
            status = f"Sıkıştırma tamamlandı!\n\n"
            status += f"Orijinal dosya: {input_file}\n"
            status += f"Sıkıştırılmış dosya: {compressed_file}\n"
            status += f"Orijinal boyut: {original_size} bytes\n"
            status += f"Sıkıştırılmış boyut: {compressed_size} bytes\n"
            status += f"Sıkıştırma oranı: {ratio:.2%}\n"
            
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, status)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Sıkıştırma sırasında hata oluştu: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LZWCompressorGUI(root)
    root.mainloop()