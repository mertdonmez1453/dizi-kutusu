import requests
from app import create_app
from app.db import db
from app.models.series import Series

def seed_series():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("TVMaze'den diziler çekiliyor...")
        
        # Sadece popüler dizileri getiren bir endpoint kullanıyoruz (ilk sayfa, 250 dizi)
        response = requests.get('https://api.tvmaze.com/shows')
        
        if response.status_code != 200:
            print(f"Hata: API'ye bağlanılamadı. Durum Kodu: {response.status_code}")
            return
            
        shows = response.json()
        added_count = 0
        
        for show in shows:
            # Sadece başlığı olan geçerli dizileri al
            title = show.get('name')
            if not title:
                continue
                
            # Veritabanında bu isimde dizi var mı kontrol et
            existing_series = Series.query.filter_by(title=title).first()
            if existing_series:
                print(f"[{title}] zaten veritabanında mevcut, atlanıyor.")
                continue
                
            # Gelen html içerikli summary verisinden HTML taglerini temizleyelim
            import re
            raw_summary = show.get('summary', 'Açıklama bulunmuyor.')
            clean_summary = re.sub('<[^<]+>', '', raw_summary) if raw_summary else 'Açıklama bulunmuyor.'
            
            # API'den gelen verileri modelimize uyarlıyoruz
            image_info = show.get('image')
            image_url = image_info.get('original') if image_info else None
            
            rating_info = show.get('rating')
            rating = rating_info.get('average') if rating_info else None
            
            # Yayın yılı için prömiyer tarihinin ilk 4 hanesi
            premiered = show.get('premiered')
            release_year = int(premiered[:4]) if premiered else None
            
            genres = show.get('genres', [])
            genre_str = ", ".join(genres) if genres else "Bilinmiyor"
            
            # Veritabanına kaydedilecek obje oluşturuluyor
            new_series = Series(
                title=title,
                description=clean_summary,
                image_url=image_url,
                rating=rating,
                release_year=release_year,
                genre=genre_str,
                status=show.get('status', 'Bilinmiyor'),
                # TVMaze API ana "/shows" url'sinde sezon/bölüm sayısı detaylı gelmez. 
                # Bunlar default kalsın, gerekirse daha detaylı api isteği atılır.
                number_of_seasons=None,
                number_of_episodes=None,
                trailer_url=show.get('officialSite') # Orijinal sitesini fragman URL yerine saklayabiliriz
            )
            
            db.session.add(new_series)
            added_count += 1
            print(f"[{title}] eklendi.")
            
        # Değişiklikleri veritabanına kaydet (toplu kaydet)
        db.session.commit()
        print(f"\nİşlem Tamamlandı! Toplam {added_count} yeni dizi eklendi.")

if __name__ == '__main__':
    seed_series()
