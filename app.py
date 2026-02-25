from flask import Flask, render_template, request, send_file, url_for  
import os                      
from PIL import Image          
import io                      
import time                    

app = Flask(__name__)          

# Konfigurasi folder dan batas ukuran file
app.config['UPLOAD_FOLDER'] = 'uploads'              # Folder hasil kompresi
app.config['PREVIEW_FOLDER'] = 'static/previews'     # Folder preview gambar
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # Batas upload 10 MB

# Membuat folder jika belum tersedia
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PREVIEW_FOLDER'], exist_ok=True)


# LOGIKA LOSSY
def quantization(img, step):
    pixels = img.load()        
    w, h = img.size            

    for x in range(w):       
        for y in range(h):     
            r, g, b = pixels[x, y]  

            pixels[x, y] = (
                (r // step) * step,
                (g // step) * step,
                (b // step) * step
            )
    return img                


def downsample(img, factor):
    w, h = img.size                              
    new_img = Image.new("RGB", (w // factor, h // factor))  

    src = img.load() #pixels citra asli                               
    dst = new_img.load() #pixels citra hasil downsample                      

    for y in range(h // factor):                  
        for x in range(w // factor):
            dst[x, y] = src[x * factor, y * factor] 

    return new_img                                 


# LOGIKA LOSSLESS
def rle_encode(img):
    pixels = list(img.getdata())   
    encoded = []                   

    prev = pixels[0]              
    count = 1                      

    for p in pixels[1:]:        
        if p == prev:              
            count += 1
        else:
            encoded.append((prev, count))  
            prev = p
            count = 1

    encoded.append((prev, count))  
    return encoded                 


def rle_decode(encoded, size):
    data = []                     

    for pixel, count in encoded:   
        data.extend([pixel] * count) 

    img = Image.new("RGB", size)   
    img.putdata(data)              
    return img                     

def clean_old_files():
    """Menghapus file preview yang sudah lama"""
    try:
        now = time.time()          # Waktu saat ini
        for filename in os.listdir(app.config['PREVIEW_FOLDER']):
            filepath = os.path.join(app.config['PREVIEW_FOLDER'], filename)

            # Menghapus file yang lebih dari 1 jam
            if os.path.getctime(filepath) < now - 3600:
                os.remove(filepath)
    except Exception as e:
        print(f"Error cleaning old files: {e}")


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            file = request.files['gambar']          
            if not file:
                return render_template('index.html', error="Tidak ada file yang dipilih")

            img_bytes = file.read()                 
            ukuran_awal = len(img_bytes) / 1024    

            metode = request.form.get('metode')     
            kualitas = request.form.get('kualitas', 'standar')  

            timestamp = int(time.time())            

            # Menyimpan preview sebelum kompresi
            before_name = f"before_{timestamp}_{file.filename}"
            before_path = os.path.join(app.config['PREVIEW_FOLDER'], before_name)
            with open(before_path, 'wb') as f:
                f.write(img_bytes)

            img = Image.open(io.BytesIO(img_bytes)).convert("RGB") 

            # LOGIKA KOMPRESI
            if metode == 'lossy':
                if kualitas == 'standar':
                    img = quantization(img, 16)     
                    jpeg_quality = 75
                else:
                    img = quantization(img, 32)     
                    img = downsample(img, 2)       
                    jpeg_quality = 50
            else:
                encoded = rle_encode(img)           
                img = rle_decode(encoded, img.size)  

            output = io.BytesIO()                    
            
            if metode == 'lossy':
                img.save(output, format='JPEG', quality=jpeg_quality, optimize=True)
                ext = '.jpg'
                metode_text = "Lossy (Quantization + Downsampling)"
                kualitas_text = kualitas.capitalize()
            else:
                img.save(output, format='PNG', optimize=True)
                ext = '.png'
                metode_text = "Lossless (RLE Edukasi)"
                kualitas_text = "-"

            ukuran_akhir = len(output.getvalue()) / 1024  # Ukuran setelah kompresi
            penghematan = round(((ukuran_awal - ukuran_akhir) / ukuran_awal) * 100, 1)
            rasio = round(ukuran_awal / ukuran_akhir, 2)

            filename = f"compressed_{timestamp}_{os.path.splitext(file.filename)[0]}{ext}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            with open(output_path, 'wb') as f:
                f.write(output.getvalue())

            after_name = f"after_{filename}"
            after_path = os.path.join(app.config['PREVIEW_FOLDER'], after_name)
            with open(after_path, 'wb') as f:
                f.write(output.getvalue())

            clean_old_files()  

            return render_template(
                'index.html',
                hasil=True,
                metode=metode_text,
                kualitas=kualitas_text,
                awal=round(ukuran_awal, 1),
                akhir=round(ukuran_akhir, 1),
                penghematan=penghematan,
                rasio=rasio,
                before_img=before_name,
                after_img=after_name,
                nama_file=filename
            )

        except Exception as e:
            return render_template('index.html', error=str(e))

    return render_template('index.html')


@app.route('/download/<filename>')
def download(filename):
    try:
        return send_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return render_template('index.html', error=f"File tidak ditemukan: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
