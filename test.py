from PyQt6.QtWidgets import (
    QApplication, QTableWidget, QTableWidgetItem, QStyledItemDelegate
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QFontMetrics, QPainter
import sys


class RightAlignElideLeftDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

    def paint(self, painter: QPainter, option, index):
        # Customize elided text
        painter.save()

        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text is None:
            text = ""

        # Prepare font metrics and elide from left
        font_metrics = QFontMetrics(option.font)
        elided = font_metrics.elidedText(text, Qt.TextElideMode.ElideLeft, option.rect.width())

        option.text = elided
        super().paint(painter, option, index)

        painter.restore()


app = QApplication(sys.argv)

table = QTableWidget(1, 1)
table.setItem(0, 0, QTableWidgetItem("This is a very long piece of text"))

# Apply custom delegate
delegate = RightAlignElideLeftDelegate()
table.setItemDelegateForColumn(0, delegate)

table.resize(200, 100)
table.show()
sys.exit(app.exec())
