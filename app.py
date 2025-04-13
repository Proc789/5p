# 多碼數預測器（修正版）- 使用 6碼追關版命中邏輯
from flask import Flask, render_template_string, request, redirect, session
import random
from collections import Counter

app = Flask(__name__)
app.secret_key = 'secret-key'

history = []
predictions = []
sources = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
last_champion_zone = ""

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>多碼數預測器</title>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>預測器</h2>
  <form method='POST'>
    <label><input type='radio' name='mode' value='4' {{ 'checked' if mode == '4' else '' }}> 4碼</label>
    <label><input type='radio' name='mode' value='5' {{ 'checked' if mode == '5' else '' }}> 5碼</label>
    <label><input type='radio' name='mode' value='6' {{ 'checked' if mode == '6' else '' }}> 6碼</label>
    <label><input type='radio' name='mode' value='7' {{ 'checked' if mode == '7' else '' }}> 7碼</label><br><br>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode='numeric'><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode='numeric'><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode='numeric'><br><br>
    <button type='submit'>提交並預測</button>
  </form>
  <form method='GET' action='/reset'>
    <button type='submit' style='margin-top: 10px;'>清除所有資料</button>
  </form>
  <br>
  {% if prediction %}<div><strong>本期預測號碼：</strong> {{ prediction }}</div>{% endif %}
  {% if last_prediction %}
    <div><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
    <div style='color: {{ "green" if last_hit_status else "red" }};'>{{ '✅ 命中！' if last_hit_status else '❌ 未命中' }}</div>
  {% endif %}
  {% if last_champion_zone %}<div>冠軍號碼開在：{{ last_champion_zone }}</div>{% endif %}
  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數：{{ all_hits }} / {{ total_tests }}<br>
    熱號命中次數：{{ hot_hits }}<br>
    動熱命中次數：{{ dynamic_hits }}<br>
    補碼命中次數：{{ extra_hits }}<br>
  </div>
  {% if history %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>{% for row in history[-10:] %}<li>{{ row }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
<script>
function moveToNext(current, nextId) {
  setTimeout(() => {
    if (current.value === '0') current.value = '10';
    let val = parseInt(current.value);
    if (!isNaN(val) && val >= 1 && val <= 10) {
      document.getElementById(nextId).focus();
    }
  }, 100);
}
</script>
</body>
</html>
"""

def weighted_hot(flat, recent):
    score = {}
    for i, group in enumerate(reversed(recent)):
        for num in group:
            score[num] = score.get(num, 0) + (3 - i)
    return sorted(score, key=lambda x: (-score[x], -flat[::-1].index(x)))

def predict(mode):
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    hot = weighted_hot(flat, recent)[:2]
    dynamic_pool = [n for n in flat if n not in hot]
    dynamic_freq = Counter(dynamic_pool)
    dynamic = sorted(dynamic_freq, key=lambda x: (-dynamic_freq[x], -flat[::-1].index(x)))[:2]
    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    if mode == '4':
        result = hot[:2] + dynamic[:1] + pool[:1]
    elif mode == '5':
        result = hot[:2] + dynamic[:2] + pool[:1]
    elif mode == '6':
        result = hot[:2] + dynamic[:2] + pool[:2]
    elif mode == '7':
        result = hot[:2] + dynamic[:2] + pool[:3]
    else:
        result = hot + dynamic + pool[:1]
    while len(result) < int(mode):
        extra = [n for n in range(1, 11) if n not in result]
        random.shuffle(extra)
        result += extra[:int(mode) - len(result)]
    sources.append({'hot': hot, 'dynamic': dynamic, 'extra': pool})
    return sorted(list(dict.fromkeys(result)))

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, last_champion_zone
    prediction = None
    mode = session.get('mode', '6')

    if request.method == 'POST':
        mode = request.form.get('mode', '6')
        session['mode'] = mode

        first = int(request.form['first'])
        if first == 0: first = 10
        second = int(request.form['second'])
        if second == 0: second = 10
        third = int(request.form['third'])
        if third == 0: third = 10
        current = [first, second, third]
        history.append(current)

        last_prediction = predictions[-1] if predictions else []
        last_hit_status = current[0] in last_prediction

        if predictions:
            champ = current[0]
            src = sources[-1]
            if champ in src['hot']:
                hot_hits += 1
                last_champion_zone = "熱號區"
                all_hits += 1
            elif champ in src['dynamic']:
                dynamic_hits += 1
                last_champion_zone = "動熱區"
                all_hits += 1
            elif champ in src['extra']:
                extra_hits += 1
                last_champion_zone = "補碼區"
                all_hits += 1
            else:
                last_champion_zone = "未命中"
        total_tests += 1

        prediction = predict(mode)
        predictions.append(prediction)
    else:
        last_prediction = predictions[-1] if predictions else []
        last_hit_status = False

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        last_hit_status=last_hit_status,
        last_champion_zone=last_champion_zone,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        history=history,
        mode=mode)

@app.route('/reset')
def reset():
    global history, predictions, sources, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, last_champion_zone
    history.clear()
    predictions.clear()
    sources.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    last_champion_zone = ""
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
