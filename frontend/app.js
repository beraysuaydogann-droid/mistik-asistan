const API_BASE = window.location.origin + "/api";

function formatText(text) {
    if (!text) return "";
    return text.replace(/\n/g, '<br>');
}

// Tab Switching Logic
function switchTab(targetId) {
    document.querySelectorAll('.page-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(targetId).classList.add('active');
    const btn = document.querySelector(`.nav-btn[data-target="${targetId}"]`);
    if(btn) btn.classList.add('active');
}

document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        switchTab(e.currentTarget.dataset.target);
    });
});

// Şehir Koordinatları kaldırıldı, kullanıcı doğrudan Enlem/Boylam girecek.

// Astroloji Form Submit
document.getElementById('astroloji-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const resultDiv = document.getElementById('astro-result');
    
    btn.innerHTML = 'Konum Aranıyor... <i class="loader"></i>';
    btn.disabled = true;
    resultDiv.classList.add('hidden');
    
    const locationQuery = document.getElementById('astro-location').value;
    let latVal = 41.0082;
    let lonVal = 28.9784;
    
    try {
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(locationQuery)}&format=json&limit=1`);
        const geoData = await geoRes.json();
        
        if (geoData && geoData.length > 0) {
            latVal = parseFloat(geoData[0].lat);
            lonVal = parseFloat(geoData[0].lon);
        } else {
            alert("Girdiğiniz konum bulunamadı. Lütfen 'İlçe, İl, Ülke' formatında tekrar deneyin.");
            btn.innerHTML = 'Haritayı Hesapla';
            btn.disabled = false;
            return;
        }
    } catch (err) {
        console.error("Geocoding error:", err);
    }
    
    btn.innerHTML = 'Yıldızlar Okunuyor... <i class="loader"></i>';
    
    const timeVal = document.getElementById('astro-time').value; // Örn: "14:05"
    let parsedHour = 12.0;
    if (timeVal) {
        const parts = timeVal.split(':');
        parsedHour = parseInt(parts[0]) + (parseInt(parts[1]) / 60.0);
    }
    
    const data = {
        year: parseInt(document.getElementById('astro-year').value),
        month: parseInt(document.getElementById('astro-month').value),
        day: parseInt(document.getElementById('astro-day').value),
        hour: parsedHour,
        lat: latVal, 
        lon: lonVal
    };

    try {
        const res = await fetch(`${API_BASE}/astroloji`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        const resultDiv = document.getElementById('astro-result');
        resultDiv.classList.remove('hidden');
        
        if (result.status === 'success') {
            let html = '<h3>✨ Matematiksel Veriler</h3><ul>';
            for (const [planet, pos] of Object.entries(result.data.gezegenler)) {
                html += `<li><strong>${planet}:</strong> ${pos}</li>`;
            }
            for (const [house, pos] of Object.entries(result.data.evler)) {
                html += `<li><strong>${house}:</strong> ${pos}</li>`;
            }
            html += '</ul>';
            
            html += '<h3>🔮 Yapay Zeka Harita Sentezi</h3>';
            html += `<p style="margin-top:1rem; font-size:1.05rem; line-height:1.8;">${formatText(result.data.detayli_yorum)}</p>`;
            
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<p style="color:red">Hata: ${result.detail}</p>`;
        }
    } catch (err) {
        alert("Sunucuya bağlanılamadı.");
    } finally {
        btn.innerHTML = 'Haritayı Hesapla ve Yorumla';
        btn.disabled = false;
    }
});

