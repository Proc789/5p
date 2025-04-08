# 追關版 v1（公版 5碼/6碼風格）
from flask import Flask, render_template, request
import random
from collections import Counter

app = Flask(__name__)

history = []
mode = {
    'train': False,
    'stage': 1,
    'hit_count': 0,
    'total': 0,
    'last_prediction': [],
    'last_prediction_text': ''
}

# 對應每關投注金額
stage_bets = {
    1: 140,
    2: 275,
    3: 625,
    4: 1350,
    5: 2875,
    6: 6050
}

def get_prediction(data, stage):
    # 預測號碼邏輯：第1關用7碼，其他關用5碼
    nums = [n for round in data[-3:] for n in round]  # 近三期
    counter = Counter(nums)
    hot = [n for n, _ in counter.most_common()]
    hot_numbers = hot[:2]

    remain = [n for n in nums if n not in hot_numbers]
    counter_remain = Counter(remain)
    dynamic_pool = [n for n, _ in counter_remain.most_common()]
    dynamic_numbers = dynamic_pool[:2]

    excluded = set(hot_numbers + dynamic_numbers)
    remaining = [n for n in range(1, 11) if n not in excluded]
    extra_count = 3 if stage == 1 else 1
    extra_numbers = random.sample(remaining, extra_count) if len(remaining) >= extra_count else []

    return sorted(hot_numbers + dynamic_numbers + extra_numbers)

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
            history.clear()
            message = '訓練模式已' + ('啟用' if mode['train'] else '關閉')

        elif 'clear' in request.form:
            history.clear()
            mode.update({'stage': 1, 'hit_count': 0, 'total': 0, 'last_prediction': [], 'last_prediction_text': ''})
            message = '已清除所有紀錄'

        else:
            try:
                nums = [int(request.form.get(f'n{i}')) for i in range(1, 4)]
                nums = [10 if n == 0 else n for n in nums]  # 將0轉成10
                if all(1 <= n <= 10 for n in nums):
                    history.append(nums)

                    if len(history) >= 5:
                        prediction = get_prediction(history, stage)
                        mode['last_prediction'] = prediction
                        mode['last_prediction_text'] = f"{prediction}（目前第 {stage} 關）"

                        if mode['train']:
                            mode['total'] += 1
                            if nums[0] in prediction:
                                mode['hit_count'] += 1
                                mode['stage'] = 1
                            else:
                                mode['stage'] = min(mode['stage'] + 1, 6)
                    else:
                        message = '請先輸入至少 5 筆資料'
                else:
                    message = '請輸入 1~10 的整數'
            except:
                message = '請正確輸入三個號碼'

    return render_template('index.html',
                           history=history,
                           prediction=mode['last_prediction_text'],
                           last_prediction=mode['last_prediction'],
                           hit_count=mode['hit_count'],
                           total=mode['total'],
                           train=mode['train'],
                           stage=mode['stage'],
                           bet=bet,
                           message=message)

if __name__ == '__main__':
    app.run(debug=True)
