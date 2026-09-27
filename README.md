# Hisse Radar

Mobil uyumlu PWA hisse araştırma paneli.

## Radar puanı
- Insider işlemleri: 20
- Kongre işlemleri: 15
- Kurumsal hareketler: 10
- Analist revizyonları: 15
- Finansal büyüme: 15
- Değerleme: 10
- Alternatif veri: 5
- Momentum: 10

## Sonraki aşama
Canlı fiyat, finansallar, analist verileri, SEC insider/13F ve Kongre bildirimleri bağlanacak. API anahtarları tarayıcı koduna gömülmeyecek.

## Ajan araştırma masası

Global Niche veri üretimi fiyatın çekildiği zamanı (`fetchedAt`) gerçek son fiyat
ve işlem kayıtlarından (`lastBarAt`, `lastTradedAt`) ayırır; kaynak adresini ve
borsa saat dilimini saklar. Yeni fiyat yanıtı, geçerli fiyat, hacim geçmişi ve
son beş gün içinde pozitif hacimli işlem kaydı olmayan adaylar ana sıralamada
puan almaz, **VERİ ENGELİ** olarak gösterilir. Uzun piyasa tatillerinde bu
sınır araştırma adaylarını geçici olarak engelleyebilir.

`agent_radar.py` aynı veri kapısını bağımsız kontrol eder. Temel finansal
verinin eksikliği her adayda ayrıca işaretlenir.

GitHub Actions içindeki **Human Command Agent Radar** yalnızca elle başlatılır.
`OPENAI_API_KEY` repository secret olarak tanımlıysa en fazla üç uygun adayın
her biri için üç dar görevli AI araştırma notu üretir (en fazla dokuz API
çağrısı). Secret yoksa ücretsiz veri kontrolü raporu üretir; AI çalıştığını
iddia etmez. Rapor `data/agent-radar.json` dosyasına yazılır ve sitede görünür.
API kullanımı ayrıca ücretlendirilir. İş akışında aracı kurum bağlantısı,
otomatik emir veya al/sat komutu bulunmaz; tüm işlem kararları kullanıcıdadır.

## Küresel işlem hazırlığı

Türkiye'den hesap açılabilen Interactive Brokers, pek çok dünya piyasasına
erişim ve kâğıt işlem API'si için inceleniyor. Bu depoda bir IBKR hesabı,
geçerli Gateway oturumu veya işlem yetkisi henüz yoktur. IBKR bireysel API
oturumu günlük yeniden kimlik doğrulaması gerektirir. Borsa bazındaki fiyat
abonelikleri, işlem izinleri, enstrüman sözleşmeleri ve piyasa takvimleri
doğrulanmadan gerçek ya da kâğıt emir gönderilmez.

`global_execution.py` adayları bu koşullara göre denetler; dört saatte bir
çalışan **Global Execution Readiness** iş akışı `data/execution-readiness.json`
raporunu günceller. Bu rapor sitede görünür. İlk pilot sınırı $100, yedi gün,
tek pozisyonda en fazla $20 ve $10 kayıpta yeni emirleri durdurma taslağıdır;
henüz bir işlem stratejisi veya kâr garantisi değildir. Tasarlanan sermaye
kuralında $100 önce $1.000 işlem sermayesine ulaşır; bu tutar korunur. Bundan
sonra gerçekleşmiş ve çekilebilir kârın her $10.000 dilimi raporda kaydedilir.
Eşik açık pozisyon değeri veya henüz takas olmamış satış gelirini kapsamaz.
Sistem banka bildirimi veya otomatik banka transferi başlatmaz.
Kişisel banka hesabına para çekme işlemi kullanıcının aracı kurum portalında
tamamlanacaktır. Bu hazırlık denetimi hiçbir API anahtarı kullanmaz.

Yahoo günlük barlarının zaman damgası örnek veride borsa açılış saatiyle
eşleşir; rapordaki `lastTradedAt` alanı son işlem anı olarak yorumlanmamalıdır.
EODHD ile doğrulanmamış BIST sembolleri otomatik eşleştirilmez.
