# Çalıştırma rehberi

Ana kurulum yolu kökteki `README.md` dosyasındadır. Önce paketi yeni klasöre çıkar, `Atlas_2026_Aday.html` ile görsel incele, ardından Python 3.12 ile `setup.ps1` çalıştır.

## Sorun giderme

| Belirti | Yapılacak |
|---|---|
| ZIP indirilemiyor | Paylaşılan yeni dosya sayfasındaki İndir düğmesini kullan; eski sandbox bağlantısı farklıdır. |
| `input_axes` veya sürüm hatası | Python 3.12 ve tam `requirements.txt`; farklı Python'daki `pip` yerine `.venv` içindeki Python'u kullan. |
| Sürüm dosyası eksik/uyuşmuyor | Aynı güvenilir teslimin model ve preprocess dosyalarını birlikte geri getir; doğrulama kontrolünü kapatma. |
| API modu boş/hata gösteriyor | `/health` adresini kontrol et; veritabanı veya etkin yayın yoksa 503 beklenir. |
| HTTP 409 | Sayfa yüklenirken etkin yayın değişmiştir; sayfayı yenile. |
| Geçmiş hedef tarihi | Arşiv tahminidir; bugünün hava sıcaklığı tahmini değildir. |
| Aday çıktı zaten var | Eski sonucu koru, yeni bir `--out` / `--output` klasörü seç. |
| Earth Engine erişim hatası | `docs/GEE_KURULUM.md`; giriş ve proje seçimini kendin yap. |
| Docker şifre değişkeni eksik | `LST_DB_PASSWORD` değerini kendi terminalinde ayarla; repoya yazma. |

Önceki Git bundle aktarım talimatları `docs/archive/CALISTIRMA_Onceki.md` içindedir. Yeni kurulum için gerekli değildir.

## Veri kaybını önleme

Bu teslimde önceki veri/model dosyaları değiştirilmedi. Yeni deneyler ayrı klasörlerde. Bilgisayarında eski klasörün üzerine açmak yerine iki klasörü yan yana tut. Çalışan veritabanını silme, `docker compose down -v` kullanma ve yeni şemayı mevcut veritabanına onaysız uygulama.
