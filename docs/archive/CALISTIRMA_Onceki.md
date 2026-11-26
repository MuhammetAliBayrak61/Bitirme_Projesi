# Kurulum ve güncelleme

ZIP içindeki bütün klasörleri birlikte çıkarın. `Atlas.html` dosyası çevrimdışı açılır. Windows PowerShell'de proje klasörünü açıp `./setup.ps1` çalıştırın. Python 3.12 kurulu olmalıdır. Kurulum sabitlenmiş bağımlılıkları kurar ve testleri çalıştırır.

## GitHub deposuna uygulama

Git bundle, eski kök dizin yerleşimini düzelten commit ile araştırma güncellemesini içerir. Kullanıcı değişikliklerini kaybetmemek için temiz çalışma dizininde yeni dal açılır. PowerShell'de kendi depo klasörünüzde şu komutları çalıştırın. Bundle yolunu indirdiğiniz gerçek dosya yoluyla değiştirin.

```powershell
git status
git fetch "C:/indirme/Bitirme_Guncelleme.bundle" lst-pilot-dogrulama
git switch -c lst-guncelleme FETCH_HEAD
git push -u origin lst-guncelleme
```

Ardından GitHub'da bu daldan main'e Pull Request açın. Main dalında yeni değişiklikler varsa PR üzerinden karşılaştırın. Bundle, temel commit fcab532 ve sonraki güncelleme commitlerini içerir.

## Araştırmayı tekrar çalıştırma

```powershell
.\.venv\Scripts\python scripts/check_environment.py
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python scripts/spatial_research.py --data data/summer.csv --out results/summer-trial
.\.venv\Scripts\python scripts/forecast.py --data data/modis-multi.csv --mode common
.\.venv\Scripts\python scripts/score_temporal.py
.\.venv\Scripts\python scripts/run_update.py
```

## Altı kaynaklı C/D deneyi

Google Cloud projesi için Earth Engine erişimini etkinleştirin ve `.venv/Scripts/earthengine authenticate` ile kendi hesabınızda oturum açın.

```powershell
.\.venv\Scripts\python scripts/enrich_summer.py --project PROJE_KIMLIGI
.\.venv\Scripts\python scripts/spatial_research.py --data data/summer-gee.csv --out results/gee-trial --require-all
```

GEE işlemleri dış serviste gerçek veriyle çalıştırılana kadar bu deneylerin sonucu hazır kabul edilmemelidir. Mekânsal pilot verisi Sentinel-2, eski çok değişkenli nokta serisi MOD09A1 kullanır. Bu kaynaklar veri dosyaları ve raporlarda ayrı belirtilir.

## İl serisi ve yeni tahmin yayını

```powershell
.\.venv\Scripts\python scripts/province_archive.py --workers 4
.\.venv\Scripts\python scripts/forecast.py --data data/province-modis.csv --mode province
.\.venv\Scripts\python scripts/update_forecasts.py --mode province --data data/province-modis.csv
.\.venv\Scripts\python scripts/run_update.py --publish
```

Veritabanı yayını için DATABASE_URL tanımlanmalıdır. Docker Compose kurulumunu README açıklar. Tahmin güncellemesi model ağırlıklarını yeniden eğitmeden çıkarım yapar. Yeniden eğitim için forecast.py kullanılır. API'nin `/api/tahmin-katmani` adresi yalnızca yayımlanabilir il tahminlerini döndürür.

## Tekrarlı Spark deneyi

Java 17+ ile `pip install pyspark==4.0.1 psutil` kurulumundan sonra Linux/WSL'de `python scripts/benchmark_repeated.py data/summer.csv` çalıştırın. Gerçek verinin %25, %50 ve %100 alt kümelerinde üçer tekrar yapılır. Süre ve Python/JVM süreç ağacının örneklenmiş tepe RSS değeri kaydedilir. Deney dosyası `results/benchmark/measurements.csv` olur. Bu ölçüm küçük veri için geçerlidir; ülke ölçeğindeki raster işlem maliyetini temsil etmez.

Yerel Airflow zincirini Docker Desktop ile açmak için aynı veritabanı parolasını kullanarak aşağıdaki komutu çalıştırın. Airflow 2.10.5 ve ayrı Python 3.12 araştırma ortamı kurulur. Bu Compose profili bu çalışma ortamında yürütülememiştir.

```powershell
docker compose -f compose.yaml -f compose.research.yaml up --build -d
```

Airflow arayüzü http://localhost:8081 üzerindedir. `turkiye_lst_pilot` DAG'ını tetikleyin. Son görev tahminleri üreterek veritabanını günceller. GEE/81 il genişletme deneyi ayrı araştırma komutlarıyla yürütülür.
