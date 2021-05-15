#!/usr/bin/env python3

# FinPlot: https://github.com/highfestiva/finplot
# https://doc.qt.io/qt-5/qgridlayout.html#details
import finplot as fplt
from functools import lru_cache
from PyQt5.QtWidgets import QGraphicsView, QComboBox, QLabel
from PyQt5.QtGui import QApplication, QGridLayout
from threading import Thread
import yfinance as yf

# Setup layout
app = QApplication([])
win = QGraphicsView()
win.setWindowTitle('TradingView wannabe')
layout = QGridLayout()
win.setLayout(layout)
win.showMaximized()

combo = QComboBox()
combo.setEditable(True)
[combo.addItem(i) for i in 'SPY ^AXJO GC=F GLD ^TNX BTC-USD ETH-USD XRP-USD'.split()]
layout.addWidget(combo, 0, 0, 1, 1)
info = QLabel()
layout.addWidget(info, 0, 1, 1, 1)

ax = fplt.create_plot(init_zoom_periods=100)
cross_hair_color = '#000000'
ax.crosshair = fplt.FinCrossHair(ax, color=cross_hair_color)
win.axs = [ax]  # finplot requres this property
axo = ax.overlay()
layout.addWidget(ax.vb.win, 1, 0, 1, 2)


# Data downloading
@lru_cache(maxsize=15)
def download(symbol):
    return yf.download(symbol, '2019-01-01')


@lru_cache(maxsize=100)
def get_name(symbol):
    return yf.Ticker(symbol).info['shortName']


# Plot data
plots = []


def plot(txt):
    # Get data
    df = download(txt)
    if len(df) < 20:  # symbol does not exist
        return
    info.setText('Loading symbol name...')

    # Cleanup
    ax.reset()  # remove previous plots
    axo.reset()  # remove previous plots

    # Process result
    price = df['Open Close High Low'.split()]
    volume = df['Open Close Volume'.split()]

    # Indicators
    emaShort = df.Close.ewm(span=10,min_periods=0,adjust=False,ignore_na=False).mean()
    emaMedium = df.Close.ewm(span=20,min_periods=0,adjust=False,ignore_na=False).mean()
    emaLong = df.Close.ewm(span=50,min_periods=0,adjust=False,ignore_na=False).mean()

    # Plot data
    fplt.candlestick_ochl(price)
    fplt.plot(emaShort, legend='EMA-10', color='#00FFFF', width=2)
    fplt.plot(emaMedium, legend='EMA-20', width=2)
    fplt.plot(emaLong, legend='EMA-50', color='#FF0000', width=2)
    fplt.volume_ocv(volume, ax=axo)
    fplt.refresh()  # refresh autoscaling when all plots complete
    Thread(target=lambda: info.setText(get_name(txt))).start()  # slow, so use thread

# Subscribe to changes in combo and execute function
combo.currentTextChanged.connect(plot)

# Initial plot
plot(combo.currentText())

# Show it on the screen
fplt.show(qt_exec=False)  # prepares plots when they're all setup
win.show()
app.exec_()
