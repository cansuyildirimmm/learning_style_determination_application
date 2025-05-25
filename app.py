import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import random

load_dotenv()  # .env dosyasındaki değişkenleri yükler

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Flash mesajları için (isteğe bağlı, şimdilik kullanmıyoruz)

# --- Gemini API Yapılandırması ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("HATA: GEMINI_API_KEY ortam değişkeni bulunamadı. Lütfen .env dosyasını kontrol edin.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Geliştirilmiş Öğrenme Stilleri ve Tanımları ---
LEARNING_STYLES = {
    "visual": {
        "name": "Görsel Öğrenen 🖼️👀 (Hayalperest Gözlemci)",
        "description": "Resimler, grafikler, renkler ve haritalarla dünyayı algılarsın. Bir şeyi görmek, onu anlamanın en iyi yoludur senin için. Zihninde canlandırmayı seversin!",
        "keywords_for_gemini": "görsel öğrenme, zihin haritaları, diyagramlar, renk kodlama, videolar, infografikler, görsel not alma, sunumlar, resimler"
    },
    "auditory": {
        "name": "İşitsel Öğrenen 🎧🗣️ (Melodik Dinleyici)",
        "description": "Sesler, müzik, tartışmalar ve anlatımlar senin için öğrenmenin anahtarı. Dinleyerek ve konuşarak bilgiyi daha iyi işlersin. Ritmler ve tekerlemeler aklında kalır!",
        "keywords_for_gemini": "işitsel öğrenme, sesli kitaplar, podcastler, tartışmalar, grup çalışmaları, müzik, tekerlemeler, bilgiyi sesli tekrar etme, ders anlatımı dinleme"
    },
    "read_write": {
        "name": "Okuma/Yazma Odaklı Öğrenen 📝📖 (Bilge Kelime Ustası)",
        "description": "Kelimelerin gücüne inanırsın! Okumak, not almak, listeler yapmak ve yazılı materyallerle çalışmak senin öğrenme tarzın. Detaylar ve düzen senin için önemlidir.",
        "keywords_for_gemini": "okuma yazma öğrenme, not alma, listeler yapma, metin analizi, makaleler, kitaplar, özet çıkarma, yazılı talimatlar, tanımlar"
    },
    "kinesthetic": {
        "name": "Kinestetik Öğrenen 🤸‍♂️🖐️ (Enerjik Kaşif)",
        "description": "Harekete geçmek, dokunmak ve deneyimlemek senin için en iyi öğrenme yolu! Soyut kavramları bile yaparak, uygulayarak ve canlandırarak somutlaştırırsın.",
        "keywords_for_gemini": "kinestetik öğrenme, yaparak öğrenme, deneyler, rol yapma, canlandırma, model oluşturma, hareket etme, saha gezileri, uygulamalı çalışmalar"
    },
    "social": {
        "name": "Sosyal Öğrenen 🤝💬 (Takım Oyuncusu)",
        "description": "Başkalarıyla etkileşim kurmak, fikir alışverişinde bulunmak ve grup içinde çalışmak öğrenmeni hızlandırır. Tartışmalar ve ortak projeler tam sana göre!",
        "keywords_for_gemini": "sosyal öğrenme, grup çalışması, işbirlikçi projeler, tartışma grupları, başkalarına öğretme, mentorluk, beyin fırtınası"
    },
    "solitary": {
        "name": "Yalnız Öğrenen 🧘‍♂️💡 (İçsel Düşünür)",
        "description": "Kendi başına, sessiz ve sakin bir ortamda çalışmayı tercih edersin. Derinlemesine düşünmek, içselleştirmek ve kendi hızında ilerlemek sana iyi gelir.",
        "keywords_for_gemini": "yalnız öğrenme, bireysel çalışma, kendi kendine öğrenme, sessiz ortam, odaklanma, içsel motivasyon, kişisel hedefler belirleme"
    },
    "logical": {
        "name": "Mantıksal Öğrenen 🧠🔢 (Analitik Zihin)",
        "description": "Neden-sonuç ilişkileri kurmayı, problemleri analiz etmeyi ve mantıksal örüntüleri bulmayı seversin. Düzenli, sistematik ve kanıta dayalı yaklaşımlar senin için idealdir.",
        "keywords_for_gemini": "mantıksal öğrenme, problem çözme, analitik düşünme, neden sonuç ilişkileri, örüntüler, şemalar, sınıflandırma, eleştirel düşünme"
    },
    "multimodal": {
        "name": "Çoklu Modal Öğrenen ✨🔄 (Esnek Uyum Sağlayıcı)",
        "description": "Harika! Sen birden fazla öğrenme stiline yatkınsın. Bu, farklı durumlara ve konulara kolayca uyum sağlayabileceğin anlamına gelir. Esnekliğin senin süper gücün!",
        "keywords_for_gemini": "çoklu modal öğrenme, farklı öğrenme tekniklerini birleştirme, esnek öğrenme stratejileri, duruma göre stil değiştirme, birden fazla duyuya hitap etme"
    }
}

