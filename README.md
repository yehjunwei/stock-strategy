# stock-strategy

## Study resources
- pandas 教學: https://leemeng.tw/practical-pandas-tutorial-for-aspiring-data-scientists.html
- Pandas_ta 教學: https://blog.csdn.net/ndhtou222/article/details/132157873
- 用python實作買賣指標: https://python.plainenglish.io/generating-buy-sell-trade-signals-in-python-1153b1a543c4
- Finmind: https://finmind.github.io/
- Finmind策略分析: https://finmindtrade.com/analysis/#/dashboards/strategy-analysis

## Strategy 01
```bash
pip install yfinance pandas pandas_ta numpy seaborn setuptools
python strategy01.py
```

## FinMind
```bash
pip install finmind
python finmind.py
```

## Python issues
```bash
# install python on macos using homebrew
❯ brew install python

# can't use python or pip
❯ which python3
/opt/homebrew/bin/python3
❯ python
zsh: command not found: python

❯ which pip3
/opt/homebrew/bin/pip3
❯ pip
zsh: command not found: pip

# make symbolic links
❯ sudo ln -s /opt/homebrew/bin/python3 /usr/local/bin/python
❯ sudo ln -s /opt/homebrew/bin/pip3 /usr/local/bin/pip
```
### install venv
```bash
# create venv
python -m venv myenv

# activate venv
source myenv/bin/activate

# deactivate
deactivate
```
