from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ButtonsTemplate,
)

import random
import configparser
import os
import datetime
import json

# 各クライアントライブラリのインスタンス作成
# 必要な設定情報を別ファイルから読み込む
conf = configparser.ConfigParser()
conf.read(os.getcwd() + '/setting.conf')
line_bot_api = LineBotApi(conf.get('linebot_credentials', 'channel_access_token'))
handler = WebhookHandler(conf.get('linebot_credentials', 'channel_secret'))

app = Flask(__name__)

# ゴミ出しの日のマップ(key:曜日、value:ごみの種類)
garbage_map = {
    '月曜日': '',
    '火曜日': '燃えるごみ',
    '水曜日': 'プラスチックごみ',
    '木曜日': 'びん缶ペットボトル',
    '金曜日': '燃えるごみ',
    '土曜日': '',
    '日曜日': '',
}

# 曜日の定義リスト
week_list = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

# ごみのリスト
garbage_list = ['燃えるごみ', 'もえるごみ','燃えるゴミ','プラスチックごみ', 'プラスチックゴミ', 'びん缶ペットボトル', '瓶缶ペットボトル']

# 対話がどこまで進んだかを示すコンテキスト用の定数群
# メニュー選択(曜日or日程orカレンダー)を待つ状態
WAITING_FOR_MENU_IN = '0'
# 捨てたいごみの種類(燃えるゴミorプラスチックごみorびん缶ペット)を待つ状態
WAITING_FOR_GARBAGE_TYPE_IN = '1'
# 捨てたいごみの期間(○○日)を待つ状態
WAITING_FOR_TERM_IN = '2'

# いつの日付を参照するかを決定する用の定数群
YEAR = 2023
MONTH = 9

# 対話用の管理ステータス
class Status:
    # コンストラクタ(初期化)
    def __init__(self):
        # 対話がどこまで進んだかを保持するための変数、初期状態はメニュー選択を待つ状態
        self.context = WAITING_FOR_MENU_IN

    # ステータスのコンテキストを取得
    def get_context(self):
        return self.context

    # ステータスのコンテキストを設定
    def set_context(self, context):
        self.context = context


# ユーザー毎のセッション情報
# 2ターン以上の会話をする場合に用いる
class MySession:
    _status_map = dict()

    # セッション情報を新規に登録
    def register(user_id):
        if MySession._get_status(user_id) is None:
            MySession._put_status(user_id, Status())

    # セッション情報からユーザーの管理ステータスを取得
    def _get_status(user_id):
        return MySession._status_map.get(user_id)

    # セッション情報にユーザーの管理ステータスを設定
    def _put_status(user_id, status: Status):
        MySession._status_map[user_id] = status

    # セッション情報からユーザーの管理ステータスのコンテキストを取得
    def read_context(user_id):
        return MySession._status_map.get(user_id).get_context()

    # セッション情報にユーザーの管理ステータスのコンテキストを更新
    def update_context(user_id, context):
        new_status = MySession._status_map.get(user_id)
        new_status.set_context(context)
        MySession._status_map[user_id] = new_status


# flaskの動作確認
# http://IP/ でHelloが表示されるかを確認
@app.route('/')
def say_hello():
    return 'Hello'

# callbackは呪文でOK
# LINE側にこういうラインボットがあるよ～と知らせる処理
@app.route('/callback', methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)

    # handle webhook body
    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('Invalid signature. Please check your channel access token/channel secret.')
        abort(400)

    # ここの戻り値はなんでもよい
    return 'OK'

# メッセージを受け取った後にどんな処理をしてどんなリプライするか
# TextMessageの他にもImageMessage(画像)などがある
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # メッセージを送信したユーザー
    user_id = event.source.user_id
    # ユーザーの発言
    text = event.message.text
    # ユーザーのセッションを作成
    MySession.register(user_id)

    """
    実装開始！！
    ここから
    """

    # ヘルプ、指定した文字以外を入力したときに表示するテキスト内容
    text_help = '''\
このようにしてください！
カレンダーを表示したければ、
メニューの「カレンダ」ーをタップ
今日のごみ収集の種類が知りたければ、メニューの「今日」をタップ
明日のごみ収集の種類が知りたければ、メニューの「明日」をタップ
「燃えるごみ」「プラスチックごみ」「びん缶ペットボトル」の
どれかを入力すると、対応する曜日を教えます
'''

    #　機能1 
    # 燃えるごみ、プラスチックごみ、びん缶ペットボトルのどれかを入力すると、曜日を教える
    if text in garbage_list:
        if text == garbage_list[1] or text == garbage_list[2]:
            text = garbage_list[0]
        elif text == garbage_list[4]:
            text = garbage_list[3]
        elif text == garbage_list[6]:
            text = garbage_list[5]
        garbage_text = get_day_by_type(text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=garbage_text + 'です'
            )
        ) 
    # 機能2 
    # 日付を入力(リッチメニューからタップ)すると、日付に対応したごみの種類を表示
    elif text == '今日' or text == '明日' or text[-1] == '日':
        garbage_text = get_type_by_day(text)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text= garbage_text + "です"
            )
        )
    #　機能3 : 'カレンダー'と入力したら、カレンダーが出力
    elif text == 'カレンダー':
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url="https://lh3.googleusercontent.com/pw/AIL4fc-maDzKU9dHw_KHoCHSXkirKPhZfPbON-6K1Ji61cIhHtg0FUZYPqnGQ6MkkhoByAqGEc5nwMtv5yWLnbOiM6pK7fmDQpcu5OnpN1V-9IxlGyEw4V5BC7uDgkrWEQMjqNY3AkgoRG80RMftfoiyi-4=w884-h1249-s-no?authuser=0",
                preview_image_url = "https://lh3.googleusercontent.com/pw/AIL4fc-maDzKU9dHw_KHoCHSXkirKPhZfPbON-6K1Ji61cIhHtg0FUZYPqnGQ6MkkhoByAqGEc5nwMtv5yWLnbOiM6pK7fmDQpcu5OnpN1V-9IxlGyEw4V5BC7uDgkrWEQMjqNY3AkgoRG80RMftfoiyi-4=w884-h1249-s-no?authuser=0"
            )
        )

    # 指定していない文字を入力すると、ヘルプの説明が出る
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(
                text=text_help
            )
        )

    """
    実装終了！！
    ここまで
    """
# カレンダーと照らし合わせる(分別ごみ→曜日)
def get_day_by_type(text):
    day_list = []
    for key, value in garbage_map.items():
        if(value == text):
            day_list.append(key)
    text = ','.join(day_list)

    return text

# カレンダーと照らし合わせる(日程→分別)
def get_type_by_day(text):
    # 今日、明日、昨日
    if text == '今日':
        dt = datetime.datetime.now()
    elif text == '明日':
        dt = datetime.datetime.now() + datetime.timedelta(days = 1)

    # ○○日
    elif text[-1] == '日':
        try:
            day = int(text[:-1])
            dt = datetime.datetime(year = YEAR, month = MONTH, day = day)
        except ValueError:
            return '例)1日, 15日, 30日というように入力してください'


    # 日付から曜日取得
    week = dt.weekday()
    # 曜日からごみの種類取得
    type = garbage_map[week_list[week]]
    text = type if type != '' else '収集はない'
    return text

# このアプリを実行する
if __name__ == '__main__':
    app.run()