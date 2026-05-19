import yfinance as yf
from groq import Groq
import requests
from datetime import datetime
import time
from flask import Flask
from threading import Thread
import os

# ================= الإعدادات الآمنة =================
# تم تعديل هذا السطر ليسحب المفتاح من خزنة ريندر السرية لحمايتك من الحظر
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 

TELEGRAM_BOT_TOKEN = "8678714877:AAE2v6jeeYzsNFYj_83rXK32RJEA7fszQew"
TELEGRAM_CHAT_ID = "7737655407"
ALERT_THRESHOLD = 5.0 
# ===================================================

app = Flask(__name__)

# دالة للتحقق من أن المفتاح تم سحبه بنجاح قبل تشغيل العميل
def get_groq_client():
    if not GROQ_API_KEY:
        print("❌ خطأ حرج: لم يتم العثور على GROQ_API_KEY في إعدادات البيئة (Environment Variables)!")
        return None
    return Groq(api_key=GROQ_API_KEY)

# صفحة ويب بسيطة عشان UptimeRobot يزورها والسيرفر يفضل صاحي
@app.route('/')
def home():
    return "Gold Monitor Bot is ALIVE and running!"

def get_market_data():
    try:
        # هنا تركنا مكتبة yfinance تتعامل تلقائياً بدون Session يدوي بناءً على التحديث الأخير منعاً للأخطاء
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
        return "حدث خطأ: مفتاح API الخاص بـ Groq غير مضبوط في السيرفر."

    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
    أنت كبير المحللين الاقتصاديين ورئيس قسم أبحاث السلع في بنك استثماري دولي.
    البيانات اللحظية الحالية المستلمة في ({date_now}):
    - السعر الحالي للذهب الفوري (XAU/USD): {gold:.2f} دولار.
    - مؤشر الدولار الأمريكي (DXY): {dxy:.2f} نقاط.
    - عوائد خزانة الولايات المتحدة لأجل 10 سنوات (US10Y): {tnx:.2f}%

    نوع التقرير المطلوب: {"[تنبيه استثنائي عاجل لحركة سعرية مفاجئة]" if is_alert else "[تقرير روتيني مفصل ومدروس]"}
    {"مقدار التغير المفاجئ المكتشف: " + str(round(price_diff, 2)) + " دولار" if is_alert else ""}

    المطلوب منك صياغة تحليل مالي متعمق ومؤسسي (باللغة العربية الفصحى فقط)، مع الالتزام الصارم بالآتي:
    1. التحليل المالي: اشرح حركة الذهب بناءً على "قانون الارتباط العكسي الرياضي" مع مؤشر DXY، وتأثير "تكلفة الفرصة البديلة المستندة إلى عوائد السندات".
    2. الأرقام والمستويات: حدد الدعوم والمقاومات اللحظية القريبة بناءً على النطاق السعري الفعلي لليوم (بفارق يتراوح بين 10 إلى 30 دولار).
    3. البلاغة وعدم التكرار: يُمنع التكرار اللفظي (مثل تكرار جملة "نلاحظ أن"). استخدم مفردات مالية متنوعة واجعل الصياغة طبيعية واحترافية.
    4. السيناريوهات للمستثمر الفيزيكال: صغ سيناريوهات واضحة للمستثمرين الذين يشترون الذهب الفعلي (فيزيكال) بأسعار الشاشة اللحظية ويستلمونه يداً بيد.
    5. شجرة السين
