from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, MessageAction,TemplateSendMessage, 
    ButtonsTemplate, QuickReplyButton, QuickReply, FlexSendMessage, FollowEvent

)

import configparser
import os
import json

conf = configparser.ConfigParser()
conf.read(os.getcwd() + '/setting.conf')

# 各クライアントライブラリのインスタンス作成
# ソースコード配布のため、必要な設定情報はファイルに外出し
line_bot_api = LineBotApi(conf.get('linebot_credentials', 'channel_access_token'))
handler = WebhookHandler(conf.get('linebot_credentials', 'channel_secret'))

app = Flask(__name__)

# flaskの動作確認
# http://IP/ でHelloが表示されるかを確認
@app.route("/")
def say_hello():
    return "Hello"


# callbackは呪文でOK
# LINE側にこういうラインボットがあるよ～と知らせる処理
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# メッセージを受け取った後にどんな処理をしてどんなリプライするか
# TextMessageの他にもImageMessage(画像)などがある
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == 'ただいま':
        event.message.text = 'おかえり'
    elif event.message.text == 'いってきます':
        event.message.text = 'いってらっしゃい'
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


# ユーザー情報を取得した上で使用する「〇〇さん、こんにちは！」
@handler.add(MessageEvent, message=TextMessage)
def response_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)

    text = event.message.text

    

    status_msg = profile.status_message
    if status_msg != "None":
        # LINEに登録されているstatus_messageが空の場合は、"なし"という文字列を代わりの値とする
        status_msg = "なし"

    if event.message.text == 'プロフィール' :
        

        messages = TemplateSendMessage(alt_text="Buttons template",
                                        template=ButtonsTemplate(
                                            thumbnail_image_url=profile.picture_url,
                                            title=profile.display_name,
                                            text=f"User Id{profile.user_id[:5]}...\n"
                                                f"Status Message: {status_msg}",
                                            actions=[MessageAction(label="自己紹介", text=f"{profile.display_name} さん、こんにちは！")]))

        line_bot_api.reply_message(event.reply_token, messages=messages)
    
    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))
    # 試し
    if text == 'じゃんけん' :
        with open('./janken.json', encoding="utf-8_sig") as f:
            janken = json.load(f)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text='最初はぐー', contents=janken)
        )
        

# クイックリプライ
# @handler.add(MessageEvent, message=TextMessage)
# def response_message(event):
#     if event.message.text == "言語":
#         language_list = ["Ruby", "Python", "PHP", "Java", "C"]

#         items = [QuickReplyButton(action=MessageAction(label=f"{language}", text=f"{language}が好き")) for language in language_list]

#         messages = TextSendMessage(text="どの言語が好きですか？",
#                 quick_reply=QuickReply(items=items))
        
#         line_bot_api.reply_message(event.reply_token, messages=messages)

@handler.add(MessageEvent, message=TextMessage)
def default(event):
    with open('./icon.json') as f:
        saisyohaguu_message = json.load(f)
    line_bot_api.reply_message(
        event.reply_token,
    )

if __name__ == "__main__":
    app.run()