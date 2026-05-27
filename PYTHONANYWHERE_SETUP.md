# Deploy Jee Cell ke PythonAnywhere (GRATIS)

## Langkah-langkah:

### 1. Daftar PythonAnywhere
- Buka https://www.pythonanywhere.com
- Klik "Create a Beginner account" (GRATIS, tanpa kartu kredit)

### 2. Upload Code
- Buka tab "Files" di PythonAnywhere
- Klik "Open Bash console here" di folder home
- Jalankan:
```bash
git clone https://github.com/Rikotriono46/jee-cell.git
cd jee-cell
pip install --user -r requirements.txt
```

### 3. Setup Web App
- Buka tab "Web" → klik "Add a new web app"
- Pilih "Manual configuration"
- Pilih "Python 3.10" (atau versi terbaru yang tersedia)

### 4. Edit WSGI Configuration
- Klik link "WSGI configuration file" di tab Web
- Ganti isi file dengan:
```python
import sys
import os

project_home = '/home/YOUR_USERNAME/jee-cell'  # Ganti YOUR_USERNAME
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['SECRET_KEY'] = 'rahasia-anda-di-sini'

from app import app as application
```

### 5. Set Working Directory
- Di tab Web, cari "Working directory"
- Set ke: `/home/YOUR_USERNAME/jee-cell`

### 6. Reload
- Klik tombol "Reload" di tab Web
- Website kamu akan live di: `https://YOUR_USERNAME.pythonanywhere.com`

## Admin Login
- URL: `https://YOUR_USERNAME.pythonanywhere.com/admin/login`
- Username: admin
- Password: jeecell2024

## Tips
- PythonAnywhere free tier: web app sleep setelah 90 detik tidak aktif
- Bangun pertama kali butuh beberapa detik untuk "wake up"
- Bisa custom domain di paid plan
