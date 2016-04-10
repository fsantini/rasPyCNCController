#!/bin/sh

pyside-uic -o JogWidget/jogWidget_ui.py JogWidget/jogWidget.ui
pyside-uic -o pyFileList/filelist_ui.py pyFileList/filelist.ui
pyside-uic -o RunWidget/runWidget_ui.py RunWidget/runWidget.ui
pyside-uic -o splash_ui.py splash.ui

