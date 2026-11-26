# 30 maddelik düzeltme takibi

Tarih: 24 Kasım 2026. Durumlar kod hazırlığını, gerçek testleri ve erişim/onay bekleyen uygulamaları ayrı gösterir. “Tamamlandı” bütün araştırma hedeflerinin başarıya ulaştığı anlamına gelmez; örneğin Antalya hata analizi olumsuz bir sonuç vermiştir.

## 15 işlik takvimde durum

| İş | Durum |
|---|---|
| 1. Güvenli yedek ve dal | Tamamlandı |
| 2. Windows Python 3.12 | Linux doğrulandı; Windows testi bekliyor |
| 3. Model sürümü | Tamamlandı |
| 4. Veri kalitesi ve 2026 | Aday veri doğrulandı; mevcut veriye geçiş onay bekliyor |
| 5. Tahmin/snapshot/yayın | Kod ve izole testler tamamlandı |
| 6. Antalya analizi | Tamamlandı; doğrulanmış hata azalması henüz yok |
| 7. Mekânsal/zamansal doğrulama | Tamamlandı; deney sınırları raporda |
| 8. A/B/C/D ve GEE | A/B tamamlandı; C/D erişim bekliyor |
| 9. 81 il, belirsizlik, drift | Tamamlandı; iklim grupları ve kapsam sınırları raporda |
| 10. Web haritası | Tamamlandı |
| 11. API/PostgreSQL/Docker | API/DB testleri tamamlandı; Docker ortamı bekleniyor |
| 12. CI ve yeni testler | Yerel testler geçti; GitHub çalışması bekliyor |
| 13. Spark | Gerçek piksel benchmark tamamlandı |
| 14. Airflow/izlenebilirlik | Kod ve kayıtlar hazır; scheduler doğrulaması bekliyor |
| 15. Belgeler/rapor/sunum | Rapor ve sunum metni tamamlandı; PPTX hazırlanmadı |

## 1. Git yedeği, geliştirme dalı — Tamamlandı

**Dosyalar:** `.gitignore`, yerel `gelistirme-testleri` dalı

Değişiklik öncesi tam Git bundle ve SHA-256 alındı, bundle doğrulandı. `main` değişmedi; uzak depo ile başlangıç dosyalarının aynı olduğu karşılaştırıldı.

**Doğrulama:** `results/verification/baseline-commit.txt`; teslim değişiklik yaması

## 2. Python/Windows/LSTM — Kullanıcı ortamı bekleniyor

**Dosyalar:** `setup.ps1`, `scripts/check_environment.py`, CI

Python 3.12/pinli ortam kontrolü ve Windows test kayıtları eklendi. Linux’ta eski 11 test dahil 32 test geçti; Windows çalıştırması henüz yok.

**Doğrulama:** `results/verification/python-tests.txt`, `environment.json`

## 3. Model bütünlüğü — Tamamlandı

**Dosyalar:** `scripts/registry.py`, `scripts/predict.py`

Eksik/bozuk manifest, ağırlık ve ön işleme uyuşmazlığı çıkarımı durdurur. Kapsam, özellik sırası, pencere, ölçekleyici ve model şekli denetlenir. Eski doğrulanmış iki-dosya birleşik SHA korunur; yeni eğitimlerde ayrı SHA ve veri sürümü de yazılır. Hash bir yayıncı imzası değildir; güvenilmeyen joblib açılmaz.

**Doğrulama:** `tests/test_integrity.py`; yeniden yükleme testleri

## 4. 2026 verisi ve tarihler — Hazır; etkinleştirme onayı bekliyor

**Dosyalar:** `scripts/province_archive.py`, `forecast.py`, `evaluate_temporal.py`

3.240 yeni il-dönem kaydı ayrı aday dosyada; 3.167’si geçerli. Eğitim/doğrulama/test yılları yapılandırılabilir. Eski modeller 2026 gerçek gözlemlerinde sınandı. Mevcut veri dosyası değiştirilmedi.

**Doğrulama:** `results/revision/incoming/*.audit.json`; `temporal-2026/`

## 5. CSV/snapshot/web tutarlılığı — Tamamlandı

**Dosyalar:** `run_update.py`, `snapshot.py`, `dashboard_data.py`, web