# --- Geliştirilmiş Sorular ---
# Her seçenek, bir veya daha fazla stile belirli bir puan verebilir.
# Örnek: "styles_points": {"visual": 2, "read_write": 1}
QUESTIONS = {
    "q1": {
        "text": "Yeni bir akıllı saat aldın. Özelliklerini nasıl keşfetmeyi tercih edersin?",
        "emoji": "⌚️",
        "options": {
            "A": {"text": "💫 Kutudaki şık broşürdeki görsellere ve şemalara hızlıca göz atarım.",
                  "styles_points": {"visual": 2, "read_write": 1}},
            "B": {
                "text": "🗣️ Saati daha önce kullanan bir arkadaşımdan bana anlatmasını veya bir inceleme videosu izlemeyi tercih ederim.",
                "styles_points": {"auditory": 2, "social": 1, "visual": 1}},
            "C": {"text": "📖 Kullanım kılavuzunu indirip önemli bölümlerini okurum, belki bazı notlar alırım.",
                  "styles_points": {"read_write": 2, "solitary": 1}},
            "D": {"text": "🔧 Saati hemen bileğime takar, tüm menüleri kurcalar, deneyerek öğrenirim.",
                  "styles_points": {"kinesthetic": 2, "logical": 1}}
        }
    },
    "q2": {
        "text": "Karmaşık bir masa oyunu öğreniyorsun. En çabuk nasıl kavrarsın?",
        "emoji": "🎲",
        "options": {
            "A": {"text": "🎨 Oyun tahtasının ve kartların üzerindeki resimlere, sembollere odaklanırım.",
                  "styles_points": {"visual": 2}},
            "B": {"text": "📣 Kuralları bilen birinin bana yüksek sesle anlatmasını ve örnekler vermesini isterim.",
                  "styles_points": {"auditory": 2, "social": 1}},
            "C": {"text": "📜 Kural kitapçığını dikkatlice okur, önemli kuralları kendi cümlelerimle yazarım.",
                  "styles_points": {"read_write": 2, "solitary": 1}},
            "D": {"text": "🤝 Hemen birkaç tur deneme oyunu oynamayı, yaparak ve görerek öğrenmeyi teklif ederim.",
                  "styles_points": {"kinesthetic": 2, "social": 1, "visual": 1}}
        }
    },
    "q3": {
        "text": "Bir gezi planlarken hangi yöntem sana daha çekici gelir?",
        "emoji": "🗺️",
        "options": {
            "A": {
                "text": "🏞️ Gideceğim yerlerin bol fotoğraflı bloglarını, Instagram paylaşımlarını incelerim, haritalara bakarım.",
                "styles_points": {"visual": 2, "read_write": 1}},
            "B": {"text": "🎤 Oraya gitmiş arkadaşlarımla konuşur, onların deneyimlerini ve tavsiyelerini dinlerim.",
                  "styles_points": {"auditory": 2, "social": 1}},
            "C": {"text": "✍️ Detaylı bir seyahat rehberi okur, yapılacaklar listesi ve bütçe planı oluştururum.",
                  "styles_points": {"read_write": 2, "logical": 1, "solitary": 1}},
            "D": {
                "text": "🚶‍♂️ Sanal turlarla gezer, belki gideceğim yerin atmosferini yansıtan müzikler dinleyerek hayal kurarım.",
                "styles_points": {"kinesthetic": 1, "visual": 1, "auditory": 1}}
        }
    },
    "q4": {
        "text": "Yeni bir yazılım programını öğrenmen gerekiyor. İlk ne yaparsın?",
        "emoji": "💻",
        "options": {
            "A": {"text": "🎬 Programın arayüzünü ve özelliklerini gösteren video eğitimlerini izlerim.",
                  "styles_points": {"visual": 2, "auditory": 1}},
            "B": {"text": "💡 Programı bilen bir meslektaşımla oturup bana temel özellikleri göstermesini rica ederim.",
                  "styles_points": {"social": 2, "auditory": 1, "kinesthetic": 1}},
            "C": {"text": "📚 Programın yardım dokümanlarını, SSS (Sıkça Sorulan Sorular) bölümünü okurum.",
                  "styles_points": {"read_write": 2, "solitary": 1}},
            "D": {
                "text": "🖱️ Programı açar, menüleri tıklar, farklı fonksiyonları deneyerek ne işe yaradıklarını anlamaya çalışırım.",
                "styles_points": {"kinesthetic": 2, "logical": 1}}
        }
    },
    "q5": {
        "text": "Bir grup projesinde çalışırken hangi rolü üstlenmeyi seversin?",
        "emoji": "👥",
        "options": {
            "A": {"text": "🎨 Sunumu hazırlamak, görselleri ve tasarımı yapmak.", "styles_points": {"visual": 2}},
            "B": {"text": "🗣️ Fikirleri toplamak, tartışmaları yönetmek ve grubu motive etmek.",
                  "styles_points": {"social": 2, "auditory": 1}},
            "C": {"text": "📝 Araştırmayı yapmak, notları düzenlemek ve raporu yazmak.",
                  "styles_points": {"read_write": 2, "solitary": 1}},
            "D": {"text": "🧩 Projenin adımlarını planlamak, görev dağılımını organize etmek ve süreci takip etmek.",
                  "styles_points": {"logical": 2, "kinesthetic": 1}}
        }
    },
    "q6": {
        "text": "Bir konu hakkında derinlemesine bilgi edinmek istediğinde...",
        "emoji": "🧐",
        "options": {
            "A": {"text": "✨ Konuyu anlatan belgeseller, animasyonlar veya infografikler ararım.",
                  "styles_points": {"visual": 2, "auditory": 1}},
            "B": {"text": "🎧 Uzmanların konuştuğu podcast'leri veya sesli dersleri dinlerim.",
                  "styles_points": {"auditory": 2, "solitary": 1}},
            "C": {"text": "📑 Akademik makaleler, detaylı kitaplar okur, anahtar kavramları not ederim.",
                  "styles_points": {"read_write": 2, "logical": 1}},
            "D": {"text": "🛠️ Konuyla ilgili bir atölyeye katılır, bir model yapar veya bir simülasyon denerim.",
                  "styles_points": {"kinesthetic": 2, "social": 1}}
        }
    },
    "q7": {
        "text": "Stresli olduğunda veya rahatlamak istediğinde ne yaparsın?",
        "emoji": "🧘‍♀️",
        "options": {
            "A": {"text": "🏞️ Güzel manzaralara bakmak, sanat galerilerini gezmek veya film izlemek.",
                  "styles_points": {"visual": 2}},
            "B": {"text": "🎶 Sakinleştirici müzikler dinlemek, doğa seslerini duymak veya bir arkadaşımla dertleşmek.",
                  "styles_points": {"auditory": 2, "social": 1}},
            "C": {"text": "✍️ Günlük tutmak, düşüncelerimi yazmak veya sevdiğim bir kitabı okumak.",
                  "styles_points": {"read_write": 2, "solitary": 1}},
            "D": {"text": "🚶‍♀️ Yürüyüşe çıkmak, yoga yapmak, dans etmek veya el işleriyle uğraşmak.",
                  "styles_points": {"kinesthetic": 2, "solitary": 1}}
        }
    }
}


