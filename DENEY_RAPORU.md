# Deney ve doğrulama raporu

24 Kasım 2026. Bu rapor gerçek çalıştırma çıktılarını ve açık sınırlamaları özetler. Önceki rapor `docs/archive/DENEY_RAPORU_Onceki.md` altında korunur.

## Kapsam ve veri

- Türkiye: 81 il için MOD11A2.061 Terra gündüz LST il ortalaması, yaklaşık 1 km kaynak pikselleri. Geometriler sadeleştirilmiş Natural Earth idari sınırlarıdır. Resmi yüksek doğruluklu il sınırı yerine kullanılmasının alan ortalamasına etkisi ayrıca incelenmelidir.
- Mekânsal ML: İstanbul, Erzurum, Antalya. 2018–2025 yaz dönemleri, 49 Landsat/Sentinel sahne çifti ve 19.600 aday 300 m hücre. A/B tam özellikli 13.370 gözlem kullanılır.
- Zaman: korunmuş arşiv 27.624 il-dönem, 27.098 geçerli LST. Ayrı 2026 aday dosyası 30.864 toplam kayıt ve 30.265 geçerli değer içerir. Yeni yıl katkısı 3.240 kayıt, 3.167 geçerli değer. Son elde edilen kompozit başlangıcı **9 Kasım 2026**. Kaynak gecikmesi nedeniyle bugünün ölçümü olarak sunulmaz.
- Aday veri mevcut `data/province-modis.csv` dosyasına uygulanmadı. Önceki yılların aday dosyadaki değerleri kaynak arşivle sayısal olarak eşit.
- LST yüzeyin uydu gözlemidir. ERA5 hava sıcaklığı başka bir değişkendir. MOD09A1 indisli zaman deneyi ile Sentinel-2 indisli mekânsal deney ayrı kaynaklardır.

## Sürüm ve veri bütünlüğü

Model yüklenmeden önce ağırlık + preprocess SHA-256, kapsam ve girdi şeması denetlenir. Eski kayıtlar doğrulanmış birleşik SHA kullanmaya devam eder. Yeni eğitimler ayrı dosya hash’lerini, pencereyi, özellik sırasını ve eğitim girdisinin hash’ini kaydeder. `joblib` güvenli bir dosya biçimi değildir; yalnızca güvenilir proje çıktıları açılmalıdır.

İl/tarih tekrarları, bozuk takvim, sonsuz değerler, piksel sayısı/oranı uyuşmazlığı, kalite maskelenmemesi reddedilir. MODIS filtresi mandatory QA ≤1, data quality=0, LST error ≤2 K ve fiziksel inceleme aralığını kullanır. İl ortalaması için bütün ilgili karolar ve ≥%50 geçerli piksel gerekir. Eksik ölçümler sıfırlanmaz.

## Mekânsal doğrulama ve Antalya

Dış test: tutulan il ve 2024–2025. Eğitim: diğer iki il, 2018–2023. İç seçim: örnekleme sahalarının tüm tekrar tarihleri aynı blokta, üç GroupKFold. Ridge alpha={1,10,100}, RF min_samples_leaf={5,15}, XGBoost max_depth={2,3}; diğer ayarlar kaynak kodda sabittir. Seed=42. Her özellik grubu aynı tam kayıtlar üzerinde çalışır.

Antalya B/XGBoost arşiv testi RMSE 8,043 °C, R² −0,0436. 2024 RMSE 7,480, 2025 RMSE 8,917 °C. 45 °C ve üzerindeki 452 gözlemde ortalama tahmin hatası −5,487 °C; diğer 519 gözlemde +5,811 °C. Bu, sıcak ve serin yüzeylerde zıt yönlü yanlılık gösterir. Nedeni yalnızca rakıma bağlanamaz; sahne, yüzey ve kaynak dağılımı da etkilidir.

Eğitim içi seçim sonrası B/XGBoost sonucu anlamlı biçimde düzelmedi. Test kümesini tekrar görmüş olduğumuz için bu analiz **keşifseldir**. Yeni doğrulama dönemi olmadan iyileşme kanıtlandığı söylenmez. Negatif R² test ortalamasına göredir; ayrıca **eğitim ortalaması** Mean modeliyle ayrı karşılaştırma yapılır. Bu iki referans aynı değildir.

