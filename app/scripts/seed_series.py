import re
import sys
import io
import argparse
import requests
import time

# Windows konsolunda Unicode karakter hatalarini onlemek icin
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app
from app.db import db
from app.models.series import Series


def fetch_page(page_number):
    """TVMaze API'den belirtilen sayfa numarasındaki dizileri çeker."""
    url = f'https://api.tvmaze.com/shows?page={page_number}'
    response = requests.get(url)
    return response


def process_show(show):
    """Tek bir dizi verisini işleyip Series nesnesi döndürür. Zaten varsa None döner."""
    title = show.get('name')
    if not title:
        return None

    # Veritabanında bu isimde dizi var mı kontrol et
    existing_series = Series.query.filter_by(title=title).first()
    if existing_series:
        return None

    # HTML taglerini temizle
    raw_summary = show.get('summary', 'Açıklama bulunmuyor.')
    clean_summary = re.sub('<[^<]+>', '', raw_summary) if raw_summary else 'Açıklama bulunmuyor.'

    # Görsel URL'si
    image_info = show.get('image')
    image_url = image_info.get('original') if image_info else None

    # Puan bilgisi
    rating_info = show.get('rating')
    rating = rating_info.get('average') if rating_info else None

    # Yayın yılı
    premiered = show.get('premiered')
    release_year = int(premiered[:4]) if premiered else None

    # Türler
    genres = show.get('genres', [])
    genre_str = ", ".join(genres) if genres else "Bilinmiyor"

    return Series(
        title=title,
        description=clean_summary,
        image_url=image_url,
        rating=rating,
        release_year=release_year,
        genre=genre_str,
        status=show.get('status', 'Bilinmiyor'),
        number_of_seasons=None,
        number_of_episodes=None,
        trailer_url=show.get('officialSite')
    )


def seed_series(max_pages=10):
    """
    TVMaze API'den sayfalama ile dizi çeker.
    Her sayfa yaklaşık 250 dizi içerir.
    
    Args:
        max_pages: Çekilecek maksimum sayfa sayısı (varsayılan: 10, ~2500 dizi)
    """
    app = create_app()
    with app.app_context():
        db.create_all()

        total_added = 0
        total_skipped = 0

        print(f"TVMaze'den diziler çekiliyor (maksimum {max_pages} sayfa, ~{max_pages * 250} dizi)...\n")

        for page in range(max_pages):
            print(f"--- Sayfa {page + 1}/{max_pages} çekiliyor... ---")

            response = fetch_page(page)

            # 404 = sayfa yok, daha fazla veri kalmamış demektir
            if response.status_code == 404:
                print(f"Sayfa {page} bulunamadı. Tüm veriler çekildi.")
                break

            if response.status_code != 200:
                print(f"Hata: Sayfa {page} çekilemedi. Durum Kodu: {response.status_code}")
                continue

            shows = response.json()
            page_added = 0

            for show in shows:
                new_series = process_show(show)
                if new_series:
                    db.session.add(new_series)
                    page_added += 1
                    print(f"  [+] {new_series.title}")
                else:
                    total_skipped += 1

            # Her sayfadan sonra veritabanına kaydet
            db.session.commit()
            total_added += page_added
            print(f"  Sayfa {page + 1} tamamlandı: {page_added} yeni dizi eklendi.\n")

            # API rate-limit aşmamak için kısa bekleme
            if page < max_pages - 1:
                time.sleep(0.5)

        print("=" * 50)
        print(f"İşlem Tamamlandı!")
        print(f"  Toplam eklenen : {total_added} dizi")
        print(f"  Atlanan (mevcut): {total_skipped} dizi")
        print("=" * 50)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TVMaze API\'den dizi verilerini çeker.')
    parser.add_argument(
        '--pages', type=int, default=10,
        help='Çekilecek sayfa sayısı (her sayfa ~250 dizi, varsayılan: 10)'
    )
    args = parser.parse_args()
    seed_series(max_pages=args.pages)
