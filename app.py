# 多碼數預測器（穩定修正版）- 含 4~7 碼、節奏判定、命中統計完整修正
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
rhythm_history = []
rhythm_state = "未知"

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
  <form method='POST'>
    <div style='text-align: left; padding: 10px;'>
      <strong>下注紀錄：</strong><br>
      {% for i in range(1,6) %}
        <label>
          <input type='checkbox' name='stage{{i}}' {% if 'stage' + str(i) in marked_stages %}checked{% endif %}>
          第{{i}}關 注碼：<input name='bet{{i}}' value='{{ bets.get("bet" + str(i), "") }}' style='width: 60px;'>
        </label><br>
      {% endfor %}
    </div>
    <button type='submit'>儲存注碼</button>
  </form>
  {% if prediction %}<div><strong>本期預測號碼：</strong> {{ prediction }}</div>{% endif %}
  {% if last_prediction %}
    <div><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
    <div style='color: {{ "green" if last_hit_status else "red" }};'>{{ '✅ 命中！' if last_hit_status else '❌ 未命中' }}</div>
  {% endif %}
  {% if last_champion_zone %}<div>冠軍號碼開在：{{ last_champion_zone }}</div>{% endif %}
  <div>熱號節奏狀態：{{ rhythm_state }}</div>
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

# 以下 predict 和 index 等邏輯不變...（保留原本程式碼）
