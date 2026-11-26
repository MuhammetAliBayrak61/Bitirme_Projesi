# Geliştirme ve doğrulama durumu

Bu güncelleme GitHub'daki `fcab532` sürümünden başladı. Kaynak dosyalar scripts, api, web, data, models, results ve tests dizinlerine taşındı. Eski deney tabloları tarihsel karşılaştırma için korunur. Yeni mekânsal deneylerin yetkili sonuç dosyası `results/summer-trial/scores.csv` dosyasıdır.

## Doğrulanan işler

- Python 3.12 ve requirements.txt ile temiz ortam kuruldu. Orijinal dört test geçti. LSTM yükleme `compile=False` ile çıkarım amacıyla yapılır. Girişte Python/paket sürümleri kontrol edilir. Uyuşmazlıkta kurulum komutunu gösteren açıklayıcı hata verilir.
- Üç pilot il için 2018–2025 yıllarının Haziran ve Ağustos aylarından 49 Landsat–Sentinel sahne çifti alındı. Dokuz örnekleme alanı yıllara dönüşümlü dağıtıldı. İstanbul 2021 için kalite nedeniyle üçüncü bir aday tarih eklendi; her il-yılda en az iki geçerli tarih sağlandı. 19.600 aday 300 m hücreden 13.370'ünde tüm A/B özellikleri ve LST var. Kalite eşikleri geçmeyen hücrelerin boş değerleri CSV'de korunur.
- Eğitim 2018–2023, bağımsız test 2024–2025. Her denemede test ili tüm yıllarda eğitim dışında tutuldu. A/B grupları aynı gözlemleri kullanır. Linear Regression, Random Forest ve XGBoost'a ortalama tahmin ve Ridge eklendi.
- Erzurum B grubunda yeni test 1.308 gözlem içerir. XGBoost RMSE 4,36 °C, Random Forest 4,67 °C, Linear Regression 8,73 °C, ortalama referansı 7,50 °C çıktı. Eğitimde diğer illerden 1.500 m üzeri 636 örnek var. Tüm model tahminleri -50 / +85 °C inceleme aralığına göre işaretlenir. Bu aralık evrensel fiziksel sınır veya doğruluk garantisi olarak kullanılmaz.
- Tek değişkenli `common` ve çok değişkenli `multi` deneyleri aynı 2018–2025 verisinde, aynı eğitim/doğrulama/test yıllarında karşılaştırıldı. Dört ufuk, bölge ve mevsim tabloları `results/paired-seasons.csv` içindedir. Test anahtarlarının ve hedeflerin eşitliği otomatik kontrol edilir.
- Model ağırlıkları ve ölçekleyici SHA-256 sürümüyle, eğitim tarihiyle kaydedilir. Batch tahmin, veri yeterliliği kontrolü, snapshot ve tek işlemde PostGIS yayını `scripts/run_update.py --publish` ile çalışır.
- React/TypeScript ve ASP.NET derlemesi geçti. PostgreSQL/PostGIS ile API sorguları ve arayüz seçimleri hem çevrimdışı hem API modunda test edildi.

## Veri ve erişim gerektiren işler

Dynamic World ve ERA5-Land GEE aktarımı için bu çalışma ortamında yetkilendirilmiş Google Cloud projesi bulunmuyor. Bu nedenle C/D modelleri eğitilmiş olarak sunulmuyor. Dokuz Dynamic World olasılık bandını ve ERA5 özelliklerini mevcut hücre/tarih anahtarlarına ekleyen `scripts/enrich_summer.py` hazırdır. Gerçek görev sonucu doğrulanmalıdır.

```powershell
.\.venv\Scripts\earthengine authenticate
.\.venv\Scripts\python scripts/enrich_summer.py --project PROJE_KIMLIGI
.\.venv\Scripts\python scripts/spatial_research.py --data data/summer-gee.csv --out results/gee-trial --require-all
```

Bu komutlar tamamlandığında 3 il × 4 grup × 3 ana algoritma için 36 karşılaştırma ve ayrıca Mean/Ridge sonuçları oluşur. Tüm gruplar aynı eksiksiz D gözlemleriyle karşılaştırılır.

İl ortalaması MODIS arşivi `scripts/province_archive.py` ile NASA MOD11A2.061 Terra ürününün Planetary Computer kopyasından indirilir. Kaynakta olmayan veya eksik karolu dönemler boş kalır. `valid_fraction`, `valid_pixels`, `total_pixels` ve `complete_tiles` kaydedilir. GEE üzerinden aynı ürün için aktarım kodu da vardır. Natural Earth il sınırları görselleştirme amacıyla sadeleştirilmiştir. İdari sınır hassasiyeti gerektiren nihai araştırmada onaylı sınır verisi kullanılmalıdır.

