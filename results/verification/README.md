# Çalıştırılmış kontroller

Son kod doğrulaması: 32 Python testi (`python-tests.txt`), 6 .NET testi (`api-unit-tests.txt`), 5 tarayıcı testi (`web-tests.json`) ve 10 HTTP sözleşme kontrolü (`api-integration.json`). `system-integration.json` izole PostgreSQL/PostGIS kesinti, rollback, yeniden bağlanma, kapsam azalmasını reddetme ve API/snapshot eşitliğini kaydeder.

`offline-html.json` indirilen bağımsız HTML'nin gerçek tarayıcıda açıldığını ve il/tek-piksel yıllarını ayrı gösterdiğini doğrular. `climate-validation.json` gerçek harita kırpımından yeniden üretilen 81 il sonuçlarını denetler.

`environment.json` Linux Python 3.12 ve sabit bağımlılıklardır. Python ve web bağımlılık taraması JSON’ları, .NET taraması metin çıktısıdır. Bunlar tarama zamanının sonuçlarıdır. `p0-existing-tests.txt` değişiklik öncesi 11 testin kaydıdır. `preservation.json` eski 150 veri/model/sonuç dosyasının değişmediğini ve yedeği doğrular.

Windows 11 kurulumu, Docker Compose, Airflow scheduler/panel ve yeni GitHub Actions çalışması bu kayıtlara dahil değildir; henüz bu ortamlarda doğrulanmadı. `system-services.txt` içindeki kasıtlı geçersiz geometri ve bağlantı hataları, başarılı rollback/kesinti senaryolarının parçasıdır.
