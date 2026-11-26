# Türkiye Yüzey Sıcaklığı Atlası

MODIS il ortalamalarıyla 81 ilde zamansal tahmin; İstanbul, Erzurum ve Antalya'da Landsat/Sentinel tabanlı mekânsal model karşılaştırması. LST **yüzey sıcaklığıdır**, meteorolojik hava sıcaklığı değildir.

Bu geliştirme paketi 24 Kasım 2026 tarihli inceleme sürümüdür. Mevcut `data/`, `models/` ve eski deney sonuçları korunmuştur. 2026 gözlemleri `results/revision/incoming/` altında ayrı aday veridir. GitHub'a push veya kullanıcının veritabanında değişiklik yapılmamıştır.

## İlk açılış

ZIP'i **yeni bir klasöre** çıkar. Yeni arayüz ve 2026 aday veri incelemesi için `Atlas_2026_Aday.html` dosyasını tarayıcıda aç. Kurulum veya hesap girişi gerekmez. Bu dosyanın açılması veritabanına veri yayımlamaz. `Atlas.html` önceki teslimin korunmuş arşividir.

## Python kurulumu ve doğrulama

Windows 11'de Python **3.12** kurulu olmalı. Proje kökünde PowerShell:

```powershell
.\setup.ps1
```

Betik çalıştırma politikası izin vermiyorsa sistem politikasını değiştirmeden aynı adımları elle çalıştır:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:KERAS_BACKEND = "jax"
.\.venv\Scripts\python scripts/check_environment.py
.\.venv\Scripts\python -m unittest discover -s tests -v
```

Python/Keras/JAX sürümleri kayıtlı modellerle birlikte sabitlenmiştir. Başka sürümde `input_axes` hatasını bastırmak için initializer yapılandırmasını değiştirmeyin. `compile=False` yükleme korunmuştur; eksik/bozuk sürüm dosyası artık yüklemeyi reddeder.

Linux Python 3.12 ortamında 32 test geçti. **Bu kullanıcının Windows bilgisayarında kurulum henüz çalıştırılmadı.** `setup.ps1` ortam ve test kayıtlarını `results/local-validation/` altında üretir. Windows CI işi de hazırdır; depoya gönderilmediğinden yeni CI çalışması henüz yoktur.

## Dosya ve sonuç rehberi

| Yol | İçerik |
|---|---|
| `DUZELTME_TAKIBI.md` | 30 madde için dosya, gerekçe, test ve açık durum |
| `DENEY_RAPORU.md` | Güncel bulgular, sınırlar ve tekrar komutları |
| `docs/GEE_KURULUM.md` | Kendi hesabında yapacağın Earth Engine kurulumu |
| `docs/SUNUM.md` | Bulgulara dayalı sunum akışı |
| `docs/archive/` | Önceki kılavuz ve raporlar |
| `results/revision/climate/` | Köppen–Geiger sınıflarıyla 81 il ve iki dönem için test özeti |
| `results/revision/diagnostics/` | İl, ufuk, mevsim, sıcak dönem ve güven aralıkları |
| `results/revision/spatial-blocked/` | Eğitim içinde mekânsal bloklarla seçilen A/B modelleri |
| `results/revision/temporal-2026/` | Eski modellerin yeni 2026 gözlemlerindeki testi |
| `results/revision/unseen-provinces/` | Üç pilot il eğitim/doğrulama dışında bırakılan deney |
| `results/revision/benchmark-real/` | 2.666.362 gerçek piksel, süre/CPU/RSS ölçümleri |
| `results/verification/` | Gerçekten çalıştırılmış test ve tarama kayıtları |

## Aday veri ve tahmin hazırlama

Aşağıdaki komutlar yeni klasörlere yazar; mevcut arşivi veya etkin yayını değiştirmez. Node.js ve `web/` altında `npm ci` çevrimdışı pano derlemesi için gerekir.

```powershell
.\.venv\Scripts\python scripts/data_quality.py results/revision/incoming/province-modis-2026.csv
.\.venv\Scripts\python scripts/run_update.py --province-data results/revision/incoming/province-modis-2026.csv
```

Çıktı `releases/<kimlik>/` içinde CSV'ler, `snapshot.json`, `manifest.json` ve `Atlas.html` içerir. Kimlikteki saat UTC'dir. Yeni dosya var olan bir yayınla birleştirilmez. `--no-build` yalnızca hazırlık/test için HTML derlemesini atlar.

**Etkinleştirme ayrı ve onay gerektiren bir işlemdir.** `run_update.py --activate ...` çevrimdışı işaretçiyi; `--activate ... --publish` veritabanı işaretçisini değiştirir. Veritabanı modu API için tek yetkili kaynaktır. HTML, sürümlü ve bağımsız bir rapor dosyasıdır. Burada bu komutlar kullanıcının sisteminde çalıştırılmadı.

## Web ve API geliştirme

```powershell
cd web
npm ci
npm run dev
```

API modu `/api` isteklerini `localhost:5274` adresine yönlendirir. API hazır değilse anlaşılır hata gösterir; sessizce eski snapshot'a dönmez. Bağımsız HTML için `npm run build:offline` kullanılabilir. Bu komut varsayılan olarak korunmuş eski snapshot'ı kullanır; yeni veriyle HTML için yukarıdaki `run_update.py` yolunu kullan.

API .NET 10 ve PostgreSQL/PostGIS gerektirir. `/health/live` süreç sağlığını, `/health` veritabanı ve etkin yayını denetler. `ConnectionStrings__Lst` bağlantısını kendi ortamında tanımlamalısın. Şifreyi kaynak koda ekleme. `dotnet test api.Tests` veritabanı gerektirmeyen hata/sözleşme testlerini çalıştırır.

Docker için `compose.yaml` hazırdır; `LST_DB_PASSWORD` değerini kendin sağlarsın. İlk oluşturma/şema ve yayın işlemleri veri yazdığı için önce incele ve onayla. `scripts/test_compose.ps1 -Run` yalnızca yeni `lst-validation` test projesi içindir. **Docker Compose ve Airflow paneli bu ortamda uçtan uca çalıştırılamadı; başarılı oldukları iddia edilmiyor.**

## Bekleyenler

- Dynamic World + ERA5-Land gerçek aktarımı ve C/D deneyleri: **Earth Engine erişimi bekleniyor**.
- Windows 11'de kullanıcı kurulumu ve Docker/Airflow dağıtım doğrulaması.
- Yeni verinin etkin arşive alınması, veritabanı şeması/yayını ve Git push: **kullanıcı onayı bekleniyor**.
- Antalya'da doğrulanmış hata azalması ve resmi iklim sınıflarına göre değerlendirme: açık araştırma konuları. Termal kümeler resmi iklim sınıfları değildir.