// Sinastri Form Submit
document.getElementById('sinastri-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const resultDiv = document.getElementById('sinastri-result');
    
    btn.innerHTML = 'Konumlar Aranıyor... <i class="loader"></i>';
    btn.disabled = true;
    resultDiv.classList.add('hidden');
    
    const loc1 = document.getElementById('s1-location').value;
    const loc2 = document.getElementById('s2-location').value;
    
    let lat1=41.0, lon1=28.9, lat2=41.0, lon2=28.9;
    
    try {
        const r1 = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(loc1)}&format=json&limit=1`);
        const d1 = await r1.json();
        if(d1 && d1.length>0) { lat1=parseFloat(d1[0].lat); lon1=parseFloat(d1[0].lon); }
        
        const r2 = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(loc2)}&format=json&limit=1`);
        const d2 = await r2.json();
        if(d2 && d2.length>0) { lat2=parseFloat(d2[0].lat); lon2=parseFloat(d2[0].lon); }
    } catch(err) {
        console.error("Geocode err", err);
    }
    
    btn.innerHTML = 'Uyumluluk Hesaplanıyor... <i class="loader"></i>';
    
    const parseHour = (timeStr) => {
        if(!timeStr) return 12.0;
        const p = timeStr.split(':');
        return parseInt(p[0]) + (parseInt(p[1])/60.0);
    };
    
    const data = {
        p1: {
            year: parseInt(document.getElementById('s1-year').value),
            month: parseInt(document.getElementById('s1-month').value),
            day: parseInt(document.getElementById('s1-day').value),
            hour: parseHour(document.getElementById('s1-time').value),
            lat: lat1, lon: lon1
        },
        p2: {
            year: parseInt(document.getElementById('s2-year').value),
            month: parseInt(document.getElementById('s2-month').value),
            day: parseInt(document.getElementById('s2-day').value),
            hour: parseHour(document.getElementById('s2-time').value),
            lat: lat2, lon: lon2
        }
    };
    
    try {
        const res = await fetch(`${API_BASE}/sinastri`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        resultDiv.classList.remove('hidden');
        if (result.status === 'success') {
            let html = `<h3>✨ Sinastri Çapraz Açı Etkileşimleri</h3><ul>`;
            result.data.cross_aspects.forEach(asp => {
                html += `<li>${asp}</li>`;
            });
            html += `</ul><hr style="border-color: rgba(102, 252, 241, 0.2); margin: 1.5rem 0;">`;
            html += `<h3>🔮 Yapay Zeka İle Derin Uyum Analizi</h3>`;
            html += `<p style="margin-top:1rem; font-size:1.05rem; line-height:1.8;">${formatText(result.data.detayli_yorum)}</p>`;
            resultDiv.innerHTML = html;
        } else {
            resultDiv.innerHTML = `<p style="color:red">Hata: ${result.detail}</p>`;
        }
    } catch(err) {
        alert("Bağlantı hatası");
    } finally {
        btn.innerHTML = 'Uyum Haritasını Çıkar';
        btn.disabled = false;
    }
});

