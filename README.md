# Hisse Radar

Mobil uyumlu PWA hisse araştırma paneli.

Uygulama her açılışta ve sekmeye geri dönüldüğünde yayımlanmış beş veri
kaynağını ağdan yeniden kontrol eder; ayrıca sayfa açıkken 15 dakikada bir ve
"Verileri yeniden kontrol et" düğmesiyle tekrar yükler. Kaynakların rapor
tarihi, fiyat yanıtı kapsamı ve gecikme durumu görünür. Sayfa açılması GitHub
Actions işini tetiklemez; 20 hisselik ana radar saatlik, dinamik niş radar
saatlik, işlem hazırlığı dört saatte bir ve 13F haftalık planlıdır. Ajan AI
araştırması yalnızca elle başlatılır. GitHub zamanlayıcısı gecikebilir, veri
sağlayıcıları yanıt vermeyebilir ve 13F bildirimleri gerçek zamanlı değildir.

Her iki hisse kartındaki yıldız, sembolü ve piyasayı favorilere ekler. Ana
radarda “Yalnızca favoriler”, küresel keşifte “Favorilerim” görünümü vardır.
Seçimler cihazın tarayıcı depolamasında kalır; hesaplar ve cihazlar arasında
eşitlenmez. Keşif raporundan çıkan bir sembol daha sonra yeniden taranana kadar
favori listesinde görünmez; tarayıcı verileri silinirse yıldızlar da silinir.

Hisse kartına dokununca görsel fiyat özeti, günlük kapanış grafiği ve mevcut
günlük düşük/yüksek ile hacim bilgileri açılır. Grafik 5 işlem günü, yaklaşık
1/3/6 ay ve bir yıllık yayımlanmış kapanış noktalarından oluşur. Yeni veri
iş akışı çalışana dek eski kayıtlarda grafik yerine veri yok açıklaması görünür.
Kaynak gün içi emir defteri, alış/satış kotasyonu veya gerçek zamanlı fiyat
sağlamaz; ekranda bunlara ilişkin değer üretilmez. Her grafik son bar tarihini
ve veri kaynağını belirtir.

## İzleme masası ve teknik görünüm

Matriks Mobil IQ'nun kişiselleştirilmiş izleme ekranları örnek alınarak, ana radar
ve küresel keşif sonuçlarını tek tabloda arayan ve sıralayan bir izleme masası
eklendi. Kullanıcı en fazla 12 yerel liste oluşturup yayımlanan sembolleri bu
listelere ekleyebilir. Listeler yalnızca tarayıcı depolamasında saklanır; farklı
cihazlara eşitlenmez. Tablo son yayımlanan günlük fiyat ve değişimi gösterir.
Hisse detayında mevcut günlük kapanışlardan 20/50 günlük basit ortalama ve
14 değişimlik RSI hesaplanır; yeterli geçmiş yoksa değer gösterilmez.
İzleme masası ve hisse kartları raporun yaşını, küresel hissede fiyatın bu tur
yenilenip yenilenmediğini ve son günlük bar tarihini birlikte kontrol eder.
İzleme masasındaki “Güncel rapor ve bar” filtresi ana radar için iki, küresel
keşif için üç saat içinde yayımlanmış raporu ve son beş takvim gününde oluşmuş
günlük barı gösterir. Beş günlük tolerans hafta sonu ve kısa tatilleri kapsar;
uzun piyasa tatilinde hisse geçici olarak filtre dışı kalabilir. Üstteki veri
kapsamı sayısı bir dizin büyüklüğü değil, bu koşulları sağlayan yayımlanmış
kayıt sayısıdır. Güncel rapor, gün içi canlı fiyat anlamına gelmez.
Bu göstergeler yatırım veya alım satım sinyali değildir. Matriks'in canlı
kotasyon, derinlik, para giriş çıkış ve broker emir işlevleri uygulamaya bağlı
değildir; ilgili veri ve emir yetkileri lisans ve resmi entegrasyon gerektirir.

## Araştırma merkezi

Yayımlanmış hisseler arasından seçilen ürün için günlük kapanışın 20/50 günlük
ortalama konumu ve 14 değişimlik RSI gözlemi gösterilir. Bu gözlemler al/sat
komutu değildir. Ana radarda mevcut gelir/net kâr büyümesi, F/K ve PEG alanları
varsa görünür; raporda dönemli bilanço satırları ve kaynak döneminin tam tarihi
olmadığı için doğrulanmış karşılaştırmalı finansal rapor sayılmaz. KAP'ın
bilanço karşılaştırması, SPK bültenleri, KAP açıklamaları ve TEFAS fon ekranı
resmî kaynak bağlantıları olarak sunulur; dış sitelerin verisi Radar içinde
yeniden yayımlanmaz. Mum formasyonu, yabancı takas, kurum bazlı para akışı,
kurum önerileri, halka arz push bildirimi ve aracı kuruma emir bağlantısı için
gerekli veri/izin bulunmadığında açık durum metni gösterilir. Radar hiçbir
aracı kurum adına emir göndermeye başlamaz.
NASDAQ veya NYSE eşleşmesi açıkça bilinen bir hissede kullanıcı isterse
TradingView'in resmî, atıflı gelişmiş grafik widget'ı yüklenir. Widget üçüncü
taraf veri kaynağıdır; Radar'ın günlük fiyat geçmişine veya işlem motoruna
bağlanmaz. Eşleşmesi bilinmeyen hisselerde sembol tahmin edilmez.

