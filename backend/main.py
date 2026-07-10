import os
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import swisseph as swe
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="Fal ve Astroloji Asistanı")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GEMINI API SETUP
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# ==================
# MODELS
# ==================
class AstrolojiRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: float
    lat: float
    lon: float

class PersonData(BaseModel):
    year: int
    month: int
    day: int
    hour: float
    lat: float
    lon: float

class SinastriRequest(BaseModel):
    p1: PersonData
    p2: PersonData

class YildiznameRequest(BaseModel):
    kisi_isim: str
    anne_isim: str
    dogum_tarihi: str

class MatrisRequest(BaseModel):
    dogum_tarihi: str # format DD.MM.YYYY

class ChatRequest(BaseModel):
    fala_dair_bilgiler: str
    fal_turu: str

import time

# ==================
# HELPER FUNCTIONS
# ==================
def get_ai_response(prompt: str, image_bytes: bytes = None, mime_type: str = None) -> str:
    if not client:
        return "Yapay Zeka yorumu kapalı (Gemini API Anahtarı eksik). Sadece matematiksel hesaplamalar gösteriliyor."
    
    contents = [prompt]
    if image_bytes and mime_type:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        
    models_to_try = ['gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-2.0-flash']
    
    for attempt in range(3):
        model_name = models_to_try[attempt]
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            return response.text
        except Exception as e:
            err_str = str(e)
            if "503" in err_str and attempt < 2:
                time.sleep(2) # Farklı bir modele geçmeden önce 2 saniye bekle
                continue
            if attempt == 2:
                return f"Yapay zeka yorumu oluşturulurken hata oluştu: {err_str}"

# ==================
# ROUTES
# ==================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Asistan API çalışıyor."}

