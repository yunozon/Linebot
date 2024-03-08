@echo off
rem flaskでapp.py以外のファイルを実行する場合は環境変数の設定が必要
rem 今回はすでに書き換わっている危険性があるため、appでも設定しておく
set FLASK_APP=app
rem デスクトップのsrcフォルダに移動
cd c:\Users\g10031929\OneDrive - Ricoh\Desktop\src
rem ngrokを起動
start ngrok http 8080
rem venvでflaskを起動する
call .venv\Scripts\activate.bat
flask run --reload --port 8080
pause