### SEC yıllık temel veri

`sec_financials.py` ana radardaki ABD sembollerini SEC'in resmî ticker/CIK
dizinine eşleyip `companyfacts` kaynağından iki karşılaştırılabilir 10-K mali
yılını seçer. Hasılat, net kâr/zarar, varlık, yükümlülük ve özkaynak için USD
kalemleri, dönemin sonu, dosyalama tarihi ve kullanılan XBRL etiketi
`data/sec-financials.json` içinde ayrı tutulur. Eksik yıllar veya kalemler
uydurulmaz. Farklı muhasebe etiketleri, özel mali yıllar, finans şirketleri ve
yeniden düzenlenen raporlar elle kaynak kontrolü gerektirebilir. Fiyatla
birleştirilmiş değerleme çarpanı bu akıştan hesaplanmaz.

`SEC Annual Fundamentals` işi hafta içi bir kez ve elle çalıştırılabilir.
SEC'in [geliştirici yönergesine](https://www.sec.gov/about/webmaster-frequently-asked-questions)
uygun, ulaşılabilir bir e-posta içeren mevcut GitHub Actions
`SEC_CONTACT_EMAIL` **repository secret** kullanılır. İstekte
`HisseRadar/2.0` tanıtıcısı ile birleştirilir. E-posta kod veya herkese açık veri
dosyasına yazılmaz. Secret yoksa iş eski dosyaya dokunmadan çıkar ve ekranda
"henüz kurulmadı" görünür. SEC tarayıcıdan doğrudan erişime CORS desteği
vermediği için kaynak GitHub Actions üzerinde alınır. Önce
`python -m unittest -v test_sec_financials` ile mali yıl seçimi sınanabilir.

## Dinamik küresel keşif

`global-niche-radar.yml` saatlik çalışır. Nasdaq Trader'ın resmî hisse
listesi ve `EODHD_API_KEY` repository secret tanımlıysa EODHD'nin LSE, XETRA,
Euronext Paris/Amsterdam ve Hong Kong hisse listelerinden her tur en fazla 120
sembolü seçer. Sonraki tur kaldığı yerden devam eder; liste aynı kalırsa 2.778
sembollük evren yaklaşık 24 saatlik döngüde tamamen denenir. İş akışı zamanlaması
ve fiyat kaynağının yanıtları kesin süre veya tüm fiyatların güncelliğini garanti
etmez. Liste bir günde yeniden alınır. EODHD ücretsiz
katmanında günlük çağrı ve veri kapsamı sınırları vardır; key yoksa Avrupa/Hong
Kong listeleri taranmış gibi gösterilmez. Resmî liste bulunamazsa ilgili piyasa
bu tur keşif evreninde yer almaz. `data/niche-universe-cache.json` yalnızca
halka açık sembol/şirket listelerini tutar, API token içermez.

Seçilen semboller Yahoo günlük fiyat geçmişiyle denenir. Bu kaynağın otomatik
toplu tarama için kullanım ve erişim güvencesi yoktur; seçilen 120 sembolden
kaçının güncel fiyat yanıtı olduğu ayrıca raporlanır. Dinamik keşif kartına araştırma sinyali
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

### Yerel otomatik kâğıt pilotu

`python paper_agent.py` araştırma verisini üç ayrı kapıdan geçirir: sinyal,
bağımsız veri ve portföy riski. Yerel `local/paper-state.json` içinde yalnızca
**sanal** 100 USD bakiye ve işlem günlüğü tutar; IBKR'ye ağ çağrısı, emir veya
para çekme talimatı göndermez. Aynı veri turu ikinci kez çalıştırılırsa yeniden
alım yapmaz. Tek pozisyon üst sınırı 20 USD, beş açık pozisyon, 10 USD toplam
zararda yeni alışları durdurma, örnek 0,25 USD komisyon ve 20 baz puanlık
alış/satış farkı uygulanır. %4 düşüş veya %5 yükseliş ancak yeni ve geçerli
fiyat yanıtı varsa sanal satışa dönüşür. Bu eşikler deney ayarıdır; getiri
tahmini değildir. `python -m unittest -v test_paper_agent` giriş, çıkış, tekrar
çalıştırma, eski fiyat ve zarar sınırını sınar.

Mevcut halka açık radar verisinde temel finansal bilgi, bağımsız doğrulama,
IBKR sözleşme kimliği ve piyasa açık onayı eksik olduğundan bütün adaylar
engellenir. Bu beklenen güvenli sonuçtur. Testler örnek doğrulanmış veriyle
sanal alım ve satım akışını gösterir. İşlemler kullanıcı cihazı veya özel
sunucuda çalıştırılmalıdır; GitHub Pages bir aracı kurum oturumu tutamaz.
Gerçek IBKR kâğıt hesabına geçiş için ayrı Gateway oturumu, broker fiyatı,
borsa/kontrat eşlemesi, hesap izinleri ve emir mutabakatı gerekir. Canlı hesap
bu pilotun kapsamı dışındadır.

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
