# WhatsApp Wound Care & Diabetic Foot Bot 🦶💬

بوت واتساب بالذكاء الاصطناعي بيجاوب أسئلة العناية بالجروح والقدم السكري — عربي/إنجليزي، للمرضى والأطباء.
An AI WhatsApp bot answering wound-care & diabetic-foot questions — bilingual, for patients and clinicians.

**كل الأدوات مجانية للتجربة** | All tools are free to start:
- **Groq** — الذكاء الاصطناعي (مجاني، من غير كارت) / free LLM, no credit card
- **Twilio WhatsApp Sandbox** — قناة الواتساب (مجانية للتجربة) / free WhatsApp test channel
- **ngrok** — يوصّل السيرفر بتاعك بالنت (مجاني) / free tunnel

---

## الملفات | Files
| File | إيه ده |
|------|--------|
| `app.py` | السيرفر الرئيسي (Flask webhook + Groq) |
| `system_prompt.py` | "عقل" البوت وقواعد الأمان الطبية — عدّل هنا |
| `test_bot.py` | تجربة الردود في التيرمينال قبل الواتساب |
| `requirements.txt` | المكتبات |
| `.env.example` | نموذج المفاتيح |

---

## الخطوات | Step by step

### 1) ثبّت Python والمكتبات
تأكد عندك Python 3.9+ ، وبعدين:
```bash
pip install -r requirements.txt
```

### 2) هات مفتاح Groq (مجاني)
1. ادخل https://console.groq.com/keys
2. اعمل حساب واضغط **Create API Key** وانسخه.
3. اعمل نسخة من `.env.example` باسم `.env` وحط المفتاح:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
```

### 3) جرّب "عقل" البوت محلياً (من غير واتساب)
```bash
python test_bot.py
```
اكتب أي سؤال، مثلاً: *"إيه الفرق بين Wagner grade 2 و 3؟"* أو *"مريض عنده قرحة في القدم، أعمل إيه؟"*
لو الردود عاجباك، كمّل للواتساب.

### 4) شغّل السيرفر
```bash
python app.py
```
هيشتغل على `http://localhost:5000`.

### 5) وصّله بالنت بـ ngrok
- نزّل ngrok من https://ngrok.com/download واعمل حساب مجاني.
- في تيرمينال تاني:
```bash
ngrok http 5000
```
- هيديك رابط زي `https://xxxx.ngrok-free.app` — انسخه.

### 6) فعّل Twilio WhatsApp Sandbox
1. اعمل حساب مجاني: https://www.twilio.com/try-twilio
2. من الـ Console افتح: **Messaging → Try it out → Send a WhatsApp message**.
3. هتلاقي رقم الساندبوكس وكود انضمام زي `join something-word`.
4. ابعت الكود ده من واتسابك للرقم ده عشان تنضم.
5. في نفس الصفحة (Sandbox settings) في خانة **"When a message comes in"**:
   - حط: `https://xxxx.ngrok-free.app/whatsapp`
   - Method: **POST** → **Save**.

### 7) جرّب! 🎉
ابعت رسالة على واتساب لرقم الساندبوكس، مثلاً:
- *"عندي جرح مش بيلتئم، أعمل إيه؟"*
- *"What dressing for a heavily exudating wound?"*

البوت هيرد عليك بنفس اللغة.
اكتب **reset** أو **مسح** في أي وقت لبدء محادثة جديدة.

---

## نشر دائم (اختياري) | Deploy for free
عشان يفضل شغّال من غير جهازك، انشره على **Render** (خطة مجانية):
1. ارفع المشروع على GitHub.
2. https://render.com → New → Web Service → اربط الريبو.
3. Build: `pip install -r requirements.txt` — Start: `gunicorn app:app`
   (زوّد `gunicorn` في requirements.txt).
4. ضيف `GROQ_API_KEY` في Environment Variables.
5. خد رابط Render وحطه في Twilio بدل رابط ngrok.

---

## ⚠️ ملاحظة طبية وقانونية | Medical & legal note
- البوت **للتثقيف الطبي** فقط — مش بديل عن الفحص أو التشخيص أو الوصفة.
- البرومبت فيه قواعد أمان (بيحوّل الحالات الخطيرة للطوارئ، وما بيديش جرعات دوائية شخصية).
- Twilio Sandbox للتجربة فقط؛ لواتساب رسمي (WhatsApp Business API) محتاج موافقة ورقم موثّق.
- لو هتستخدمه مع مرضى حقيقيين، راجع متطلبات خصوصية البيانات الطبية في بلدك.

## تغيير الموديل | Change the model
عدّل `GROQ_MODEL` في `.env`. موديلات Groq المجانية بتتغير — شوف القائمة على
https://console.groq.com/docs/models
