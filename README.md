# Dizi Kutusu

Flask tabanlı dizi puanlama ve yorumlama uygulaması.

## Gereksinimler

- Python 3.10+

## Kurulum

### 1. Depoyu klonlayın

```bash
git clone https://github.com/mertdonmez1453/dizi-kutusu.git
cd dizi-kutusu
```

### 2. Sanal ortam oluşturun

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Bağımlılıkları yükleyin

```bash
pip install -r requirements.txt
```

### 4. Uygulamayı başlatın

```bash
python run.py
```

> Bu komut veritabanını ve tabloları otomatik olarak oluşturur.
> Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır.

### 5. (Opsiyonel) Dizi verilerini yükleyin

Veritabanına TVMaze API'den örnek dizi verisi eklemek için:

```bash
python -m app.scripts.seed_series --pages 5
```

`--pages` parametresi kaç sayfa veri çekileceğini belirler (her sayfa ~250 dizi).

## Test

```bash
pytest
```
