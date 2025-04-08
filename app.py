# 追關版 v1 - 套用公版 UI + 7碼首關 + 5碼追關邏輯（支援輸入0自動轉10）
from flask import Flask, render_template, request
import random
from collections import Counter

app = Flask(__name__)

history = []
mode = {'train': False, 'stage': 1, 'hit_count': 0, 'total': 0, 'last_prediction': []}

# 對應每關投注金額（可依表調整）
stage_bets = {
    1: 140,
    2: 275,
    3: 625,
    4: 1350,
    5: 2875,
    6: 6050
}

# 熱號：最近三期所有號碼中出現最多的前2碼
# 動熱：排除熱號後，取最多的前2碼（7碼取2，5碼也取2）
# 補碼：從1~10中排除前述號碼後隨機取（7碼取3，5碼取1）
def get_prediction(data, stage):
    numbers = [n for round in data[-3:] for n in round]  # 近三期所有號碼
    counter = Counter(numbers)
    hot = [n for n, _ in counter.most_common()]

    hot_numbers = hot[:2]
    remain = [n for n in numbers if n not in hot_numbers]
    counter_remain = Counter(remain)
    dynamic_pool = [n for n, _ in counter_remain.most_common()]
    dynamic_numbers = dynamic_pool[:2]

    excluded = set(hot_numbers + dynamic_numbers)
    remaining_numbers = [n for n in range(1, 11) if n not in excluded]
    extra_count = 3 if stage == 1 else 1
    extra_numbers = random.sample(remaining_numbers, extra_count) if len(remaining_numbers) >= extra_count else []

    prediction = sorted(hot_numbers + dynamic_numbers + extra_numbers)
    return prediction

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    prediction = []
    stage = mode['stage']
    bet = stage_bets.get(stage, '-')

    if request.method == 'POST':
        if 'toggle_train' in request.form:
            mode['train'] = not mode['train']
            mode['hit_count'] = 0
            mode['total'] = 0
            mode['stage'] = 1
            message = '訓練模式已' + ('啟用' if mode['train'] else '關閉')

        elif 'clear' in request.form:
            history.clear()
            mode.update({'stage': 1, 'hit_count': 0, 'total': 0, 'last_prediction': []})
            message = '已清除所有紀錄'

        else:
            try:
                nums = [int(request.form.get(f'n{i}')) for i in range(1, 4)]
                nums = [10 if n == 0 else n for n in nums]  # 將0轉為10

                if all(1 <= n <= 10 for n in nums):
                    history.append(nums)

                    if len(history) >= 5:
                        prediction = get_prediction(history, stage)
                        mode['last_prediction'] = prediction

                        # 命中判定（是否包含冠軍號）
                        if mode['train']:
                            mode['total'] += 1
                            if nums[0] in prediction:
                                mode['hit_count'] += 1
                                mode['stage'] = 1  # 命中回第一關
                            else:
                                mode['stage'] = min(mode['stage'] + 1, 6)
                    else:
                        message = '請先輸入至少 5 筆資料'
                else:
                    message = '請輸入 1~10 之間的數字'
            except:
                message = '請正確輸入三個號碼'

    return render_template('index.html', 
                           history=history,
                           prediction=mode['last_prediction'],
                           hit_count=mode['hit_count'],
                           total=mode['total'],
                           train=mode['train'],
                           stage=mode['stage'],
                           bet=bet,
                           message=message)

if __name__ == '__main__':
    app.run(debug=True)
