🥋 T-Smart: Taekwondo Digital Coach & Analysis System
T-Smart, Taekwondocuların antrenman sırasında yaptıkları teknik hataları tespit eden, bu hataların nasıl düzeltileceğine dair rehberlik sunan ve sporcu gelişimini veri odaklı takip eden modern bir dijital antrenör sistemidir.

🛠️ Teknik Özellikler ve Stack
Bu proje, modern yazılım prensipleri ve kurumsal veri yönetimi araçları kullanılarak geliştirilmiştir:

Modern UI/UX: CustomTkinter ile dinamik ve karanlık mod destekli kullanıcı arayüzü.

Veritabanı Yönetimi: MS SQL Server entegrasyonu ve pyodbc sürücüsü ile güvenli veri depolama.

Güvenlik Katmanı: Kullanıcı bilgileri hashlib (SHA-256) kullanılarak şifrelenmiş şekilde saklanmaktadır.

Veri Analitiği: collections.Counter ve datetime modülleri ile sporcu performans istatistikleri ve tarihsel gelişim takibi.

Görüntü İşleme: Pillow (PIL) ve tkinter.Canvas ile teknik analiz görsellerinin işlenmesi.



📂 Proje Yapısı
main.py: Uygulamanın ana giriş noktası ve arayüz mantığı.

tsmart.sql: Veritabanı tabloları, ilişkiler ve saklı prosedürler (stored procedures).

.gitignore: Gereksiz dosyaların ve hassas bağlantı bilgilerinin güvenliği için yapılandırma.



🚀 Kurulum ve Kullanım
Sisteminizde MS SQL Server'ın kurulu olduğundan emin olun.

tsmart.sql dosyasını SQL Server üzerinde çalıştırarak veritabanı şemasını oluşturun.

Gerekli kütüphaneleri yükleyin:


pip install customtkinter pyodbc Pillow
Uygulamayı başlatın:

python main.py


🎯 Gelecek Hedeflerim
 .OpenCV ve Mediapipe ile anlık video analizi entegrasyonu.

 .Sporcular için grafiksel gelişim raporları.

 .Mobil uygulama desteği (React Native).

Geliştiren: Yiğit Doğan
İzmir Ekonomi Üniversitesi - Bilgisayar Programcılığı