@app.post("/api/astroloji")
def calculate_chart(req: AstrolojiRequest):
    try:
        time_utc = req.hour - 3.0 # Basic TR timezone (UTC+3)
        jd = swe.julday(req.year, req.month, req.day, time_utc)
        
        # Gezegenler
        planets = [
            (swe.SUN, "Güneş"), (swe.MOON, "Ay"), (swe.MERCURY, "Merkür"), 
            (swe.VENUS, "Venüs"), (swe.MARS, "Mars"), (swe.JUPITER, "Jüpiter"), 
            (swe.SATURN, "Satürn"), (swe.URANUS, "Uranüs"), (swe.NEPTUNE, "Neptün"), 
            (swe.PLUTO, "Plüton"), (swe.TRUE_NODE, "Kuzey Ay Düğümü"), 
            (swe.CHIRON, "Chiron"), (swe.MEAN_APOG, "Lilith")
        ]
        
        zodiac_signs = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
        
        planet_data = {}
        planet_lons = {}
        for p_id, p_name in planets:
            try:
                res, _ = swe.calc_ut(jd, p_id, swe.FLG_MOSEPH)
                lon = res[0]
                planet_lons[p_name] = lon
                zodiac_idx = int(lon / 30)
                degree = lon % 30
                planet_data[p_name] = f"{degree:.2f}° {zodiac_signs[zodiac_idx]}"
            except swe.Error:
                pass # Ephemeris dosyası yoksa bu noktayı atla
            
        # Evler (Placidus sistemi 'P')
        try:
            cusps, ascmc = swe.houses(jd, req.lat, req.lon, b'P')
            ascendant = ascmc[0]
            asc_sign = zodiac_signs[int(ascendant / 30)]
            mc = ascmc[1]
            mc_sign = zodiac_signs[int(mc / 30)]
            
            house_data = {
                "Yükselen (ASC - 1.Ev)": f"{ascendant % 30:.2f}° {asc_sign}",
                "Tepe (MC - 10.Ev)": f"{mc % 30:.2f}° {mc_sign}"
            }
            
            for i in range(12):
                h_lon = cusps[i]
                house_data[f"{i+1}. Ev Girişi"] = f"{h_lon % 30:.2f}° {zodiac_signs[int(h_lon / 30)]}"
                
            planet_houses = {}
            for p_name, p_lon in planet_lons.items():
                h_num = 12
                for i in range(11):
                    if cusps[i] < cusps[i+1]:
                        if cusps[i] <= p_lon < cusps[i+1]:
                            h_num = i + 1
                            break
                    else:
                        if p_lon >= cusps[i] or p_lon < cusps[i+1]:
                            h_num = i + 1
                            break
                planet_houses[p_name] = f"{h_num}. Ev"
                
        except swe.Error:
            house_data = {"Bilgi": "Ev hesaplaması eksik."}
            planet_houses = {}
            
        # Açılar
        aspects = []
        p_names = list(planet_lons.keys())
        for i in range(len(p_names)):
            for j in range(i+1, len(p_names)):
                p1, p2 = p_names[i], p_names[j]
                diff = abs(planet_lons[p1] - planet_lons[p2])
                if diff > 180: diff = 360 - diff
                
                if diff <= 8: aspects.append(f"{p1} Kavuşum {p2}")
                elif abs(diff - 60) <= 6: aspects.append(f"{p1} Sekstil {p2}")
                elif abs(diff - 90) <= 8: aspects.append(f"{p1} Kare {p2}")
                elif abs(diff - 120) <= 8: aspects.append(f"{p1} Üçgen {p2}")
                elif abs(diff - 180) <= 8: aspects.append(f"{p1} Karşıt {p2}")
        
        raw_text = f"Gezegenlerin Burçları: {planet_data}\nGezegenlerin Evleri: {planet_houses}\nEv Girişleri: {house_data}\nÖnemli Açılar (Aspects): {aspects}"
        
        # AI Yorumu
        prompt = f"""Sen dünya çapında çok ünlü, derin bir bilgiye sahip profesyonel bir astrologsun. Müşterim "Doğum haritamı en ince detayına kadar, her zerresini yorumla" dedi. Müşterim için %100 detaylı ve inanılmaz ayrıntılı bir harita analizi yapacaksın.
Harita Verisi:
{raw_text}

Kesinlikle uyulması gereken kurallar:
1. Her gezegenin hem hangi BURÇTA hem de hangi EVDE olduğunu birlikte yorumla (Örn: "Venüs Akrep burcunda ve 7. Evde, bunun anlamı...").
2. Çıkan tüm temel AÇILARI (Kavuşum, Kare, Üçgen, Karşıt) mutlaka tek tek analiz et, hayatına etkisini anlat.
3. 12 Evin de hangi burçla başladığını (Ev Girişleri) genel hatlarıyla kaderine etkisini açıkla.
4. "Neyin neden geldiğini" ispatlayarak anlat. Analiz ÇOK UZUN, ansiklopedik bir rehber kalitesinde olmalı. Yüzeysel tek bir cümle bile geçme. Analizin bir sanat eseri gibi zengin olsun."""

        ai_yorum = get_ai_response(prompt)

        return {
            "status": "success", 
            "data": {
                "gezegenler": planet_data,
                "evler": house_data,
                "detayli_yorum": ai_yorum
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sinastri")
async def calculate_sinastri(req: SinastriRequest):
    try:
        def get_planets(p: PersonData):
            jd = swe.julday(p.year, p.month, p.day, p.hour - 3.0)
            planets_list = [
                (swe.SUN, "Güneş"), (swe.MOON, "Ay"), (swe.MERCURY, "Merkür"), 
                (swe.VENUS, "Venüs"), (swe.MARS, "Mars"), (swe.JUPITER, "Jüpiter"), 
                (swe.SATURN, "Satürn"), (swe.URANUS, "Uranüs"), (swe.NEPTUNE, "Neptün"), 
                (swe.PLUTO, "Plüton"), (swe.TRUE_NODE, "Kuzey Ay Düğümü"), (swe.CHIRON, "Chiron")
            ]
            lons = {}
            for p_id, p_name in planets_list:
                try:
                    res, _ = swe.calc_ut(jd, p_id, swe.FLG_MOSEPH)
                    lons[p_name] = res[0]
                except:
                    pass
            return lons
            
        lons1 = get_planets(req.p1)
        lons2 = get_planets(req.p2)
        
        cross_aspects = []
        for p1_name, p1_lon in lons1.items():
            for p2_name, p2_lon in lons2.items():
                diff = abs(p1_lon - p2_lon)
                if diff > 180: diff = 360 - diff
                
                orb = 6
                if p1_name in ["Güneş", "Ay"] or p2_name in ["Güneş", "Ay"]: orb = 8
                
                if diff <= orb: cross_aspects.append(f"1. Kişinin {p1_name}'i ile 2. Kişinin {p2_name}'i KAVUŞUM")
                elif abs(diff - 60) <= 5: cross_aspects.append(f"1. Kişinin {p1_name}'i ile 2. Kişinin {p2_name}'i SEKSTİL")
                elif abs(diff - 90) <= orb: cross_aspects.append(f"1. Kişinin {p1_name}'i ile 2. Kişinin {p2_name}'i KARE")
                elif abs(diff - 120) <= orb: cross_aspects.append(f"1. Kişinin {p1_name}'i ile 2. Kişinin {p2_name}'i ÜÇGEN")
                elif abs(diff - 180) <= orb: cross_aspects.append(f"1. Kişinin {p1_name}'i ile 2. Kişinin {p2_name}'i KARŞIT")
                
        raw_text = f"Çapraz Açılar:\n" + "\n".join(cross_aspects)
        
        prompt = f"""Sen dünyaca ünlü bir ilişki astroloğusun. Bana "İlişki Uyumu (Sinastri)" analizi yapacaksın.
Aşağıda 1. Kişi (Müşteri) ile 2. Kişi (Partner) arasındaki astrolojik Çapraz Açıların (Cross-Aspects) tam listesi var:
{raw_text}

KURALLAR:
1. Gördüğün tüm açıları (Kare, Üçgen, Kavuşum, Karşıt vb.) iki kişi arasındaki ilişkide ne anlama geldiğini net ispatlayarak yorumla. (Örn: Güneş - Ay kavuşumu ruhsal bağı temsil eder, Mars-Venüs Karesi tutku ve kavgayı getirir...)
2. İkili arasında hangi konularda mükemmel uyum var? Hangi konularda tartışma veya toksik döngü ihtimali var?
3. Karmik bir bağ veya kadersel bir eşlik var mı? Varsa hangi gezegenlere dayanarak bunu söylüyorsun?
4. Müşteriye "ilişkinin gidişatı ve temel dinamikleri" hakkında %100 detaylı, ansiklopedi uzunluğunda ve aşırı doyurucu bir rehberlik sun. Müşteri adeta büyülenmeli."""

        from fastapi.concurrency import run_in_threadpool
        ai_yorum = await run_in_threadpool(get_ai_response, prompt)
        
        if "hata oluştu" in ai_yorum:
            raise HTTPException(status_code=500, detail=ai_yorum)
            
        return {
            "status": "success",
            "data": {
                "cross_aspects": cross_aspects,
                "detayli_yorum": ai_yorum
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yildizname")
def calculate_yildizname(req: YildiznameRequest):
    ebced_map = {
        'a':1, 'b':2, 'c':3, 'ç':3, 'd':4, 'e':1, 'f':80, 'g':1000, 'ğ':1000, 'h':8, 
        'ı':10, 'i':10, 'j':3, 'k':20, 'l':30, 'm':40, 'n':50, 'o':6, 'ö':6, 'p':2, 
        'r':200, 's':60, 'ş':300, 't':400, 'u':6, 'ü':6, 'v':6, 'y':10, 'z':7, ' ':0
    }
    
    def calculate_ebced(name):
        name = name.lower()
        return sum(ebced_map.get(char, 0) for char in name)
        
    kisi_ebced = calculate_ebced(req.kisi_isim)
    anne_ebced = calculate_ebced(req.anne_isim)
    toplam_ebced = kisi_ebced + anne_ebced
    
    burclar = [
        "Balık (Sıfır kalanı)", "Koç", "Boğa", "İkizler", "Yengeç", "Aslan", 
        "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova"
    ]
    kalan = toplam_ebced % 12
    yildizname_burcu = burclar[kalan]
    
    gezegenler = ["Güneş", "Ay", "Merkür", "Venüs", "Mars", "Jüpiter", "Satürn"]
    gezegen = gezegenler[toplam_ebced % 7]
    
    raw_data = f"İsim: {req.kisi_isim} ({kisi_ebced}), Anne: {req.anne_isim} ({anne_ebced}), Toplam Ebced Değeri: {toplam_ebced}, Yıldızname Burcu: {yildizname_burcu}, Yönetici Gezegen: {gezegen}"

    prompt = f"""Sen geleneksel ilimlere, havas ilmine ve yıldıznameye (İslami Astroloji) son derece hakim, bilge bir üstadsın. Müşterim için %100 detaylı ve her şeyin kökenini açıklayan bir Yıldızname analizi yapacaksın.
Veriler:
{raw_data}

Kesinlikle uyulması gereken kurallar:
1. Ebced hesabının ne anlama geldiğini, isimlerin bu sayılara nasıl dönüştüğünü ve bu sayıların kaderi nasıl etkilediğini mantığıyla anlat.
2. Çıkan Yıldızname burcunun ve Yönetici Gezegenin İslami/Havas astrolojisindeki %100 detaylı karşılığını yaz. Neyin neden geldiğini açıkla (Örn: "Yönetici gezegenin Satürn/Zühal olduğu için bu senin fıtratına şu ağırlığı verir, çünkü Zühal şunları temsil eder...").
3. Kişinin hayat yolunu, hastalık potansiyellerini, rızkını ve nazara yatkınlığını NEDENLERİYLE BİRLİKTE en ince ayrıntısına kadar açıkla. Analiz çok uzun ve tatmin edici bir rehber olsun."""

    ai_yorum = get_ai_response(prompt)

    return {
        "status": "success",
        "data": {
            "ebced_hesabi": f"Kişi: {kisi_ebced}, Anne: {anne_ebced}, Toplam: {toplam_ebced}",
            "yildizname_burcu": yildizname_burcu,
            "yonetici_gezegen": gezegen,
            "detayli_yorum": ai_yorum
        }
    }

@app.post("/api/matris")
def calculate_matrix(req: MatrisRequest):
    try:
        parts = req.dogum_tarihi.split(".")
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        
        def reduce_to_22(num):
            while num > 22:
                num -= 22
            return num if num > 0 else 22
            
        def sum_digits(num):
            return sum(int(digit) for digit in str(num))
            
        # Ana Noktalar
        kisisel_profil = reduce_to_22(d) # Gün
        ruhsal_baglanti = reduce_to_22(m) # Ay
        gecmis_karma = reduce_to_22(sum_digits(y)) # Yıl
        gelecek_potansiyeli = reduce_to_22(kisisel_profil + ruhsal_baglanti + gecmis_karma) # Alt toplam
        
        merkez = reduce_to_22(kisisel_profil + ruhsal_baglanti + gecmis_karma + gelecek_potansiyeli)
        
        # Detaylar
        para_hatti = reduce_to_22(gecmis_karma + merkez)
        ask_hatti = reduce_to_22(gelecek_potansiyeli + merkez)
        
        matrix_data = {
            "Kişisel Profil (Dış Dünyaya Sunum)": kisisel_profil,
            "Ruhsal ve İlahi Bağlantı": ruhsal_baglanti,
            "Geçmiş Yaşam Karması": gecmis_karma,
            "Gelecek Potansiyeli ve Sınavlar": gelecek_potansiyeli,
            "Merkez (Konfor Alanı, Temel Enerji)": merkez,
            "Para ve Kariyer Hattı": para_hatti,
            "Aşk ve İlişkiler Hattı": ask_hatti
        }
        
        prompt = f"""Sen Destiny Matrix (Kader Matrisi - 22 Arkana) sistemini kusursuz bilen uzman bir numerologsun. Müşterim için 100/100 detaylı, her şeyin temelini açıklayan bir Kader Matrisi analizi yapacaksın.
Veriler (Temsil ettikleri tarot arkanaları):
{matrix_data}

Kesinlikle uyulması gereken kurallar:
1. Bulunan HER BİR noktanın (Kişisel Profil, Ruhsal Bağlantı, Geçmiş Karma, Gelecek, Merkez, Para, Aşk) ne anlama geldiğini ve oraya düşen sayının (Tarot Arkanasının) o alanı nasıl etkilediğini MANTIĞIYLA açıkla.
2. Neyin neden olduğunu göster. (Örn: "Geçmiş Karmik Kuyruğunda 15 numaralı Şeytan arkana var, bu yüzden geçmiş yaşamında şu hataları yaptın ve bu hayatına şöyle yansıdı..." gibi).
3. Analiz son derece derin, uzun ve açıklayıcı olsun. Müşteri bu analizi okuduğunda "Bunu tam olarak şu sayıdan/arkanadan dolayı yaşıyormuşum" diyebilsin."""

        ai_yorum = get_ai_response(prompt)

        return {
            "status": "success",
            "data": {
                "matris_kodlari": matrix_data,
                "detayli_yorum": ai_yorum
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Geçersiz tarih formatı. Lütfen GG.AA.YYYY formatında giriniz.")

@app.post("/api/ai-yorum")
async def get_ai_yorum(
    fal_deste: str = Form(...),
    fal_acilim: str = Form(...),
    fala_dair_bilgiler: str = Form(...),
    image: UploadFile = File(None)
):
    try:
        prompt = f"""Sen dünya çapında çok yetenekli, psişik yetenekleri olan usta bir kart okuyucusu ve kâhinsin.
Kullanılan Deste: {fal_deste}
Seçilen Açılım Sistemi (Spread): {fal_acilim}

Müşterinin paylaştığı kartlar, çıkan semboller veya niyetleri:
{fala_dair_bilgiler}

KESİNLİKLE UYMAN GEREKEN KURALLAR:
1. Yorumu tamamen "Seçilen Açılım Sistemi"nin (Spread) pozisyon kurallarına göre yap. (Örneğin 12'li açılımsa her kartı düştüğü evin anlamıyla oku. 5'li Haç ise her kartı düştüğü pozisyona göre oku).
2. Kartları sıradan bir liste gibi anlatıp geçme. Kartlar arasındaki bağlantıları, kadersel mesajları ve sembolojik derinlikleri birbiriyle çarpıştırarak harika bir hikaye yarat.
3. Eğer sisteme bir GÖRSEL yüklendiyse, önce o görseldeki kartları veya sembolleri çok dikkatli incele, resimdeki detayları destenin özelliklerine göre analiz et.
4. Analizin "%100" detaylı, çok uzun ve adeta bir ansiklopedi kalitesinde olsun. Yüzeysel tek bir cümle kullanma.
5. Müşterinin aklındaki soruları, korkuları ve kadersel döngüleri en dürüst şekilde (sert bile olsa aydınlatıcı bir dille) açıkla."""
    
        image_bytes = None
        mime_type = None
        if image and image.filename:
            image_bytes = await image.read()
            mime_type = image.content_type
            
        from fastapi.concurrency import run_in_threadpool
        ai_yorum = await run_in_threadpool(get_ai_response, prompt, image_bytes, mime_type)
        
        if "hata oluştu" in ai_yorum:
            raise HTTPException(status_code=500, detail=ai_yorum)
            
        return {"status": "success", "yorum": ai_yorum}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================
# STATIC FILES (FRONTEND)
# ==================
import os
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
