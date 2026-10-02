# QuarkFX Forex Economic Calendar

Forex Factory और Myfxbook से Forex Economic Calendar स्क्रैप करने और हर 5 मिनट पर अपडेट करने का ऑटोमेटेड टूल।

## 📁 4 आउटपुट JSON फाइलें (Output Files)

स्क्रैपर रन होने पर `output/` डायरेक्टरी में 4 फाइलें बनती हैं:
1. `output/forexfactory_thisweek.json` - Forex Factory (This Week Calendar)
2. `output/forexfactory_21days.json` - Forex Factory (21 Days / 3 Weeks Calendar)
3. `output/myfxbook_thisweek.json` - Myfxbook (This Week Calendar)
4. `output/myfxbook_21days.json` - Myfxbook (21 Days / 3 Weeks Calendar)

---

## 🌐 4 API एंडपॉइंट्स (URLs)

`python server.py` चलाने पर पोर्ट 5000 पर 4 URLs उपलब्ध होते हैं:
1. `http://localhost:5000/api/forexfactory/thisweek` (या `/forexfactory_thisweek.json`)
2. `http://localhost:5000/api/forexfactory/21days` (या `/forexfactory_21days.json`)
3. `http://localhost:5000/api/myfxbook/thisweek` (या `/myfxbook_thisweek.json`)
4. `http://localhost:5000/api/myfxbook/21days` (या `/myfxbook_21days.json`)

---

## ⏱️ क्रोन जॉब (Cron Job - Every 5 Minutes)

### विकल्प 1: लोकल रनर (Local Python Cron Runner)
```bash
python cron_runner.py
```
यह तुरंत स्क्रैप करेगा और फिर हर 5 मिनट (300 सेकंड) पर ऑटोमैटिकली 4 फाइलों को अपडेट करता रहेगा।

### विकल्प 2: GitHub Actions (Cloud Cron)
`.github/workflows/scrape_cron.yml` फाइल रेपो में पहले से कॉन्फ़िगर है:
```yaml
schedule:
  - cron: '*/5 * * * *'
```
रेपो को GitHub पर पुश करते ही यह हर 5 मिनट पर ऑटोमैटिक रन होकर चारों फाइलों को कमिट कर देगा।

---

## 🚀 इंस्टॉलेशन और इस्तेमाल (Setup & Usage)

1. **निर्भरताएँ इंस्टॉल करें:**
   ```bash
   pip install -r requirements.txt
   ```

2. **एक बार स्क्रैपर चलाकर 4 फाइलें जनरेट करें:**
   ```bash
   python scraper.py
   ```

3. **5 मिनट के क्रोन जॉब लूप में चलाने के लिए:**
   ```bash
   python cron_runner.py
   ```

4. **API सर्वर चालू करने के लिए:**
   ```bash
   python server.py
   ```
