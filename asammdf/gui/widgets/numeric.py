# -*- coding: utf-8 -*-
from pathlib import Path

HERE = Path(__file__).resolve().parent

from ..ui import resource_qt5 as resource_rc

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
from natsort import natsorted
from numpy import zeros, searchsorted

from ..utils import COLORS

class Numeric(QtWidgets.QWidget):
    add_channel_request = QtCore.pyqtSignal(str)

    def __init__(self, signals, *args, **kwargs):
        super().__init__()
        self.signals = []
        self._min = self._max = 0
        self.format = 'phys'
        uic.loadUi(HERE.joinpath("..", "ui", "numeric.ui"), self)

        self.timestamp.valueChanged.connect(self._timestamp_changed)
        self.timestamp_slider.valueChanged.connect(self._timestamp_slider_changed)

        self._update_values(self.timestamp.value())
        self.channels.add_channel_request.connect(self.add_channel_request)

        self.add_signals(signals)

    def add_signals(self, signals):
        self.signals = natsorted(signals, key=lambda x: x.name)
        self.channels.clear()
        self._min = self._max = 0
        items = []
        for i, sig in enumerate(signals):
            sig.kind = sig.samples.dtype.kind
            size = len(sig)
            sig.size = size
            if size:
                if sig.kind == 'f':
                    value = f'{sig.samples[0]:.6f}'
                else:
                    value = str(sig.samples[0])
                self._min = min(self._min, sig.timestamps[0])
                self._max = max(self._max, sig.timestamps[-1])
            else:
                value = 'n.a.'

            items.append(
                QtWidgets.QTreeWidgetItem([sig.name, value, sig.unit])
            )
        self.channels.addTopLevelItems(items)

        self.timestamp.setRange(self._min, self._max)
        self.min_t.setText(f'{self._min:.3f}s')
        self.max_t.setText(f'{self._max:.3f}s')
        self._update_values()

    def _timestamp_changed(self, stamp):
        val = int((stamp - self._min) / (self._max - self._min) * 9999)
        if val != self.timestamp_slider.value():
            self.timestamp_slider.setValue(val)

        self._update_values(stamp)

    def _timestamp_slider_changed(self, stamp):
        factor = stamp / 9999
        val = (self._max - self._min) * factor + self._min
        if val != self.timestamp.value():
            self.timestamp.setValue(val)

        self._update_values(val)

    def _update_values(self, stamp=None):
        if stamp is None:
            stamp = self.timestamp.value()
        iterator = QtWidgets.QTreeWidgetItemIterator(self.channels)
        
        idx_cache = {}

        if self.format == 'bin':

            index = 0
            while 1:
                item = iterator.value()
                if not item:
                    break
                sig = self.signals[index]
                if sig.size:
                    if sig.group_index in idx_cache:
                        idx = idx_cache[sig.group_index]
                    else:
                        idx = min(sig.size-1, searchsorted(sig.timestamps, stamp))
                        idx_cache[sig.group_index] = idx
                    value = sig.samples[idx]

                    if sig.kind == 'f':
                        item.setText(1, f'{value:.6f}')
                    elif sig.kind in 'ui':
                        item.setText(1, bin(value))
                    else:
                        item.setText(1, str(value))

                index += 1
                iterator += 1
        elif self.format == 'hex':

            index = 0
            while 1:
                item = iterator.value()
                if not item:
                    break
                sig = self.signals[index]
                if sig.size:
                    if sig.group_index in idx_cache:
                        idx = idx_cache[sig.group_index]
                    else:
                        idx = min(sig.size-1, searchsorted(sig.timestamps, stamp))
                        idx_cache[sig.group_index] = idx
                    value = sig.samples[idx]

                    if sig.kind == 'f':
                        item.setText(1, f'{value:.6f}')
                    elif sig.kind in 'ui':
                        item.setText(1, f'0x{value:X}')
                    else:
                        item.setText(1, str(value))

                index += 1
                iterator += 1
        else:
            index = 0
            while 1:
                item = iterator.value()
                if not item:
                    break
                sig = self.signals[index]
                if sig.size:
                    if sig.group_index in idx_cache:
                        idx = idx_cache[sig.group_index]
                    else:
                        idx = min(sig.size-1, searchsorted(sig.timestamps, stamp))
                        idx_cache[sig.group_index] = idx
                    value = sig.samples[idx]
                    if sig.kind == 'f':
                        item.setText(1, f'{value:.6f}')
                    else:
                        item.setText(1, str(value))

                index += 1
                iterator += 1

    def add_new_channel(self, sig):
        if sig:
            self.add_signals(self.signals + [sig,])

    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.modifiers()

        if key in (QtCore.Qt.Key_H, QtCore.Qt.Key_B, QtCore.Qt.Key_P) and modifier == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_H:
                self.format = 'hex'
            elif key == QtCore.Qt.Key_B:
                self.format = 'bin'
            else:
                self.format = 'phys'
            self._update_values()
            event.accept()
        else:
            super().keyPressEvent(event)
