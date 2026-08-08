import sys
import os
from PySide6.QtCore import Qt, QRectF, QVariantAnimation, Signal, QEasingCurve
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap, QPen, QIcon
from PySide6.QtWidgets import QWidget, QStyleOptionButton
from core.game_detector import get_profile_by_id

ICON_BASE = 56
ACCENT = QColor("#C2462C")

def get_absolute_asset_path(relative_path: str) -> str:
    """Resolves path for dev runs and PyInstaller EXE."""
    # For PyInstaller EXE: resources are in sys._MEIPASS
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    # For development: relative to project root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, relative_path)

class GameCarousel(QWidget):
    """Animated vertical game launcher."""
    game_selected = Signal(str)  # emits the game_id

    def __init__(self):
        super().__init__()
        self.setObjectName("GameCarousel")  # For QSS targeting
        self._games = []      # (game_id, title, QPixmap)
        self._pos = 0.0       # continuous focus position
        self._target = 0
        self._spacing = 76
        self.setMinimumHeight(240)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self._anim.finished.connect(self._on_anim_finished)

    # ---------- data ----------

    def add_game(self, game_id: str):
        profile = get_profile_by_id(game_id)
        if not profile:
            return
        icon_path = get_absolute_asset_path(f"assets/{profile.icon_name}")
        pix = QPixmap(icon_path)
        if pix.isNull():
            # Fallback: create a placeholder icon
            pix = QPixmap(ICON_BASE, ICON_BASE)
            pix.fill(QColor("#3A3D44"))
        self._games.append((game_id, profile.title, pix))
        self._update_spacing()
        self.update()

    def clear(self):
        self._anim.stop()
        self._games.clear()
        self._pos = 0.0
        self._target = 0
        self.update()

    def count(self) -> int:
        return len(self._games)

    def current_index(self) -> int:
        return self._target

    # ---------- selection / animation ----------

    def select_game(self, index: int, animate: bool = True):
        n = len(self._games)
        if n == 0:
            return
        index = max(0, min(n - 1, index))
        if animate:
            self._anim.stop()
            self._anim.setStartValue(float(self._pos))
            self._anim.setEndValue(float(index))
            self._anim.start()
        else:
            self._pos = float(index)
        self._target = index
        self.game_selected.emit(self._games[index][0])
        self.update()

    def _move(self, delta: int):
        self.select_game(self._target + delta)

    def _on_anim(self, value):
        self._pos = float(value)
        self.update()

    def _on_anim_finished(self):
        self._pos = float(self._target)
        self.update()

    # ---------- input ----------

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._move(-1)
        elif delta < 0:
            self._move(1)
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Up, Qt.Key.Key_W):
            self._move(-1)
        elif key in (Qt.Key.Key_Down, Qt.Key.Key_S):
            self._move(1)
        elif key == Qt.Key.Key_Home:
            self.select_game(0)
        elif key == Qt.Key.Key_End:
            self.select_game(len(self._games) - 1)
        elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Space):
            if self._games:
                self.game_selected.emit(self._games[self._target][0])
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            idx = self._item_at(event.position().y())
            if idx is not None:
                self.setFocus()
                self.select_game(idx)
            event.accept()
            return
        super().mousePressEvent(event)

    def _item_at(self, y: float):
        n = len(self._games)
        if n == 0:
            return None
        cy = self.height() / 2
        best, best_d = None, 1e9
        for i in range(n):
            d = abs(cy + (i - self._pos) * self._spacing - y)
            if d < best_d:
                best_d, best = d, i
        return best if best_d <= self._spacing * 0.7 else None

    # ---------- layout / paint ----------

    def resizeEvent(self, event):
        self._update_spacing()
        self.update()
        super().resizeEvent(event)

    def _update_spacing(self):
        n = max(1, len(self._games))
        self._spacing = int(max(70, min(92, self.height() / n)))

    @staticmethod
    def _focus(dy: float) -> float:
        a = abs(dy)
        if a <= 1.0:
            return 1.0 - a * 0.30
        if a <= 2.0:
            return 0.70 - (a - 1.0) * 0.24
        return max(0.24, 0.46 - (a - 2.0) * 0.12)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            self._paint(painter)
        except Exception as e:
            # Log error but don't crash - draw error state
            print(f"GameCarousel paint error: {e}")
            painter.fillRect(self.rect(), QColor("#1A1C1F"))
            painter.setPen(QColor("#FF6B6B"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Render Error")
        finally:
            painter.end()

    def _paint(self, painter: QPainter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        n = len(self._games)
        if n == 0:
            painter.fillRect(self.rect(), QColor("#1A1C1F"))
            painter.setPen(QColor("#8A8F96"))
            f = QFont(self.font())
            f.setPointSize(10)
            painter.setFont(f)
            painter.drawText(self.rect(), int(Qt.AlignmentFlag.AlignCenter), "No games found")
            return

        w = self.width()
        h = self.height()
        cy = h / 2

        for i, (game_id, title, pix) in enumerate(self._games):
            item_cy = cy + (i - self._pos) * self._spacing
            if item_cy < -60 or item_cy > h + 60:
                continue

            focus = self._focus(i - self._pos)
            icon_h = ICON_BASE * (0.70 + 0.45 * focus)
            alpha = int(120 + 115 * focus)
            painter.setOpacity(max(0.40, min(1.0, alpha / 255.0)))

            # Card behind each icon so dark FNAF artwork is clearly visible
            card = QRectF(w / 2 - icon_h * 0.85, item_cy - icon_h * 0.75, icon_h * 1.7, icon_h * 1.5 + 6)
            if focus > 0.82:
                card_bg = QColor("#3A3D44")
                card_bg.setAlpha(255)
            else:
                card_bg = QColor("#2B2D31")
                card_bg.setAlpha(230)
            painter.setBrush(card_bg)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(card, 12, 12)

            if focus > 0.82:
                t = (focus - 0.82) / 0.18
                glow = QColor(ACCENT)
                glow.setAlpha(int(46 * t))
                painter.setBrush(glow)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(
                    QRectF(w / 2 - icon_h * 1.15, item_cy - icon_h * 0.75, icon_h * 2.3, icon_h * 1.5),
                    12, 12,
                )
                # FIXED: QPen.setAlpha doesn't exist - use QColor with alpha
                pen_color = QColor(ACCENT)
                pen_color.setAlpha(int(150 * t))
                pen = QPen(pen_color)
                pen.setWidthF(1.4)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(pen)
                painter.drawRoundedRect(
                    QRectF(w / 2 - icon_h * 1.05, item_cy - icon_h * 0.68, icon_h * 2.1, icon_h * 1.36),
                    10, 10,
                )

            if not pix.isNull():
                # drawPixmap needs an explicit source rect in PySide6
                target = QRectF(w / 2 - icon_h / 2, item_cy - icon_h / 2 - 6, icon_h, icon_h)
                source = QRectF(0, 0, pix.width(), pix.height())
                painter.drawPixmap(target, pix, source)

            if focus > 0.8:
                painter.setPen(QColor("#FFFFFF"))
            else:
                painter.setPen(QColor("#B9BEC6"))
            f = QFont(self.font())
            f.setPointSizeF(9.5 + 1.4 * focus)
            f.setBold(focus > 0.75)
            painter.setFont(f)
            painter.drawText(
                QRectF(4, item_cy + icon_h / 2 - 2, w - 8, 26),
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                title,
            )

        painter.setOpacity(1.0)