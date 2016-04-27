#!/bin/sh

pyside-uic -o JogWidget/jogWidget_ui.py JogWidget/jogWidget_expand.ui
pyside-uic -o pyFileList/filelist_ui.py pyFileList/filelist_expand.ui
pyside-uic -o RunWidget/runWidget_ui.py RunWidget/runWidget_expand.ui
pyside-uic -o splash_ui.py splash_expand.ui