def determine_learning_style(answers):
    style_scores = {style_key: 0 for style_key in LEARNING_STYLES if style_key != "multimodal"}

    for q_id, chosen_option_key in answers.items():
        if q_id in QUESTIONS and chosen_option_key in QUESTIONS[q_id]["options"]:
            option_styles = QUESTIONS[q_id]["options"][chosen_option_key]["styles_points"]
            for style, points in option_styles.items():
                if style in style_scores:
                    style_scores[style] += points

    if not any(style_scores.values()):  # Eğer hiç puan yoksa (olmamalı ama önlem)
        return random.choice(list(style_scores.keys()))

    # En yüksek skoru ve o skora sahip stilleri bul
    max_score = 0
    dominant_styles = []
    for style, score in style_scores.items():
        if score > max_score:
            max_score = score
            dominant_styles = [style]
        elif score == max_score and max_score > 0:  # Eşitlik durumu (0'dan büyükse)
            dominant_styles.append(style)

    # Eğer 2 veya daha fazla stil eşit ve en yüksek puandaysa "multimodal"
    # Veya belirli bir eşik üzerinde birden fazla stil varsa (örneğin, en yüksek skorun %70'i gibi)
    # Şimdilik basit tutalım:
    if len(dominant_styles) >= 2:  # Eğer 2 veya daha fazla stil eşit baskınsa
        # Multimodal için özel bir durum, ama yine de en baskın olanlardan birini baz alabiliriz
        # Veya doğrudan "multimodal" döndürebiliriz.
        # Şimdilik, bu durumda "multimodal"ı ve içlerinden en çok keywords'ü olanı seçelim (daha çeşitli öneri için)
        # Ya da sadece "multimodal" döndürüp Gemini'ye ona göre prompt yazalım.
        # En iyisi, en baskın olanlardan rastgele birini seçip, Gemini prompt'unda bunun "multimodal" bir profilin parçası olduğunu belirtmek.
        # Ya da daha basit: Eğer 2 veya daha fazla stil eşitse "multimodal" de.
        # En yüksek skorları alan stillere bakalım. Eğer aralarında çok fark yoksa multimodal olabilir.
        # sorted_styles = sorted(style_scores.items(), key=lambda item: item[1], reverse=True)
        # if len(sorted_styles) > 1 and sorted_styles[0][1] == sorted_styles[1][1]: # Eğer ilk iki eşitse
        #     return "multimodal" # Bu en basit yaklaşım.
        # return sorted_styles[0][0] # Yoksa en yüksek olan.

        # Yeni yaklaşım: En yüksek puanı alanların listesini döndür, Gemini'ye bu listeyi ver.
        # Ama tek bir "kazanan" stil döndürmek daha kolay yönetilir.
        # Bu yüzden, eğer 2'den fazla eşit baskın stil varsa "multimodal" diyelim.
        # Eğer 1 veya 2 eşit baskın stil varsa, onlardan birini (ilkini) döndürelim.
        if len(dominant_styles) > 2:  # 3 veya daha fazla stil eşitse
            return "multimodal"
        elif dominant_styles:  # En az bir baskın stil varsa
            return dominant_styles[0]  # Eşitlik durumunda ilkini al (veya random.choice(dominant_styles))

    # Hiçbir stil belirgin değilse (çok düşük puanlar veya hepsi 0 ise)
    return random.choice(list(style_scores.keys()))  # Rastgele bir tane seç