Dynamic World ve ERA5-Land erişimi yoktur. C/D gerçek deneyleri çalıştırılmadı. Olasılık/birim/anahtar kontrolleri test edildi; bu kontrollerdeki sentetik test kayıtları araştırma verisi değildir. NDVI/NDBI eşikleriyle oluşturulan yüzey grupları Dynamic World sınıfları sayılmaz.

## Donmuş modellerin 2026 testi

Mevcut LSTM/XGBoost ağırlıkları yeniden eğitilmeden, yeni elde edilen 2026 hedeflerinde sınandı. Seasonal Naive ile yalnızca aynı il/başlangıç/hedef/ufuk anahtarları karşılaştırılır. Önceki yıl referansı eksik olan hedefler ortak karşılaştırma dışında kalır. Her model için 7.156 eşleşmiş test kaydı vardır; tüm olası 2026 hedeflerini temsil ettiği iddia edilmez.

16 günlük nominal ufukta pilot iller:

| city | model | n | mae | rmse |
| --- | --- | --- | --- | --- |
| Antalya | LSTM | 23 | 4.499 | 5.382 |
| Antalya | SeasonalNaive | 23 | 3.866 | 4.269 |
| Antalya | XGBoost | 23 | 2.905 | 3.771 |
| Erzurum | LSTM | 23 | 6.941 | 8.453 |
| Erzurum | SeasonalNaive | 23 | 5.148 | 5.738 |
| Erzurum | XGBoost | 23 | 4.565 | 6.637 |
| İstanbul | LSTM | 20 | 3.094 | 4.258 |
| İstanbul | SeasonalNaive | 20 | 3.826 | 5.047 |
| İstanbul | XGBoost | 20 | 3.056 | 3.803 |

81 il ve dört ufuk boyunca il/ufuk RMSE’lerinin basit ortalaması: LSTM 5,965 °C, XGBoost 5,081 °C, Seasonal Naive 5,999 °C. Bu sayı **havuzlanmış RMSE değildir**. Erzurum’da bu ufukta basit referans her iki ML modelinden iyi. Model üstünlüğü il ve döneme göre değişir; “LSTM her yerde en iyi” sonucu çıkarılamaz.

## Eğitimde görülmeyen iller

Antalya, Erzurum ve İstanbul bütün eğitim ve doğrulama kayıtlarından çıkarıldı. Diğer 78 ilde 2018–2022 eğitim, 2023 doğrulama, ayrılan illerde 2024–2025 test kullanıldı. Bu küçük bölgesel genelleme deneyi 81 ilin her birini ayrı ayrı dışarıda bırakan deney değildir. Pencere 24, en fazla 15 epoch, LSTM 16 birim, patience=3, batch=256; XGBoost 120 ağaç, depth=3, learning_rate=.06; seed=42. Modeller ayrı deney klasörüne kaydedildi.

| city | model | n | mae | rmse |
| --- | --- | --- | --- | --- |
| Antalya | LSTM | 70 | 2.353 | 2.969 |
| Antalya | SeasonalNaive | 70 | 2.978 | 3.741 |
| Antalya | XGBoost | 70 | 2.573 | 3.291 |
| Erzurum | LSTM | 68 | 3.771 | 5.012 |
| Erzurum | SeasonalNaive | 68 | 4.987 | 6.048 |
| Erzurum | XGBoost | 68 | 4.393 | 5.893 |
| İstanbul | LSTM | 65 | 2.496 | 3.298 |
| İstanbul | SeasonalNaive | 65 | 2.844 | 3.683 |
| İstanbul | XGBoost | 65 | 2.520 | 3.430 |

## Belirsizlik, veri kapsamı ve drift

81 ilde dört ufuk için MAE/RMSE/n ve kapsam CSV’leri üretildi. Yıllık beklenen 46 kompozit korunur. Eğitimdeki aylık ortalama LST ve mevsimsel genlikten dört termal grup çıkarıldı. Bu gruplar **iklim sınıfları değildir**. Ayrı bir dış kaynak değerlendirmesi de aşağıda verilmiştir.