// Yıldızname Form
document.getElementById('yildizname-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerHTML = 'Hesaplanıyor...';
    btn.disabled = true;

    const data = {
        kisi_isim: document.getElementById('y-kisi').value,
        anne_isim: document.getElementById('y-anne').value,
        dogum_tarihi: document.getElementById('y-tarih').value
    };

    try {
        const res = await fetch(`${API_BASE}/yildizname`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        const resultDiv = document.getElementById('yildizname-result');
        resultDiv.classList.remove('hidden');
        if (result.status === 'success') {
            resultDiv.innerHTML = `
                <h4>Yıldızname Burcu: ${result.data.yildizname_burcu}</h4>
                <p>Yönetici Gezegen: ${result.data.yonetici_gezegen}</p>
                <p>Ebced Hesabı: ${result.data.ebced_hesabi}</p>
                <hr style="border-color: rgba(102, 252, 241, 0.2); margin: 1rem 0;">
                <p style="font-size:1.05rem; line-height:1.8;">${formatText(result.data.detayli_yorum)}</p>
            `;
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.innerHTML = 'Hesapla ve Yorumla';
        btn.disabled = false;
    }
});

// Matris Form
document.getElementById('matris-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerHTML = 'Hesaplanıyor...';
    btn.disabled = true;

    const data = {
        dogum_tarihi: document.getElementById('m-tarih').value
    };

    try {
        const res = await fetch(`${API_BASE}/matris`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        
        const resultDiv = document.getElementById('matris-result');
        resultDiv.classList.remove('hidden');
        
        if (result.status === 'success') {
            let html = '<ul>';
            for (const [key, val] of Object.entries(result.data.matris_kodlari)) {
                html += `<li><strong>${key}:</strong> ${val}</li>`;
            }
            html += '</ul>';
            html += '<hr style="border-color: rgba(102, 252, 241, 0.2); margin: 1rem 0;">';
            html += `<p style="font-size:1.05rem; line-height:1.8;">${formatText(result.data.detayli_yorum)}</p>`;
            resultDiv.innerHTML = html;
        } else {
             resultDiv.innerHTML = `<p style="color:red">Hata: ${result.detail}</p>`;
        }
    } catch (err) {
        console.error(err);
    } finally {
        btn.innerHTML = 'Çıkar ve Yorumla';
        btn.disabled = false;
    }
});

// AI Fal Yorumu Form
const spreadData = {
    "Klasik Tarot": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "3 Kartlık Zaman Açılımı (Geçmiş, Şimdi, Gelecek)",
        "Kelt Haçı (10 Kartlık Derin Analiz)"
    ],
    "Katina Aşk Falı": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "3 Kartlık İlişki Açılımı (Geçmiş, Şimdi, Gelecek)",
        "5 Kartlık İmparatorluk Haçı (Durum, O, Engel, Tavsiye, Sonuç)",
        "12'li Deste Açılımı (Astrolojik Evler)"
    ],
    "Çingene Tarotu": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "3 Kartlık Zaman Açılımı (Geçmiş, Şimdi, Gelecek)",
        "Kelt Haçı (10 Kartlık Derin Analiz)",
        "Yol Ayrımı Açılımı (7 Kart - Seçenek Kıyaslama)"
    ],
    "Moonology": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "3 Kartlık Ay Döngüsü Açılımı",
        "4 Kartlık Yeni Ay/Dolunay Açılımı"
    ],
    "Kalbin Bağlantıları": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "3 Kartlık Aşk Dinamiği (Sen, O, Gelecek)",
        "5 Kartlık Derin Bağ Açılımı (Kalp, Zihin, Engel, Tavsiye, Kader)"
    ],
    "İskambil Falı": [
        "Tek Kart (Soru-Cevap / Evet-Hayır)",
        "9 Kartlık Çingene Matrisi (3x3)",
        "4 Kartlık İsim Falı"
    ],
    "Geçmiş Yaşam Kartları": [
        "Tek Kart (Karmik Mesaj)",
        "Geçmiş Yaşam Kökleri Açılımı",
        "Karmik Düğüm Analizi"
    ],
    "Kahve Falı": [
        "Fincan İçi ve Tabağı (Genel Analiz)"
    ]
};

document.getElementById('fal-deste').addEventListener('change', (e) => {
    const acilimSelect = document.getElementById('fal-acilim');
    const selectedDeste = e.target.value;
    
    acilimSelect.innerHTML = '<option value="">Açılım Sistemi Seçiniz...</option>';
    
    if (selectedDeste && spreadData[selectedDeste]) {
        spreadData[selectedDeste].forEach(spread => {
            const opt = document.createElement('option');
            opt.value = spread;
            opt.textContent = spread;
            acilimSelect.appendChild(opt);
        });
    } else {
        acilimSelect.innerHTML = '<option value="">Önce Deste Seçiniz...</option>';
    }
});

document.getElementById('fal-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = e.target.querySelector('button');
    const resultDiv = document.getElementById('fal-result');
    const loader = document.getElementById('fal-loader');
    const textDiv = document.getElementById('fal-text');
    
    resultDiv.classList.remove('hidden');
    loader.classList.remove('hidden');
    textDiv.innerHTML = '';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('fal_deste', document.getElementById('fal-deste').value);
    formData.append('fal_acilim', document.getElementById('fal-acilim').value);
    formData.append('fala_dair_bilgiler', document.getElementById('fal-bilgi').value);
    
    const imageFile = document.getElementById('fal-image').files[0];
    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const res = await fetch(`${API_BASE}/ai-yorum`, {
            method: 'POST',
            body: formData
        });
        const result = await res.json();
        
        loader.classList.add('hidden');
        if (result.status === 'success') {
            textDiv.innerHTML = `<p style="font-size:1.05rem; line-height:1.8;">${formatText(result.yorum)}</p>`;
        } else {
            textDiv.innerHTML = `<p style="color:red">Hata: ${result.detail}</p>`;
        }
    } catch (err) {
        loader.classList.add('hidden');
        textDiv.innerHTML = `<p style="color:red">Sunucuya bağlanılamadı veya API hatası.</p>`;
    } finally {
        btn.disabled = false;
    }
});