Güncel aday tahmin latest dosyalarından alınır; ilk eğitim çıktıları archiveFuture altında tutulur ve arayüzde ayrı seçimdir. Model/veri kimliği ve tarihler taşınır. HTML aday snapshot ile yeniden derlenir.

**Doğrulama:** API/snapshot değer eşleşmesi; tarayıcı arşiv seçimi

## 6. Veri kalitesi — Tamamlandı

**Dosyalar:** `data_quality.py`, `province_archive.py`

Tekil il/tarih, kronoloji, gerçek MODIS başlangıçları, kaynak, sayılar/oranlar, kalite maskesi, uç değerler ve QC bitleri kontrol edilir. İndirme hatasında mevcut veri korunur.

**Doğrulama:** `test_integrity.py`, `test_validation.py`; eski aday satırları eşitlik testi

## 7. Yayın bütünlüğü — Tamamlandı

**Dosyalar:** `release.py`, `run_update.py`, `publish.py`

Değişmez aday klasör ve ayrı etkinleştirme eklendi. Snapshot ve çevrimdışı HTML hash’leri etkinleştirmeden önce kontrol edilir. API tek transactional DB yayın kimliğini okur; HTML sürümlü bağımsız rapordur. Dosya ile DB arasında dağıtık atomiklik varmış gibi davranılmaz.

**Doğrulama:** İzole PostGIS’te rollback, kesinti/503, yeniden bağlanma ve kayıt korunumu

## 8. Antalya hatası — Analiz tamamlandı; iyileşme açık

**Dosyalar:** `research_diagnostics.py`, `spatial_validation.py`

Hata yıl/rakım/indis/sıcak dönem kırılımlarında raporlandı. >=45°C gözlemlerde −5,49°C, diğerlerinde +5,81°C yanlılık var. Eğitim içi blok seçiminden sonra B/XGBoost RMSE yine ~8,04°C; kanıtlanmış iyileşme iddiası yok.

**Doğrulama:** `diagnostics/spatial-error-slices.csv`; `spatial-blocked/scores.csv`

## 9. Mekânsal ayrımlar — Tamamlandı

**Dosyalar:** `spatial_validation.py`, `spatial_research.py`

Dış test ili ve 2024–2025 ayrımı korunur. Aynı sahanın bütün tarihleri tek iç blokta tutulur; aday hiperparametreler sadece eğitim içinde seçilir. Ayrım ve örnek sayıları kaydedilir.

**Doğrulama:** `spatial-blocked/split-manifest.csv.gz`, `validation.csv`, `coverage.csv`

## 10. Zamansal karşılaştırma — Tamamlandı

**Dosyalar:** `research_diagnostics.py`, `evaluate_temporal.py`, `benchmark_inference.py`

Ufuk, mevsim, sıcak dönem, LSTM/XGBoost/Naive farkları, süre, CPU ve RSS raporu üretildi. Common/multi eşleşmiş gözlemleri korunur.

**Doğrulama:** `diagnostics/*scores.csv`; `temporal-2026/timings.csv`; şekiller

## 11. A/B/C/D katkısı — Earth Engine erişimi bekleniyor

**Dosyalar:** `spatial_research.py`

A/B karşılaştırması aynı satırlar ve bloklar üzerinde var. C/D girdi şeması ve tam gözlem ortaklaştırması hazır. Gerçek C/D verisi olmadan sonuç üretilmedi.

**Doğrulama:** A/B sonuçları var; dört grup için gerçek kabul testi bekliyor

## 12. DW/ERA5 aktarımı — Earth Engine erişimi bekleniyor

**Dosyalar:** `enrich_summer.py`, `docs/GEE_KURULUM.md`

Tek sahne denemesi, hücre kimliği ve önbellek kimliği kontrolü, olasılık toplamı ve sıcaklık birimi kontrolü, kaynak/tarih denetimi hazır. Google hesabına giriş yapılmadı.

**Doğrulama:** Sentetik girdiler yalnızca birim testlerinde; gerçek aktarım çalıştırılmadı

## 13. 81 il ve bölgesel doğrulama — Tamamlandı; deney sınırları raporlandı

**Dosyalar:** `research_diagnostics.py`, `research_figures.py`, `climate_validation.py`, `forecast.py`