Eşleşmiş RMSE farklarına 1.000 tekrar ve seed=42 ile %95 percentile blok bootstrap uygulanır. Zaman için 32, 96 ve 192 günlük bloklara duyarlılık raporlanır. Mekânsal hata için bütün sahne tarihi tek bloktur. Az sayıda blok aralıkları kararsızlaştırabilir. Çoklu karşılaştırma düzeltmesi uygulanmadı; sonuçlar keşifseldir. Bunlar tek bir yeni tahminin tahmin aralıkları değildir.

Drift karşılaştırması mevsimselliği azaltmak için aynı aylarda yapılır. PSI>0,25, eğitim aralığı dışında >%20 veya yeni RMSE’nin arşiv RMSE’sini %25 aşması inceleme uyarısıdır; bu eşikler operasyonel sezgiseldir. Otomatik yeniden eğitim veya model değişikliği tetiklenmez.

## Dış iklim sınıflandırmasıyla bölgesel sonuçlar

Beck vd. (2018) 1980–2016 Köppen–Geiger sınıflandırması, Figshare v2 kaynağından indirildi; boyut ve sağlayıcının MD5 değeri doğrulandı. 1 km düzeyindeki rasterdan Türkiye penceresi kırpıldı. İl sınırı içindeki hücreler küresel alan ağırlığıyla sayıldı. Dağıtılan küçük TIFF ile hesaplama tekrarlandığında bütün sınıf payları ve test skorları aynı çıktı. Kaynak, lisans ve yapılan dönüşüm `results/revision/climate/SOURCE.md` içindedir.

Baskın sınıfa göre 81 il: Csa 30, BSk 17, Dsb 17, Dfb 7, Cfb 4, Dsa 4, Cfa 2. Bu sınıflar modelin LST tahmininden türetilmedi; modellere yeni özellik olarak verilmedi. Her ilde diğer sınıfların payları da saklanır. Örneğin Erzurum’da Dsb payı yalnızca %44,24 olduğundan tek sınıflı bir il gibi yorumlanmamalıdır. Cfa/Cfb/Dsa grupları az il içerir ve ayrıca işaretlenir.

2026, 16 günlük ufukta Dfb grubunda havuzlanmış RMSE: LSTM 7,79; XGBoost 5,53; Seasonal Naive 5,68 °C. Csa grubunda sırasıyla 4,91; 4,12; 5,84 °C. Bu bulgu LSTM’nin soğuk iklimli gruplarda daha dikkatle izlenmesi gerektiğini gösterir; bir nedensellik kanıtı değildir. Tam tablo iki dönem × yedi sınıf × dört ufuk × üç model için `climate-scores.csv` dosyasındadır.

Bu değerlendirme resmi MGM il sınıflandırması değildir. İller farklı iklim alanlarını içerir; sınır geometrileri sadeleştirilmiştir. İklim sınıflarına göre zamansal test özeti, bütün bir iklim zonunu eğitim dışında bırakmakla aynı deney değildir. Ayrı üç-il-dışarıda deneyi yukarıda raporlanmıştır.

## Gerçek piksel benchmark

18 gerçek MODIS sahnesinden kalite filtresiyle **2.666.362 benzersiz piksel** çıkarıldı. Satırlar çoğaltılmadı. 266.636, 1.333.181 ve 2.666.362 satırlık alt kümeler, aynı makine ve iki Spark iş parçacığı ile karşılaştırıldı. İş yükü: CSV oku, il/tarih grubunda ortalama LST hesapla, sonucu maddileştir. Her hacimde ilk işlem ve iki sıcak tekrar var. Spark oturumu başlangıcı ayrıca kaydedilir. Motor çıktıları sayısal toleransla eşleşti.

Tam hacimde iki sıcak tekrarın medyanı:

| engine | rows | median_seconds | max_rss_mib |
| --- | --- | --- | --- |
| pandas | 2666362 | 0.876 | 298.172 |
| spark | 2666362 | 1.483 | 738.945 |

