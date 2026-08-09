import sys
import os
from PySide6.QtCore import Qt, Signal, QRectF, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPixmap, QColor, QFont, QPen
from PySide6.QtWidgets import QWidget
from core.game_detector import get_all_profiles

BG = QColor("#1E2127")
PANEL = QColor("#21252B")
BORDER = QColor("#3A4048")
FOCUS_ACCENT = QColor("#C2462C")
TITLE_COLOR = QColor("#E6E8EA")
MUTED = QColor("#7F848E")
FALLBACK = QColor("#3A3D44")

FOCUS_W = 560
FOCUS_H = 262
SPACING = 470
MIN_SCALE = 0.40
TITLE_ZONE = 46


def get_absolute_asset_path(relative_path: str) -> str:
    """Resolves bundled assets for dev runs and PyInstaller EXE."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root_dir, relative_path)


class GameCarousel(QWidget):
    """PS5-style horizontal cover carousel.

    All games are always visible. The focused cover sits centered and large;
    neighbours shrink and fade with distance. Navigation is smooth (OutCubic
    easing) via arrow keys, mouse wheel or direct click.
    """
    game_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("GameCarousel")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(FOCUS_H + TITLE_ZONE + 14)
        self._entries = []          # {id, pix, available, title}
        self._pos = 0.0             # animated float focus position
        self._target = 0            # int target index
        self._anim = None
        self._last_emitted = None

    # ---------------- data ----------------

    def populate_all(self):
        self._entries = []
        self._pos = 0.0
        self._target = 0
        self._last_emitted = None
        for p in get_all_profiles():
            pix = QPixmap(get_absolute_asset_path(
                f"assets/banners/{p.banner_name or p.icon_name}"))
            if pix.isNull():
                pix = QPixmap(get_absolute_asset_path(f"assets/{p.icon_name}"))
            if pix.isNull():
                pix = QPixmap(64, 64)
                pix.fill(FALLBACK)
            icon = QPixmap(get_absolute_asset_path(f"assets/{p.icon_name}"))
            if icon.isNull():
                icon = QPixmap(pix)
            self._entries.append({
                "id": p.id, "pix": pix, "icon": icon,
                "available": False, "title": p.title,
            })
        self.update()

    def set_available(self, game_id: str):
        for e in self._entries:
            if e["id"] == game_id and not e["available"]:
                e["available"] = True
                self.update()
                return

    def select_first_available(self):
        for i, e in enumerate(self._entries):
            if e["available"]:
                self._animate_to(i)
                return
        self.update()

    # ---------------- geometry ----------------

    def _geometry(self, index: int, cx: float, cy: float):
        d = index - self._pos
        scale = max(MIN_SCALE, 1.0 - 0.30 * min(abs(d), 2.0))
        w = FOCUS_W * scale
        h = FOCUS_H * scale
        x = cx + d * SPACING - w / 2.0
        y = cy - h / 2.0
        return x, y, w, h, scale

    # ---------------- animation / navigation ----------------

    def _animate_to(self, index: int):
        n = len(self._entries)
        if n == 0 or index < 0 or index >= n:
            return
        if self._anim is not None and self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()
        self._target = index
        anim = QVariantAnimation(self)
        anim.setStartValue(self._pos)
        anim.setEndValue(float(index))
        anim.setDuration(380)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.valueChanged.connect(self._on_anim_value)
        anim.finished.connect(self._on_anim_finished)
        self._anim = anim
        anim.start()

    def _on_anim_value(self, value):
        self._pos = float(value)
        self.update()

    def _on_anim_finished(self):
        self._pos = float(self._target)
        self.update()
        self._emit_current()

    def _emit_current(self):
        if not (0 <= self._target < len(self._entries)):
            return
        e = self._entries[self._target]
        if e["available"] and e["id"] != self._last_emitted:
            self._last_emitted = e["id"]
            self.game_selected.emit(e["id"])

    def _next_available(self, direction: int):
        t = self._target
        step = 1 if direction > 0 else -1
        i = t + step
        while 0 <= i < len(self._entries):
            if self._entries[i]["available"]:
                return i
            i += step
        return None

    # ---------------- input ----------------

    def keyPressEvent(self, event):
        idx = None
        if event.key() == Qt.Key.Key_Left:
            idx = self._next_available(-1)
        elif event.key() == Qt.Key.Key_Right:
            idx = self._next_available(1)
        elif event.key() == Qt.Key.Key_Home:
            for i, e in enumerate(self._entries):
                if e["available"]:
                    idx = i
                    break
        elif event.key() == Qt.Key.Key_End:
            for i in range(len(self._entries) - 1, -1, -1):
                if self._entries[i]["available"]:
                    idx = i
                    break
        if idx is not None:
            self._animate_to(idx)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        idx = self._next_available(1 if event.angleDelta().y() < 0 else -1)
        if idx is not None:
            self._animate_to(idx)
        event.accept()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self._entries:
            return
        cx = self.width() / 2.0
        cy = (self.height() - TITLE_ZONE) / 2.0
        for i, e in enumerate(self._entries):
            if not e["available"]:
                continue
            x, y, w, h, _ = self._geometry(i, cx, cy)
            if QRectF(x, y, w, h).contains(event.position()):
                self._animate_to(i)
                return

    # ---------------- painting ----------------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), BG)
        p.fillRect(QRectF(0, self.height() - 1, self.width(), 1), BORDER)

        n = len(self._entries)
        if n == 0:
            empty_font = QFont(self.font())
            empty_font.setPixelSize(14)
            p.setFont(empty_font)
            p.setPen(MUTED)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "No games configured.")
            return

        cx = self.width() / 2.0
        cy = (self.height() - TITLE_ZONE) / 2.0

        for i, e in enumerate(self._entries):
            x, y, w, h, scale = self._geometry(i, cx, cy)
            if x + w < -20 or x > self.width() + 20:
                continue
            d = abs(i - self._pos)
            alpha = max(0.20, 1.0 - 0.45 * min(d, 2.0))
            if not e["available"]:
                alpha *= 0.55
            p.setOpacity(alpha)

            focused = d < 0.5
            if focused:
                p.setOpacity(1.0)
                p.setBrush(QColor(0, 0, 0, 110))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(QRectF(x + 4, y + 8, w, h + 2))

            p.setBrush(PANEL)
            p.setPen(QPen(FOCUS_ACCENT if focused and e["available"] else BORDER))
            p.drawRoundedRect(QRectF(x, y, w, h), 6, 6)
            p.drawPixmap(QRectF(x + 2, y + 2, w - 4, h - 4).toRect(), e["pix"])

            if not e["available"]:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(20, 23, 27, 215))
                p.drawRoundedRect(QRectF(x + 8, y + h - 30, w - 16, 22), 3, 3)
                tag_font = QFont(self.font())
                tag_font.setPixelSize(11)
                p.setFont(tag_font)
                p.setPen(QColor("#FF6B5E"))
                p.drawText(QRectF(x + 8, y + h - 30, w - 16, 22),
                           Qt.AlignmentFlag.AlignCenter, "SAVE NOT FOUND")

        p.setOpacity(1.0)
        if 0 <= self._target < n:
            e = self._entries[self._target]
            f = QFont(self.font())
            f.setPixelSize(20)
            f.setBold(True)
            p.setFont(f)
            icon = e["icon"] if not e["icon"].isNull() else None
            title_w = p.fontMetrics().horizontalAdvance(e["title"])
            gap = 8 if icon else 0
            icon_h = 26
            total_w = title_w + (icon_h + gap if icon else 0)
            start_x = (self.width() - total_w) / 2.0
            title_rect = QRectF(0, self.height() - TITLE_ZONE, self.width(), 28)
            if icon:
                p.setOpacity(1.0)
                p.drawPixmap(QRectF(start_x, self.height() - TITLE_ZONE + 1,
                                    icon_h, icon_h).toRect(), icon)
                title_rect = QRectF(start_x + icon_h + gap,
                                    self.height() - TITLE_ZONE, title_w + 8, 28)
            p.setPen(TITLE_COLOR)
            p.drawText(title_rect,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       e["title"])
            f2 = QFont(self.font())
            f2.setPixelSize(11)
            p.setFont(f2)
            p.setPen(MUTED)
            p.drawText(QRectF(0, self.height() - 18, self.width(), 14),
                       Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                       e["id"].upper())
