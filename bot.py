import yfinance as yf
from groq import Groq
import requests
from datetime import datetime
import time
from flask import Flask
from threading import Thread
import os

# ================= الإعدادات الآمنة والنهائية =================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
TELEGRAM_BOT_TOKEN = "8678714877:AAE2v6jeeYzsNFYj_83rXK32RJEA7fszQew"
TELEGRAM_CHAT_ID = "7737655407"

# إعدادات مؤسسية تحافظ على الباقة وتضمن استقرار النظام
ALERT_THRESHOLD = 8.0 
ROUTINE_MINUTES = 60  
# ==========================================================

app = Flask(__name__)

def get_groq_client():
    if not GROQ_API_KEY:
        print("❌ خطأ: لم يتم العثور على GROQ_API_KEY")
        return None
    return Groq(api_key=GROQ_API_KEY)

@app.route('/')
def home():
    return "Gold Monitor Bot is ALIVE and running stably!"

def get_market_data():
    try:
        gold = yf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        dxy = yf.Ticker("DX-Y.NYB").history(period="1d")['Close'].iloc[-1]
        tnx = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]
        return gold, dxy, tnx
    except Exception as e:
        print(f"حدث خطأ أثناء سحب البيانات: {e}")
        return None, None, None

def generate_report(gold, dxy, tnx, is_alert=False, price_diff=0.0):
    client = get_groq_client()
    if not client:
        return None

    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_type = "[تنبيه استثنائي عاجل لحركة سعرية مفاجئة]" if is_alert else "[تقرير روتيني مفصل ومدروس]"
    alert_text = f"مقدار التغير المفاجئ المكتشف: {round(price_diff, 2)} دولار" if is_alert else ""

    prompt_lines = [
        "أنت كبير المحللين الاقتصاديين ورئيس قسم أبحاث السلع في بنك استثماري دولي.",
        f"البيانات اللحظية الحالية المستلمة في ({date_now}):",
        f"- السعر الحالي للذهب الفوري (XAU/USD): {gold:.2f} دولار.",
        f"- مؤشر الدولار الأمريكي (DXY): {dxy:.2f} نقاط.",
        f"- عوائد خزانة الولايات المتحدة لأجل 10 سنوات (US10Y): {tnx:.2f}%",
        "",
        f"نوع التقرير المطلوب: {report_type}",
        alert_text,
        "",
        "المطلوب منك صياغة تحليل مالي متعمق ومؤسسي (باللغة العربية الفصحى فقط)، مع الالتزام الصارم بالآتي:",
        "1. التحليل المالي: اشرح حركة الذهب بناءً على 'قانون الارتباط العكسي الرياضي' مع مؤشر DXY، وتأثير 'تكلفة الفرصة البديلة المستندة إلى عوائد السندات'.",
        "2. الأرقام والمستويات: حدد الدعوم والمقاومات اللحظية القريبة بناءً على النطاق السعري الفعلي لليوم (بفارق يتراوح بين 10 إلى 30 دولار).",
        "3. البلاغة وعدم التكرار: يُمنع التكرار اللفظي. استخدم مفردات مالية متنوعة واجعل الصياغة طبيعية واحترافية.",
        "4. السيناريوهات للمستثمر الفيزيكال: صغ سيناريوهات واضحة للمستثمرين الذين يشترون الذهب الفعلي بأسعار الشاشة اللحظية ويستلمونه يداً بيد.",
        "5. شجرة السيناريوهات: يُمنع استخدام الأكواد. ارسم 'شجرة سيناريوهات نصية' تناسب تليجرام باستخدام الرموز:",
        "📈 سيناريو الصعود: [الشرح والهدف 🎯]",
        "📉 سيناريو الهبوط: [الشرح والهدف 🎯]",
        "",
        "6. إخلاء المسؤولية الإلزامي: أضف النص التالي في النهاية:",
        "⚠️ إخلاء مسؤولية: الأسعار الواردة هي حقيقية لحظة إصداره. التحليلات هي نتاج ذكاء اصطناعي تُقدم كأداة مساعدة وليست توصية مالية حتمية."
    ]
    prompt = "\n".join(prompt_lines)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "أنت محلل مالي أكاديمي."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"⚠️ تنبيه صامت: تم الوصول للحد الأقصى أو حدث خطأ بالسيرفر: {e}")
        return None

def send_to_telegram(message):
    protocol = "https://"
    domain = "api.telegram.org"
    url = f"{protocol}{domain}/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] تم إرسال التقرير بنجاح لتليجرام.")
    except Exception as e:
        print(f"خطأ في الإرسال لتليجرام: {e}")

def run_bot():
    print("البوت بدأ العمل بنظام المراقبة المؤسسي الآمن...")
    last_gold_price = None
    minutes_counter = 0
    
    while True:
        current_gold, current_dxy, current_tnx = get_market_data()
        if current_gold and current_dxy and current_tnx:
            if last_gold_price is None:
                print("إرسال التقرير الافتتاحي الأول...")
                last_gold_price = current_gold
                report = generate_report(current_gold, current_dxy, current_tnx, is_alert=False)
                if report:
                    send_to_telegram(report)
                minutes_counter = 0
            
            price_difference = current_gold - last_gold_price
            if abs(price_difference) >= ALERT_THRESHOLD:
                print(f"🚨 استثناء عاجل! تحرك السعر بمقدار {price_difference:.2f} دولار. جاري التحديث...")
                report = generate_report(current_gold, current_dxy, current_tnx, is_alert=True, price_diff=price_difference)
                if report:
                    send_to_telegram(report)
                    last_gold_price = current_gold 
                    minutes_counter = 0 
            
            elif minutes_counter >= ROUTINE_MINUTES:
                print(f"مرت {ROUTINE_MINUTES} دقيقة.. إرسال التقرير الروتيني المحدث...")
                report = generate_report(current_gold, current_dxy, current_tnx, is_alert=False)
                if report:
                    send_to_telegram(report)
                    last_gold_price = current_gold 
                    minutes_counter = 0 
        else:
            print("لم يتم العثور على بيانات في هذه الدورة. سيتم المحاولة مجدداً.")
            
        time.sleep(60)
        minutes_counter += 1

if __name__ == "__main__":
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