def get_gemini_recommendations(learning_style_key):
    if not GEMINI_API_KEY:
        return ["API anahtarı yapılandırılmadığı için öneri alınamadı."]

    style_info = LEARNING_STYLES.get(learning_style_key)
    if not style_info:
        return ["Belirtilen öğrenme stili için bilgi bulunamadı."]

    style_name_for_prompt = style_info["name"].split("(")[0].strip()  # Parantez öncesi adı al
    style_keywords = style_info["keywords_for_gemini"]

    prompt = f"""
    Sen eğlenceli ve yaratıcı bir öğrenme koçusun. Kullanıcının öğrenme stili "{style_name_for_prompt}". 
    Bu stile sahip birine, öğrenme deneyimini daha etkili ve keyifli hale getirecek 5 adet özgün, eğlenceli ve uygulanabilir öneri ver.
    Öneriler şu konuları içerebilir ama bunlarla sınırlı değildir: {style_keywords}.
    Her öneri kısa, net olmalı ve başında o öneriyle ilgili çarpıcı bir emoji bulunmalı.
    Önerileri madde işaretleri (örneğin '*' veya '-') kullanarak listele.
    Örnek:
    * 🎨 Zihin haritaları ve renkli notlarla konuları görselleştirerek çalış.
    * 🎧 Ders notlarını ses kaydına alıp yürüyüş yaparken dinle.
    """

    if learning_style_key == "multimodal":
        prompt = f"""
        Sen eğlenceli ve yaratıcı bir öğrenme koçusun. Kullanıcının öğrenme stili "Çoklu Modal (Esnek Uyum Sağlayıcı)". 
        Bu, kullanıcının birden fazla öğrenme stiline (Görsel, İşitsel, Okuma/Yazma, Kinestetik, Sosyal, Yalnız, Mantıksal vb.) yatkın olduğu anlamına gelir.
        Ona, bu esnekliğini kullanarak farklı stilleri birleştirebileceği 5 adet özgün, eğlenceli ve uygulanabilir öğrenme önerisi ver.
        Her öneri kısa, net olmalı ve başında o öneriyle ilgili çarpıcı bir emoji bulunmalı.
        Önerileri madde işaretleri (örneğin '*' veya '-') kullanarak listele.
        Örnek:
        * 🧩🎬 Bir konuyu öğrenirken hem mantıksal bulmacalar çöz (Mantıksal) hem de konuyla ilgili kısa videolar izle (Görsel/İşitsel).
        * 🤝✍️ Grup çalışmalarında aktif rol alırken (Sosyal) aynı zamanda öğrendiklerini kendi cümlelerinle yazarak özetle (Okuma/Yazma).
        """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')  # veya 'gemini-pro'
        response = model.generate_content(prompt)

        recommendations_text = response.text
        recommendations_list = [
            line.strip()
            for line in recommendations_text.split('\n')
            if line.strip() and (
                        line.strip().startswith('*') or line.strip().startswith('-') or "emoji" in line.lower() or len(
                    line.split(" ")) > 2)
        ]
        # Baştaki madde işaretlerini temizleyelim
        cleaned_recommendations = [rec.lstrip('*- ').strip() for rec in recommendations_list if rec]

        return cleaned_recommendations[:5] if cleaned_recommendations else [
            "Şu an için özel bir öneri bulunamadı. 😔 Lütfen daha sonra tekrar deneyin."]
    except Exception as e:
        print(f"Gemini API Hatası: {e}")
        # Kullanıcıya daha dostane bir hata mesajı gösterelim
        error_message = f"Yapay zekadan öneri alınırken bir sorun oluştu (Hata: {type(e).__name__}). Lütfen API anahtarınızı, internet bağlantınızı kontrol edin veya bir süre sonra tekrar deneyin."
        if "API key not valid" in str(e):
            error_message = "Yapay zeka servisine bağlanırken bir sorun oluştu. Lütfen API anahtarınızın doğru olduğundan emin olun."
        elif "quota" in str(e).lower():
            error_message = "Yapay zeka servis kotası dolmuş olabilir. Lütfen daha sonra tekrar deneyin."

        return [error_message]