Docker daemon bu ortamda bulunmadığından Docker Compose ve Airflow zamanlayıcısı uçtan uca çalıştırılmış değildir. API/veritabanı aynı sürümlerle yerel süreçlerde test edildi. Airflow DAG sonuna tahmin ve veritabanı yayını bağlandı; dağıtım ortamında scheduler testi gereklidir.

GitHub yazma kimliği bu oturumda bulunmuyor. Güncelleme yerel Git dalı ve uygulanabilir bundle olarak hazırlanır.


## Spark ölçümleri

Gerçek hücre tablosunun 4.800, 9.600 ve 19.200 satırlık alt kümelerinde pandas/Spark üçer kez çalıştırıldı. Her tekrarın il-yıl ortalamaları karşılaştırıldı. Tam alt kümede medyan süre pandas için 0,13 s, Spark için 13,86 s oldu. Ölçülen en yüksek süreç ağacı RSS değeri sırasıyla 94,71 MiB ve 633,50 MiB oldu. Sonradan eklenen Temmuz sahnesi bu benchmark koşusuna dahil edilmedi. Bunlar tek makinede küçük tablolara ait ölçümlerdir. Spark sonuçları büyük veri ölçeklenebilirliği kanıtı olarak yorumlanmamalıdır. Dosya sonuçları results/benchmark/measurements.csv içindedir.

## 81 il için tamamlanan deney

MOD11A2.061 Terra arşivindeki 2.048 kaynak karo işlendi. 2018–2025 aralığında 81 il için 27.624 il-dönem kaydı üretildi. 27.098 kayıtta bütün il karoları mevcut ve geçerli piksel oranı en az %50. Kaynakta bulunmayan dönemler üretilmedi. Beklenen her tam yılda 46 dönem vardır; 2022, 2023 ve 2025 kaynak kapsamı eksiktir. İl bazındaki kapsam results/province-coverage.csv içindedir.

Eğitim 2018–2022, doğrulama 2023, bağımsız test 2024–2025 olarak yapıldı. Modeller 81 ilin geçmişini birlikte öğrenir. Bu deney, bilinen illerin gelecek dönemlerine genellemeyi ölçer. Ayrı bir görülmemiş-il testi mekânsal bölümde uygulanır.

Hem XGBoost hem LSTM doğrulamada 24 gözlemlik pencereyi seçti. LSTM 16 birimlidir, batch büyüklüğü 256, en çok 15 epoch ve üç epoch sabırlı erken durdurma kullanılmıştır. Gerçek eğitim/veri hazırlama kodu ve modeller pakettedir.

İl ortalamalarının 16 günlük nominal ufukta bağımsız test RMSE değerleri aşağıdadır.

| İl | Model | Test n | RMSE °C |
|---|---|---:|---:|
| Antalya | LSTM | 70 | 2.982 |
| Antalya | SeasonalNaive | 70 | 3.741 |
| Antalya | XGBoost | 70 | 3.265 |
| Erzurum | LSTM | 68 | 5.150 |
| Erzurum | SeasonalNaive | 68 | 6.048 |
| Erzurum | XGBoost | 68 | 5.728 |
| İstanbul | LSTM | 65 | 3.310 |
| İstanbul | SeasonalNaive | 65 | 3.683 |
| İstanbul | XGBoost | 65 | 3.435 |

Son arşiv başlangıcı 27 Aralık 2025 olan girdilerden Ocak 2026 kompozitlerine 648 model tahmini üretildi (81 il × 4 ufuk × 2 model). Bu çıktılar arşiv çıkarımıdır. Güncel takvim tarihine ait hava tahmini olarak kullanılmamalıdır. 648 çıktı tanımlı yayımlama koşullarını geçti. Bu koşullar son sekiz dönemde en az dört gözlem, aynı il/ufukta en az 12 bağımsız test örneği ve inceleme sıcaklık aralığıdır. Model hataları ayrıca gösterilir; koşullar yüksek doğruluk garantisi vermez.

Kayıtlı il modellerinin yeniden yüklenmesi ve aynı tahminleri üretmesi dahil 11 test geçti. Kalite maskelemesi, il-dönem benzersizliği ve piksel oranları test edildi. Model/ölçekleyici dosyalarının SHA-256 sürümü çıkarımdan önce doğrulanır. İşlem sırasında model dosyaları karışırsa açıklayıcı hata verilir.

C/D için gerçek GEE aktarımı ve Docker/Airflow zamanlayıcısının hedef ortamda uçtan uca testi hâlâ beklemektedir. GitHub'a doğrudan gönderim yapılamadı; Git bundle hazırlanmıştır.

Son entegrasyon kontrolünde batch çıkarım → snapshot → PostgreSQL/PostGIS yayını zinciri çalıştırıldı. API 81 ilin listesini, Ankara il serisini, Antalya mekânsal sonuçlarını ve 648 il tahminini döndürdü. Çevrimdışı Atlas ve API modundaki il/yıl/model/ufuk seçimleri DOM testinden geçti. Bu kontrol Airflow scheduler veya Docker Compose çalıştırmasının yerine geçmez.
