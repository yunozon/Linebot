@echo off
rem pipenvでpython実行環境を構築する
pip uninstall pipenv
pip install pipenv
pipenv --python 3.9
pipenv update --dev
pause