81 il için hata/kapsam tablosu ve arayüz puanları var. Üç il eğitim/doğrulamadan çıkarılarak ayrı deney koşuldu. Eğitim LST’sinden termal gruplar ayrıca tutuldu. Dış kaynak Beck vd. (2018) Köppen–Geiger rasterından 81 ilin sınıf payları ve baskın sınıfı çıkarıldı; 2024–2025 ile 2026 için yedi baskın sınıfta eşleşmiş test skorları hesaplandı. Az il içeren sınıflar ve karışık iklimli iller işaretli. Bu çalışma resmi MGM ataması veya leave-climate-zone-out deneyi değildir.

**Doğrulama:** `province-coverage-performance.csv`; `unseen-provinces/`; `figures/thermal-group-scores.csv`; `climate/`; `verification/climate-validation.json`

## 14. Belirsizlik — Tamamlandı

**Dosyalar:** `research_diagnostics.py`, `confidence.py`

Eşleşmiş RMSE farklarına %95 blok bootstrap: zaman için 32/96/192 gün duyarlılığı; mekânsal için tam sahne tarihi blokları. Az blok ve çoklu karşılaştırma sınırları belirtilir.

**Doğrulama:** `diagnostics/*confidence.csv`; bu aralıklar bireysel tahmin aralığı değildir

## 15. Drift izlemesi — Tamamlandı

**Dosyalar:** `research_diagnostics.py`, `evaluate_temporal.py`

Ay eşleştirmesiyle dağılım ve aralık dışı oran, geçerli piksel oranı, yeni dönem hatasının eskiye oranı kaydedilir. Eşikler inceleme uyarısıdır; otomatik yeniden eğitim yok.

**Doğrulama:** `diagnostics/drift.csv`; `temporal-2026/performance-monitor.csv`

## 16. Dinamik yıl — Tamamlandı

**Dosyalar:** `web/src/main.tsx`, `Province.tsx`

Her serinin kendi son yılı seçilir; il serisi ile tek piksel yıl seçimi ayrı etiketlidir. İl değişince geçersiz seçim kullanılmaz.

**Doğrulama:** Tarayıcı testi 2027 test verisini otomatik seçti

## 17. Harita lejantı/erişilebilirlik — Tamamlandı

**Dosyalar:** `main.tsx`, `style.css`

Sayısal °C aralıkları, model/hedef, min/max, verisiz il, klavye Enter/Space ve görünür odak eklendi.

**Doğrulama:** Tarayıcı klavye ve mobil testleri; görsel inceleme

## 18. Ölçeklerin ayrılması — Tamamlandı

**Dosyalar:** `main.tsx`, `Province.tsx`

81 il MODIS ortalaması, yaklaşık 1km tek piksel ve 300m Landsat hücresi ayrı kapsam/metinlerle sunulur. MOD09A1 ile Sentinel kaynak farkı açık.

**Doğrulama:** Arayüz kapsam testi ve görsel kontrol

## 19. API hata/sağlık — Tamamlandı

**Dosyalar:** `api/Program.cs`, `api.Tests/`

Liveness/readiness, standart 400/404/409/503 yanıtları, istek süresi, salt-okunur API hız sınırı ve sıkıştırma eklendi.

**Doğrulama:** 6 .NET testi; 10 HTTP sözleşme kontrolü; geçici DB kesinti testi

## 20. Yayın arşivi — Tamamlandı; gerçek DB uygulaması onay bekliyor

**Dosyalar:** `sql/init.sql`, `publish.py`

Ek tablolarla sürümlü kayıt ve etkin işaretçi. Eski province tablosu silinmez. Beklenmeyen kapsam azalması reddedilir; ilk seed etkin yayın varsa dokunmaz.

**Doğrulama:** Geçici DB transaction/kapsam/yeniden başlatma kontrolleri

## 21. Web yükleme — Tamamlandı

**Dosyalar:** `web/vite.config.ts`, `main.tsx`

API derlemesi büyük snapshot’ı içermez; il ayrıntıları seçilince gelir. Çevrimdışı derleme tam veriyi taşır. Hata/yükleniyor durumları ayrı.

**Doğrulama:** JS yaklaşık 202KB; yerel tarayıcı ilk açılış+il geçişi <1sn; gerçek internet ölçümü değil

