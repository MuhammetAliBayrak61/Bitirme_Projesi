# Sunum metni ve konuşmacı notları

Bu dosya 10 slaytın içerik metnidir. Düzenlenebilir PowerPoint dosyası değildir. Sayısal kaynaklar `DENEY_RAPORU.md` ve `results/revision/` altındadır.

## Slayt 1 · Türkiye Yüzey Sıcaklığı Atlası

- 81 ilde MODIS il ortalaması ve üç pilot ilde mekânsal makine öğrenmesi
- 24 Kasım 2026 inceleme sürümü

Konuşmacı notu: LST ve hava sıcaklığı ayrımını ilk slaytta açıkla.

## Slayt 2 · Veri kapsamı

- Korunmuş arşiv: 27.624 il-dönem
- 2026 aday veri: 3.240 yeni kayıt, 3.167 geçerli gözlem
- Son kompozit başlangıcı: 9 Kasım 2026

Konuşmacı notu: 2026 dosyası mevcut veri tabanına uygulanmadı. Geometriler sadeleştirilmiş Natural Earth sınırları.

## Slayt 3 · Model ve veri bütünlüğü

- Ağırlık ve ön işleme dosyaları birlikte doğrulanır
- Eksik model kimliği ve yanlış özellik sırası yüklemeyi durdurur
- 32 Python testi eski modellerin tekrar üretilebilirliğini de kapsar

Konuşmacı notu: Hash kontrolünün güvenilmeyen pickle dosyasını güvenli yapmadığını belirt.

## Slayt 4 · Mekânsal değerlendirme

- Dışarıda tutulan il ve 2024–2025 yılı bağımsız testtir
- Aynı sahanın bütün tarihleri aynı iç doğrulama bloğunda kalır
- A/B gerçek sonuçları var. C/D Earth Engine erişimi bekliyor

Konuşmacı notu: Test iline bakarak hiperparametre seçilmedi. Test dönemi daha önce incelendiği için yeni analiz keşifseldir.

## Slayt 5 · Antalya’da hata yönü değişiyor

- 45°C ve üzeri gözlemler: ortalama −5,49°C hata
- Daha serin gözlemler: +5,81°C hata
- B/XGBoost RMSE yaklaşık 8,04°C. İyileşme kanıtlanmadı

Konuşmacı notu: Görsel: results/revision/figures/antalya-bias.png

## Slayt 6 · Yeni 2026 verisiyle zamansal test

- Dondurulmuş LSTM, XGBoost ve Seasonal Naive
- Aynı hedeflerde 7.156 test kaydı / model
- İl ve ufuk ortalama RMSE: LSTM 5,965; XGBoost 5,081; Naive 5,999°C

Konuşmacı notu: Bu değerler havuzlanmış RMSE değildir. Görsel: results/revision/figures/temporal-horizons.png

## Slayt 7 · Belirsizlik ve bölgesel genelleme

- 32/96/192 günlük bloklarla fark güven aralıkları
- 81 il için kapsama oranı ve hata tabloları
- Dış Köppen–Geiger verisine göre yedi iklim grubunda karşılaştırma
- Üç pilot il eğitim ve doğrulamadan çıkarılarak ayrıca sınandı

Konuşmacı notu: Köppen–Geiger haritası ile kendi termal kümelerimizi ayır. İklim grubu test özeti, bir iklim zonunun tamamen eğitim dışında bırakılması değildir. Çoklu karşılaştırma düzeltmesi yok.

## Slayt 8 · Gerçek piksel ölçeğinde Spark

- 2.666.362 benzersiz gerçek MODIS pikseli
- Tam hacimde sıcak tekrar medyanı: Pandas yaklaşık 0,88sn, Spark 1,48sn
- Spark başlangıcı ayrıca yaklaşık 4,2sn

Konuşmacı notu: Görsel: results/revision/figures/benchmark-real-pixels.png. Sonucu yalnızca bu makine ve iş yükü için yorumla.

## Slayt 9 · Uygulama doğrulaması

- 6 .NET ve 5 tarayıcı testi
- 10 API sözleşme kontrolü, geçici DB’de rollback ve kesinti testi
- API ilk JS paketi yaklaşık 202KB. İl ayrıntısı seçilince yüklenir

Konuşmacı notu: Gösterim için Atlas_2026_Aday.html aç. Bu dosya bir aday inceleme raporudur, otomatik yayın yapmaz.

## Slayt 10 · Kalan doğrulamalar

- Earth Engine erişimiyle C/D gerçek deneyleri
- Windows kurulumu ve Docker/Airflow uçtan uca dağıtımı
- Antalya’da yeni bağımsız doğrulamayla hata azalmasının gösterilmesi
- Etkin veri, DB ve GitHub değişiklikleri için kullanıcı onayı

Konuşmacı notu: Tamamlanmayan adımları tamamlanmış gibi sunma.
