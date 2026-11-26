# Geliştirme durumu — 24 Kasım 2026

Ayrıntılı 30 madde ve dosya/test eşleştirmesi `DUZELTME_TAKIBI.md` içindedir.

- **Güvenilir temel:** yedek ve dal, model şeması, veri kalitesi, aday yayın ve rollback kodları doğrulandı. Windows doğrulaması ve mevcut veriye etkinleştirme onayı bekliyor.
- **ML/veri bilimi:** 2026 aday gözlemleri, sabit model testi, mekânsal bloklar, Antalya analizi, 81 il/kapsam, güven aralıkları ve drift raporları üretildi. Köppen–Geiger dış iklim sınıflarıyla yedi grupta hata karşılaştırması eklendi. C/D erişim bekliyor; Antalya’da kanıtlanmış iyileşme açık.
- **Yazılım:** .NET, PostgreSQL/PostGIS ve web birlikte test edildi. CI kapsamı genişletildi. Yeni GitHub işlerinin çalışması ve Windows Docker doğrulaması bekliyor.
- **Büyük veri/teslim:** 2,67 milyon gerçek pikselde benchmark tamamlandı. Airflow güncellemesi kod düzeyinde hazır; scheduler/Docker uçtan uca doğrulanmadı. Raporlar ve tekrar komutları teslimde.

## Yetki sınırı

Kullanıcının mevcut veri/model dosyaları değiştirilmedi. Gerçek veritabanına migration/yayın uygulanmadı, Git push yapılmadı. 2026 kayıtları ve yeni modeller aday/deney klasörlerindedir. Test veritabanı yalnızca bu çalışma için oluşturulan geçici, izole bir ortamdır. Google hesabı/anahtarı/tokenı oluşturulmadı; GEE girişini kullanıcı yapacaktır.
