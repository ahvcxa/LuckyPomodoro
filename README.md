# 🍀 Multiplayer Pomodoro

Gelişmiş, gerçek zamanlı çok kullanıcılı Pomodoro uygulaması. Arkadaşlarınızla birlikte odaklanın ve verimliliğinizi artırın!

## ✨ Özellikler

- **🎨 Modern Yeşil Tema**: Göz yormayan, ferah emerald/green tonları
- **🍀 Yonca Logosu**: Belirgin ve şık tasarım
- **⏱️ Doğru Zamanlama**: Target Timestamp mantığı ile süre asla kaymaz
- **⚙️ Ayarlanabilir Süreler**: Çalışma, Kısa Mola, Uzun Mola sürelerini özelleştirin
- **👥 Gerçek Zamanlı Senkronizasyon**: WebSocket ile anlık veri akışı
- **🔄 Canlı Kullanıcı Listesi**: Odadaki tüm kullanıcıları görün
- **🌐 İnternet Erişimi**: Yerel ağ ve internet üzerinden erişim desteği

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# Gerekli paketleri yükleyin
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın

```bash
# Uygulamayı başlat (0.0.0.0 ile yerel ağdaki cihazlardan erişilebilir)
python main.py
```

Veya uvicorn ile:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Tarayıcıda Açın

```
http://localhost:8000
```

## 🌐 Arkadaşlarla İnternet Üzerinden Oynamak İçin Ngrok Kullanımı

Ngrok, yerel sunucunuzu internet üzerinden erişilebilir hale getiren bir araçtır. Böylece arkadaşlarınız uzaktan odaya katılabilir.

### Adım 1: Ngrok'u İndirin ve Kurun