@app.route('/')
def index():
    # Soruları her seferinde karıştırmak için:
    # shuffled_q_items = random.sample(list(QUESTIONS.items()), len(QUESTIONS))
    # current_questions = dict(shuffled_q_items)
    # return render_template('index.html', questions=current_questions)
    return render_template('index.html', questions=QUESTIONS)


@app.route('/submit', methods=['POST'])
def submit_quiz():
    answers = request.form.to_dict()

    if not answers:
        # Eğer hiçbir cevap gelmediyse ana sayfaya yönlendir (ya da hata mesajı göster)
        return redirect(url_for('index'))

    determined_style_key = determine_learning_style(answers)
    learning_style_info = LEARNING_STYLES.get(determined_style_key,
                                              LEARNING_STYLES["multimodal"])  # Bulamazsa varsayılan

    error_message = None
    recommendations = []

    if not GEMINI_API_KEY:
        error_message = "Yapay zeka servisi şu anda aktif değil (API anahtarı eksik). Lütfen site yöneticisi ile iletişime geçin."
        # recommendations = ["API anahtarı eksik olduğu için öneri yüklenemedi."] # Bu zaten error_message'da
    else:
        recommendations = get_gemini_recommendations(determined_style_key)
        # get_gemini_recommendations zaten hata durumunda bir liste döndürüyor.
        # İlk elemanın hata içerip içermediğini kontrol edebiliriz.
        if recommendations and ("hata oluştu" in recommendations[0].lower() or "sorun oluştu" in recommendations[
            0].lower() or "api anahtarı" in recommendations[0].lower()):
            error_message = recommendations[0]
            recommendations = []  # Hata varsa öneri listesini boşalt

    return render_template('results.html',
                           learning_style_info=learning_style_info,
                           recommendations=recommendations,
                           error=error_message)


if __name__ == '__main__':
    # debug=True geliştirme aşamasında kullanışlıdır, ancak production'a geçerken False yapın.
    # host='0.0.0.0' aynı ağdaki diğer cihazlardan erişim için (dikkatli kullanın)
    app.run(debug=True, host='0.0.0.0', port=5000)