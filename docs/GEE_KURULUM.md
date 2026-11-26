# Earth Engine — kullanıcı tarafından yapılacak kurulum

Durum: **Erişim bekleniyor.** Bu teslimde Google hesabı/projesi, API anahtarı, hizmet hesabı veya gizli kimlik bilgisi oluşturulmadı; Dynamic World/ERA5 çıktısı üretilmiş gibi gösterilmedi.

1. Kendi Google hesabınla [resmi erişim sayfasını](https://developers.google.com/earth-engine/guides/access) aç. Buradaki kayıt bağlantısından mevcut Cloud projen için kayıt yap veya kendi projenı oluştur. Kurumsal hesapta proje oluşturma yetkisini yöneticin vermelidir.
2. Bitirme araştırman için uygun ticari olmayan kullanım kaydını gerçek bilgilerle tamamla; ekranda istenen doğrulamaları kendin yap.
3. Cloud Console'da doğru projeyi seç, **Earth Engine API** etkin mi kontrol et. Hesabının projeye erişim yetkisi olmalı.
4. Console'daki **Project ID** değerini kopyala. Proje adı ve sayısal proje numarası farklı alanlardır. Bu belgede gerçek veya uydurulmuş bir Project ID yoktur.
5. Python ortamı kurulduktan sonra kendi bilgisayarında çalıştır:

```powershell
.\.venv\Scripts\python -c "import ee; ee.Authenticate()"
```

6. Tarayıcıda hesabını seçip yetki ver. Kimlik bilgileri kendi bilgisayarında kalsın; token/anahtar/parola dosyalarını sohbete veya GitHub'a gönderme.
7. PowerShell'de `$GEE_PROJECT` değişkenine Console'dan aldığın gerçek kimliği kendin atadıktan sonra doğrula:

```powershell
.\.venv\Scripts\python -c "import ee,sys; ee.Initialize(project=sys.argv[1]); print(ee.Number(1).getInfo())" $GEE_PROJECT
```

Beklenen çıktı `1`. Erişim başarısızsa sonraki aktarıma geçme.

8. Önce yalnızca **bir Antalya sahnesini** yeni bir dosyaya aktar:

```powershell
.\.venv\Scripts\python scripts/enrich_summer.py --project $GEE_PROJECT --city Antalya --limit-scenes 1 --output candidates/gee-smoke.csv
```

9. CSV yanında üretilen `.audit.json` dosyasında tam kayıt sayısını ve eksik oranlarını incele. Dokuz Dynamic World olasılığı 0–1 aralığında olmalı ve tam kayıtta toplamları yaklaşık 1 olmalı. ERA5 hava/çiy noktası Kelvin'den Celsius'a çevrilir. ERA5 doğal ölçeği yaklaşık 11 km'dir; 300 m hücrede bağımsız meteoroloji ölçümü değildir.
10. Küçük aktarımı doğruladıktan sonra bütün veri ve A/B/C/D karşılaştırması:

```powershell
.\.venv\Scripts\python scripts/enrich_summer.py --project $GEE_PROJECT --output candidates/summer-gee.csv
.\.venv\Scripts\python scripts/spatial_research.py --data candidates/summer-gee.csv --out results/gee-comparison-01 --require-all
```

Karşılaştırma dört grubun **aynı tam gözlemlerinde**, aynı dış il/yıl ayrımı ve yalnızca eğitim içi bloklarla yapılır. Yetersiz veya boş gerçek veri varsa deney durur; eksikler uydurma veriyle doldurulmaz.

Resmi kaynaklar: [kimlik doğrulama](https://developers.google.com/earth-engine/guides/auth), [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1), [ERA5-Land](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR). Kontrol tarihi: 23 Kasım 2026.