## 22. Docker Compose — Dağıtım ortamı bekleniyor

**Dosyalar:** `compose.yaml`, `Dockerfile`, `scripts/test_compose.ps1`

Yeni şemaya uygun, tekrar çalıştırmada aktif yayını koruyan seed ve Windows ilk açılış/yeniden başlatma denetimi hazır.

**Doğrulama:** PostGIS/API ayrı testte geçti; Docker daemon/Windows Compose testi yapılmadı

## 23. GitHub Actions — CI tanımı hazır; uzak çalıştırma bekliyor

**Dosyalar:** `.github/workflows/test.yml`, `requirements-dev.txt`

Windows/Linux Python, .NET, PostGIS, tarayıcı, kod kontrolü, bağımlılık taraması ve Docker build işleri eklendi.

**Doğrulama:** Yerel karşılıkları geçti; push yapılmadı, yeni GitHub işlerinin yeşil olduğu söylenmiyor

## 24. Regresyon testleri — Tamamlandı

**Dosyalar:** `tests/test_integrity.py`, `test_validation.py`, `api.Tests/`, `web/tests/`

Eksik/bozuk model, yinelenen tarih, eksik dönem, 2026 hedefi, QC, GEE özellik kontratı, blok ayrımı, API kesintisi ve yayın rollback testleri eklendi.

**Doğrulama:** 32 Python + 6 .NET + 5 tarayıcı + 10 HTTP kontrolü

## 25. Spark ölçeği — Tamamlandı

**Dosyalar:** `benchmark_pixels.py`, `benchmark_repeated.py`

18 gerçek MODIS sahnesinden 2.666.362 benzersiz piksel. Üç hacim, ilk işlem + iki sıcak tekrar, başlangıç/CPU/RSS ayrı. Pandas/Spark sayısal eşitliği doğrulandı.

**Doğrulama:** `benchmark-real/measurements.csv`; bu makinede Spark daha yavaş

## 26. Airflow — Kod hazır; Airflow ortamı bekleniyor

**Dosyalar:** `airflow/lst_pipeline.py`, `airflow/Dockerfile`, `pipeline.py`

Eski pilot görevleri yerine değişim tespiti → aday veri → kalite → sabit model değerlendirmesi → aday yayın. İndirmeyle aynı kaynak envanteri kontrol edilir; yeni tarih yoksa kısa devre. Eğitim/yayın kullanıcı kararıdır.

**Doğrulama:** Yeni veri yok testi geçti; scheduler/panel ve Docker DAG uçtan uca çalıştırılmadı

## 27. İzlenebilirlik — Tamamlandı

**Dosyalar:** `provenance.py`, `registry.py`, `province_archive.py`, `run_update.py`

Kaynak/ürün, indirme zamanı, geçerli/eksik sayılar, veri/model/kod hash’leri, süre, başarısızlık türü ve yayın kimliği tutulur; gizli URL/kimlik kaydedilmez.

**Doğrulama:** Aday .audit.json, model sürümleri, yayın manifesti

## 28. Kurulum belgeleri — Tamamlandı

**Dosyalar:** `README.md`, `CALISTIRMA.md`

ZIP ile tek başlangıç yolu, Python ve API/Docker ayrımı, hata çözümleri ve test kanıtları. Eski bundle yönergesi arşive taşındı.

**Doğrulama:** Komut ve dosya yolları teslimde kontrol edildi; Windows için doğrulama sınırı açık

## 29. Akademik kapsam — Tamamlandı

**Dosyalar:** `DENEY_RAPORU.md`, `docs/SUNUM.md`

Yüzey/hava sıcaklığı, il/hücre ayrımı, C/D eksikliği, gerçek ölçek deneyleri ve bekleyen dağıtım açık yazıldı.

**Doğrulama:** Sayısal bulgular CSV’lerden tekrar hesaplandı

## 30. Tekrarlanabilirlik — Tamamlandı

**Dosyalar:** `DENEY_RAPORU.md`, `results/revision/`, `results/verification/`

Tohum, ayrımlar, özellikler, aday parametreler, sürümler, komutlar, veri hash’leri ve başarısızlık analizleri. Eski sonuçlar korundu.

**Doğrulama:** Kaynak/model/eski sonuç dosyalarının başlangıca göre değişmediği denetlendi
