# Hisse Radar

Mobil uyumlu PWA hisse araştırma paneli.

## Dinamik küresel keşif

`global-niche-radar.yml` dört saatte bir çalışır. Nasdaq Trader'ın resmî hisse
listesi ve `EODHD_API_KEY` repository secret tanımlıysa EODHD'nin LSE, XETRA,
Euronext Paris/Amsterdam ve Hong Kong hisse listelerinden her tur en fazla 30
sembolü borsalara dağıtarak seçer. Liste bir günde yeniden alınır. EODHD ücretsiz
katmanında günlük çağrı ve veri kapsamı sınırları vardır; key yoksa Avrupa/Hong
Kong listeleri taranmış gibi gösterilmez. Resmî liste bulunamazsa ilgili piyasa
bu tur keşif evreninde yer almaz. `data/niche-universe-cache.json` yalnızca
halka açık sembol/şirket listelerini tutar, API token içermez.

Seçilen semboller Yahoo günlük fiyat geçmişiyle denenir. Bu kaynağın otomatik
toplu tarama için kullanım ve erişim güvencesi yoktur; 30 sorgu yanıtının
kaçının yeni olduğu ayrıca raporlanır. Dinamik keşif kartına araştırma sinyali
verilmesi için geçerli fiyat/hacim kapısı yanında 20 günlük ortalamanın en az
1,5 katı hacim ve beş günde mutlak %5 fiyat hareketi aranır. Bunlar doğrulanmış
bir şirket tezi veya kazanç tahmini değildir. Önceki turda taranmış semboller
arama için tutulur ama fiyat yenilenmediyse `YENİLENMEDİ` işaretlenir.

Sitede piyasa, sembol ve görünüm filtresi, 30'lu sayfalama, evren/tur/birikmiş
keşif sayıları ve raporun zamanı vardır. Yeni uygun sembol belirdiğinde sayfa
açıkken uygulama içi alarm gösterilir; ilk açılış mevcut sinyalleri yeni alarm
saymaz. Sekme kapalıyken anlık telefon bildirimi yoktur; açık sayfa 15 dakikada
bir yayınlanan veriyi kontrol eder. Yazılım kendi kodunu ve işlem kurallarını
otomatik değiştirmez. IBKR otomatik kâğıt/canlı işlem bağlantısı henüz yoktur.

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
oturumu için düzenli yeniden kimlik doğrulaması gerekir. IB Gateway otomatik
yeniden başlatmayla hafta içinde oturumu sürdürebilir; haftalık manuel giriş
gerekir. Borsa bazındaki fiyat
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

## Telefonla manuel araştırma akışı

IBKR hesap başvurusu onaylanana kadar işlem entegrasyonu kurulmaz. Hisse Radar
ajan araştırma kartlarında sembol kopyalama düğmesi vardır. Kullanıcı sembolü
IBKR Mobile'da aratır ve doğru enstrümanı, borsayı, güncel fiyatı, komisyonu
ve emir tutarını kendisi denetler. Semboller aracı kurum sözleşme kimliği
değildir; adaylar emir önerisi sayılmaz. Önce kâğıt işlem kullanılır. Telefon
tarayıcısı IB Gateway API sunucusu olarak çalışmaz; Hisse Radar IBKR'ye emir
veya çekim talimatı göndermez.

Yahoo günlük barlarının zaman damgası örnek veride borsa açılış saatiyle
eşleşir; rapordaki `lastTradedAt` alanı son işlem anı olarak yorumlanmamalıdır.
EODHD ile doğrulanmamış BIST sembolleri otomatik eşleştirilmez.

## Kâğıt pilot günlüğü

Global Niş panelindeki günlük, yalnızca tarayıcının yerel depolama alanına
varsayımsal veya IBKR kâğıt işlem sonuçlarını kaydeder. Alış tutarı en fazla
100 USD'dir; satış değeri, alış/satış komisyonu ve kur/spread maliyeti ayrı
girilir. Net sonuç `satış - alış - komisyon - diğer maliyet` olarak hesaplanır.
CSV dışa aktarımı ve yerel kayıt silme vardır. GitHub Pages'e hesap numarası,
IBAN, şifre veya işlem günlüğü yüklenmez. Tarayıcı verisi temizlenirse günlüğün
yerel kaydı kaybolur; CSV yedeği kullanıcı tarafından saklanmalıdır. Bu günlük
aracı kurumdaki emir veya bakiye ile otomatik mutabakat yapmaz.