1. [Ngrok'un resmi sitesine](https://ngrok.com/) gidin
2. Ücretsiz hesap oluşturun (gerekli)
3. İndirme sayfasından işletim sisteminize uygun versiyonu indirin
4. İndirdiğiniz dosyayı açın ve kurulum talimatlarını takip edin

### Adım 2: Ngrok Authtoken'ı Ayarlayın

Ngrok hesabınızdan aldığınız authtoken'ı terminalde çalıştırın:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### Adım 3: FastAPI Uygulamanızı Başlatın

Bir terminal penceresinde:

```bash
python main.py
```

Uygulamanız `http://localhost:8000` adresinde çalışıyor olmalı.

### Adım 4: Ngrok Tünelini Başlatın

Başka bir terminal penceresinde:

```bash
ngrok http 8000
```

Ngrok size bir URL verecek, örneğin:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

### Adım 5: Arkadaşlarınızı Davet Edin

Ngrok'un verdiği HTTPS URL'sini (örn: `https://abc123.ngrok-free.app`) arkadaşlarınızla paylaşın. Onlar bu URL'yi tarayıcılarında açarak odaya katılabilirler!

### ⚠️ Önemli Notlar

- **Ücretsiz Ngrok**: Ücretsiz plan sınırlı süre ve bağlantı sayısına sahiptir. Her Ngrok başlatıldığında URL değişir.
- **Güvenlik**: Ngrok URL'nizi sadece güvendiğiniz kişilerle paylaşın.
- **Alternatifler**: 
  - **Cloudflare Tunnel**: Ücretsiz ve sınırsız
  - **LocalTunnel**: Başka bir ücretsiz alternatif
  - **Serveo**: SSH tabanlı basit çözüm

### Ngrok Alternatifi: Cloudflare Tunnel (Önerilen)

Cloudflare Tunnel daha stabil ve ücretsizdir:

```bash
# Cloudflare Tunnel kurulumu
# 1. cloudflared indirin: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
# 2. Tunnel oluşturun:
cloudflared tunnel --url http://localhost:8000
```

## 🌍 Ücretsiz İnternet Hosting Seçenekleri

Uygulamanızı ücretsiz olarak internete yayınlamak için birkaç harika seçenek var:

### 1. Render (En Kolay ve Önerilen) ⭐

Render, FastAPI uygulamaları için mükemmel ücretsiz hosting sağlar.

**Adımlar:**

1. **Render hesabı oluşturun**: [render.com](https://render.com) adresine gidin ve ücretsiz hesap oluşturun

2. **Yeni Web Service oluşturun**:
   - Dashboard'da "New +" → "Web Service" seçin
   - GitHub repo'nuzu bağlayın VEYA "Manual Deploy" seçin

3. **Ayarları yapılandırın**:
   ```
   Name: multiplayer-pomodoro (veya istediğiniz isim)
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Deploy edin**: Render otomatik olarak deploy edecek ve size bir URL verecek (örn: `https://multiplayer-pomodoro.onrender.com`)

5. **WebSocket için ekstra ayar (ÖNEMLİ)**:
   - Render dashboard'da servisinizin "Settings" sekmesine gidin
   - "Headers" bölümüne şunu ekleyin:
     ```
     Key: Upgrade
     Value: websocket
     ```
   - VEYA daha kolay yol: Environment Variables'a şunu ekleyin:
     ```
     Key: WEBSOCKET_ENABLED
     Value: true
     ```

**Avantajlar:**
- ✅ Tamamen ücretsiz (Free tier)
- ✅ Otomatik HTTPS
- ✅ Kolay kurulum
- ✅ GitHub entegrasyonu (otomatik deploy)
- ✅ WebSocket desteği (ekstra ayar ile)

**Önemli Notlar:**
- ⚠️ **Ücretsiz plan**: 15 dakika kullanılmazsa uyku moduna geçer, ilk istekte tekrar başlar (30 saniye gecikme olabilir)
- ✅ **Link direkt çalışır**: Deploy tamamlandıktan sonra verilen linki tarayıcıda açtığınızda uygulama çalışır
- ✅ **HTTPS otomatik**: Render otomatik olarak HTTPS sağlar (güvenli bağlantı)
- ✅ **WebSocket çalışır**: Yukarıdaki ayarları yaptıktan sonra WebSocket bağlantıları sorunsuz çalışır

---

### 2. Railway (Modern ve Hızlı)

Railway, modern bir platform ve kolay deployment sağlar.

**Adımlar:**

1. **Railway hesabı oluşturun**: [railway.app](https://railway.app) adresine gidin

2. **Yeni proje oluşturun**:
   - "New Project" → "Deploy from GitHub repo" VEYA "Empty Project"

3. **GitHub repo'nuzu bağlayın** (veya dosyaları yükleyin)

4. **Railway otomatik olarak algılayacak** ve deploy edecek

5. **Settings'ten PORT değişkenini ayarlayın** (genelde otomatik)

**Avantajlar:**
- ✅ Ücretsiz kredi ($5/ay)
- ✅ Çok hızlı deploy
- ✅ Otomatik HTTPS
- ✅ Kolay GitHub entegrasyonu

---

### 3. Fly.io (Güçlü ve Esnek)

Fly.io, küresel dağıtım sağlar.

**Adımlar:**

1. **Fly.io CLI'ı yükleyin**: [fly.io/docs/getting-started/installing-flyctl/](https://fly.io/docs/getting-started/installing-flyctl/)

2. **Hesap oluşturun ve giriş yapın**:
   ```bash
   fly auth signup
   ```

3. **Proje klasöründe `fly.toml` dosyası oluşturun**:
   ```toml
   app = "multiplayer-pomodoro"
   primary_region = "iad"

   [build]
     builder = "paketobuildpacks/builder:base"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0

   [[services]]
     http_checks = []
     internal_port = 8000
     processes = ["app"]
     protocol = "tcp"
     script_checks = []
   ```

4. **Deploy edin**:
   ```bash
   fly deploy
   ```

**Avantajlar:**
- ✅ Ücretsiz tier (3 küçük VM)
- ✅ Küresel CDN
- ✅ Çok hızlı

---

### 4. PythonAnywhere (Basit ve Doğrudan)

PythonAnywhere, Python uygulamaları için özel bir platformdur.

**Adımlar:**

1. **Hesap oluşturun**: [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Files sekmesinden dosyalarınızı yükleyin**

3. **Web sekmesinden yeni web app oluşturun**

4. **WSGI dosyasını düzenleyin**:
   ```python
   import sys
   path = '/home/kullaniciadi/multiplayer-pomodoro'
   if path not in sys.path:
       sys.path.append(path)

   from main import app
   application = app
   ```

5. **Reload butonuna tıklayın**

**Avantajlar:**
- ✅ Python'a özel
- ✅ Basit arayüz
- ⚠️ Ücretsiz plan bazı kısıtlamalara sahip

---

### 5. Replit (En Kolay Başlangıç)

Replit, tarayıcıda kod yazıp deploy etmenizi sağlar.

**Adımlar:**

1. **Replit hesabı oluşturun**: [replit.com](https://replit.com)

2. **Yeni Repl oluşturun**: "Python" seçin

3. **Dosyalarınızı yükleyin** (drag & drop)

4. **Packages sekmesinden paketleri yükleyin**:
   ```
   fastapi
   uvicorn
   websockets
   jinja2
   python-multipart
   ```

5. **Run butonuna tıklayın** - Replit otomatik olarak bir URL verecek

**Avantajlar:**
- ✅ Tarayıcıda çalışır
- ✅ Çok kolay kurulum
- ✅ Anında deploy

---

### 🎯 Hangi Platformu Seçmeliyim?

- **Yeni başlayanlar için**: **Render** veya **Replit** (en kolay)
- **GitHub kullanıyorsanız**: **Render** veya **Railway** (otomatik deploy)
- **Daha fazla kontrol istiyorsanız**: **Fly.io**
- **Python'a özel platform**: **PythonAnywhere**

### 📝 Genel Deployment Notları

Tüm platformlarda dikkat edilmesi gerekenler:

1. **PORT değişkeni**: Çoğu platform `$PORT` veya `PORT` environment variable kullanır. `main.py` dosyasını şu şekilde güncelleyebilirsiniz:
   ```python
   import os
   port = int(os.environ.get("PORT", 8000))
   uvicorn.run(app, host="0.0.0.0", port=port)
   ```

2. **WebSocket desteği**: Tüm platformlar WebSocket'i destekler, ancak bazılarında ekstra yapılandırma gerekebilir.

3. **Static dosyalar**: `static/` klasörü varsa, platform ayarlarından static file serving'i etkinleştirin.

## 📖 Kullanım

### Oda Oluşturma ve Katılma

1. Ana sayfada adınızı girin
2. Oda ID'sini boş bırakarak yeni oda oluşturun VEYA
3. Mevcut bir oda ID'si ile odaya katılın

### Timer Kontrolleri

- **▶️ Başlat**: Timer'ı başlatır (odadaki herkes senkronize başlar)
- **⏸️ Durdur**: Timer'ı durdurur
- **🔄 Sıfırla**: Timer'ı seçili moda göre sıfırlar

### Modlar

- **💼 Çalışma**: Ana çalışma süresi
- **☕ Kısa Mola**: Kısa mola süresi
- **🏖️ Uzun Mola**: Uzun mola süresi

### Süre Ayarları

1. "Süre Ayarları" kartındaki input alanlarına istediğiniz süreleri girin (dakika cinsinden)
2. "Ayarları Uygula" butonuna tıklayın
3. Ayarlar odadaki tüm kullanıcılara anında uygulanır

### Davet Linki

"📋 Linki Kopyala" butonu ile oda linkini kopyalayıp arkadaşlarınızla paylaşabilirsiniz.

## 🏗️ Teknik Detaylar

### Target Timestamp Mantığı

Uygulama, doğru zamanlama için "Target Timestamp" mantığını kullanır:

- Sunucu timer başlatıldığında **bitiş zamanını** (target timestamp) hesaplar
- Frontend sadece kalan süreyi gösterir (target timestamp - şu anki zaman)
- Bu sayede süre asla kaymaz veya hızlanmaz
- Ağ gecikmeleri timer'ı etkilemez

### WebSocket Mesaj Tipleri

**Client → Server:**
- `start_timer`: Timer'ı başlat
- `stop_timer`: Timer'ı durdur
- `reset_timer`: Timer'ı sıfırla (mode parametresi ile)
- `update_settings`: Süre ayarlarını güncelle

**Server → Client:**
- `timer_state`: Mevcut timer durumu
- `timer_started`: Timer başlatıldı
- `timer_stopped`: Timer durduruldu
- `timer_reset`: Timer sıfırlandı
- `settings_updated`: Ayarlar güncellendi
- `user_joined`: Kullanıcı katıldı
- `user_left`: Kullanıcı ayrıldı
- `user_list_update`: Kullanıcı listesi güncellendi

## 🎨 Özelleştirme

### Renkler

TailwindCSS kullanıldığı için `templates/index.html` dosyasındaki Tailwind sınıflarını değiştirerek renkleri özelleştirebilirsiniz. Şu anki tema: Emerald/Green (500-900).

### Varsayılan Süreler

`main.py` dosyasındaki şu değişkenleri değiştirerek varsayılan süreleri ayarlayabilirsiniz:

```python
DEFAULT_WORK_DURATION = 25 * 60      # 25 dakika
DEFAULT_SHORT_BREAK = 5 * 60         # 5 dakika
DEFAULT_LONG_BREAK = 15 * 60         # 15 dakika
```

### Port

Varsayılan port 8000'dir. `main.py` dosyasının sonundaki `uvicorn.run()` çağrısında değiştirebilirsiniz.

## 🐛 Sorun Giderme

### WebSocket Bağlantı Hatası

- Sunucunun çalıştığından emin olun
- Firewall ayarlarını kontrol edin
- Port 8000'in başka bir uygulama tarafından kullanılmadığından emin olun

### Timer Senkronize Değil

- Sayfayı yenileyin
- WebSocket bağlantısını kontrol edin (tarayıcı konsolunda)
- Tüm kullanıcıların aynı oda ID'sine sahip olduğundan emin olun

### Ngrok Bağlantı Sorunları

- Ngrok authtoken'ın doğru ayarlandığından emin olun
- Ücretsiz plan limitlerini kontrol edin
- Alternatif olarak Cloudflare Tunnel kullanmayı deneyin

## 📄 Lisans

Bu proje eğitim amaçlıdır ve özgürce kullanılabilir.

---

**Keyifli çalışmalar! 🍀✨**