Spark oturum başlangıcı yaklaşık 4,2 saniye. Bu makine ve bu toplulaştırma işinde Pandas daha hızlı ve daha az bellek kullanıyor. Dağıtık küme, terabayt ölçeği veya başka iş yüklerine genellenemez. CPU süreleri ve Python+JVM süreç ağacı tepe RSS değerleri `measurements.csv` dosyasındadır. Ham piksel CSV’si büyük olduğu için Git/teslim paketine konmaz; kaynak sahne listesi, hash ve üretim betiği dahil edilir.

## Uygulama ve yayın doğrulaması

32 Python testi, 6 .NET testi, 5 Playwright tarayıcı testi ve 10 HTTP sözleşme kontrolü. Geçici PostgreSQL/PostGIS’te başarısız insert rollback, 81 il korunumu, veri kesintisinde 503 ve yeniden bağlantı test edildi. API/snapshot tahminleri aynı yayın kimliğinde eşleşir. API derlemesinin JS’i yaklaşık 202 KB; çevrimdışı HTML bütün veriyi taşıdığı için büyüktür. Yerel ilk yükleme/il geçişi yaklaşık yarım saniye düzeyinde gözlendi; mobil internet benchmark’ı değildir.

API için veritabanındaki etkin sürüm tek yetkili kaynaktır. Dosya ve veritabanı arasında dağıtık transaction vaat edilmez. Çevrimdışı rapor değişmez bir sürüm dosyasıdır. Yayın hazırlığı mevcut arşivi değiştirmez. Kullanıcının gerçek veritabanı, mevcut veri dosyaları ve GitHub dalı bu çalışma sırasında güncellenmedi.

## Tekrar komutları

Proje kökünde Python 3.12 sanal ortamı kullan. Spark deneyi Java gerektirir; burada Java 21 ile çalıştırıldı. Yeni çıktı adı seç; aşağıdaki deneyler eski sonuç üzerine yazmayı reddeder.

```powershell
.\.venv\Scripts\python scripts/climate_validation.py --raster results/revision/climate/koppen-1980-2016-turkiye.tif --out results/climate-repeat-01
.\.venv\Scripts\python scripts/spatial_research.py --data data/summer.csv --out results/spatial-repeat-01
.\.venv\Scripts\python scripts/forecast.py --data data/province-modis.csv --mode province --windows 24 --epochs 15 --holdout-cities Antalya Erzurum İstanbul --out results/unseen-repeat-01
.\.venv\Scripts\python scripts/evaluate_temporal.py --data results/revision/incoming/province-modis-2026.csv --out results/temporal2026-repeat-01
.\.venv\Scripts\python -m pip install -r requirements-research.txt
.\.venv\Scripts\python scripts/benchmark_pixels.py --output cache/benchmark/pixels-new.csv
.\.venv\Scripts\python scripts/benchmark_repeated.py cache/benchmark/pixels-new.csv --out results/benchmark-repeat-01 --repeats 3
```

Ortam sürümleri `results/verification/environment.json`, model/deney ayrımları ilgili `experiment.json`, kaynak ve veri kimliği `.audit.json`/`.source.json` dosyalarındadır. Yeni veri kaynağı zaman içinde güncellenebileceğinden aynı sahne kimlikleriyle karşılaştırma yapılmalıdır.

## Açık işler

Earth Engine C/D aktarımı; kullanıcının Windows 11 kurulumu; Docker Compose/Airflow scheduler/panel testi; yeni CI’ın GitHub’da çalışması; Antalya’da yeni bağımsız veriyle gösterilen iyileşme. Mevcut veriye geçiş, veritabanı uygulaması ve Git push için kullanıcı onayı gerekir.

Veri katalogları: [MOD11A2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD11A2), [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1), [ERA5-Land](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR). Veri indirme sağlayıcısı: Microsoft Planetary Computer. Bu rapordaki performans sayıları dış kaynaklardan alınmadı, teslimdeki gerçek deney dosyalarından hesaplandı.
