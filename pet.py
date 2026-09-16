"""Cyrene desktop companion: a transparent native Qt window."""
from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, QStandardPaths
from PySide6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from core import clamp_position, read_settings, write_settings

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
STYLE = """
QMenu { background: #fff9ff; color: #554363; border: 1px solid #e9d5ef;
        border-radius: 12px; padding: 8px; font: 10pt 'Microsoft YaHei UI'; }
QMenu::item { padding: 8px 24px 8px 14px; border-radius: 6px; }
QMenu::item:selected { background: #f2e2f5; color: #91549f; }
QMenu::separator { height: 1px; background: #efdfef; margin: 5px 10px; }
"""
LINES = ["今天，也一起写下新的回忆吧♪", "忙碌的时候，也要记得休息哦。",
         "我在这里，陪着你呢。", "把小小的快乐，留给今天吧♪", "窗外的风，会带来什么故事呢？"]


class Pet(QWidget):
    def __init__(self, settings_path=None):
        super().__init__()
        self.settings_path = settings_path or Path(QStandardPaths.writableLocation(
            QStandardPaths.AppConfigLocation)) / "settings.json"
        self.options = read_settings(self.settings_path)
        self.scale = self.options["scale"]
        self.sprites = {name: QPixmap(str(ROOT / "assets" / f"{name}.png"))
                        for name in ("idle", "happy", "sleep", "walk")}
        if any(p.isNull() for p in self.sprites.values()):
            raise RuntimeError("桌宠素材缺失，请保留 assets 文件夹并重新启动。")
        self.setWindowTitle("昔涟 · 往昔的涟漪")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowIcon(QIcon(self.sprites["idle"]))
        self.state = "idle"
        self.state_until = 0.0
        self.next_action = time.monotonic() + 16
        self.next_line = time.monotonic() + 45
        self.bubble = "你好呀，我是昔涟♪\n拖动陪我走走，右键打开菜单。"
        self.bubble_until = time.monotonic() + 9
        self.particles = []
        self.direction = 1
        self.drag_anchor = None
        self.drag_start = None
        self.dragged = False
        self.click_timer = QTimer(self)
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.pet_head)
        self.hover = False
        self.frame_time = time.monotonic()
        self.phase = 0.0
        self.x_float = 0.0
        self.apply_flags()
        self.resize_pet()
        area = QApplication.primaryScreen().availableGeometry()
        position = self.options.get("position", [area.right() - self.width() - 42,
                                                   area.bottom() - self.height() - 16])
        self.move(*position)
        self.keep_visible()
        self.x_float = float(self.x())
        self.tray = QSystemTrayIcon(QIcon(self.sprites["idle"]), self)
        self.tray.setToolTip("昔涟桌宠 · 双击显示 / 右键菜单")
        self.tray.setContextMenu(self.make_menu())
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        self.screen_connections = []
        for screen in QApplication.screens():
            screen.availableGeometryChanged.connect(self.keep_visible)
        QApplication.instance().screenRemoved.connect(self.keep_visible)
        QApplication.instance().aboutToQuit.connect(self.save)

    def apply_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.options["topmost"]:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def resize_pet(self):
        # Preserve the bottom-center anchor when changing size.
        foot = QPoint(self.x() + self.width() // 2, self.y() + self.height())
        self.setFixedSize(round(300 * self.scale), round(370 * self.scale))
        if self.isVisible():
            self.move(foot.x() - self.width() // 2, foot.y() - self.height())
        self.keep_visible()
        self.update()

    def area(self):
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        a = screen.availableGeometry()
        return a.x(), a.y(), a.x() + a.width(), a.y() + a.height()

    def keep_visible(self, *_):
        self.move(*clamp_position(self.x(), self.y(), self.width(), self.height(), self.area()))
        self.x_float = float(self.x())

    def save(self):
        self.options["scale"] = self.scale
        self.options["position"] = [self.x(), self.y()]
        try:
            write_settings(self.settings_path, self.options)
        except OSError:
            pass  # Companion remains usable even if the profile is read-only.

    def say(self, text, seconds=5):
        self.bubble = text
        self.bubble_until = time.monotonic() + seconds
        self.update()

    def pet_head(self):
        self.state = "happy"
        self.state_until = time.monotonic() + 3.0
        self.next_action = self.state_until + random.uniform(10, 20)
        self.say(random.choice(["嘿嘿，是摸摸头呀♪", "这份温柔，我会记住的。", "有你在，今天也是好天气♪"]))
        self.particles = [[random.uniform(95, 205), random.uniform(105, 155), random.uniform(-18, 18),
                           random.uniform(1.1, 2.0)] for _ in range(7)]

    def sleep_toggle(self):
        if self.state == "sleep":
            self.state = "idle"
            self.say("醒来啦。我们继续一起冒险吧♪")
            self.next_action = time.monotonic() + 16
        else:
            self.state = "sleep"
            self.say("让我在你身边，小睡一会儿…", 4)
        self.update_tray()

    def walk(self):
        self.state = "walk"
        self.direction = random.choice([-1, 1])
        self.x_float = float(self.x())
        self.state_until = time.monotonic() + random.uniform(4, 7)
        self.say("出发，去收集一点新的回忆♪", 3)

    def set_option(self, key, value):
        self.options[key] = value
        if key == "topmost":
            pos = self.pos()
            visible = self.isVisible()
            self.apply_flags()
            self.move(pos)
            if visible:
                self.show()
        elif key == "wander" and not value and self.state == "walk":
            self.state = "idle"
        elif key == "quiet" and value:
            self.bubble_until = 0
        self.save()
        self.update_tray()

    def set_scale(self, value):
        self.scale = max(0.65, min(1.6, value))
        self.resize_pet()
        self.save()

    def restore(self):
        self.show()
        self.keep_visible()
        self.raise_()

    def home(self):
        a = QApplication.primaryScreen().availableGeometry()
        self.move(a.x() + a.width() - self.width() - 32,
                  a.y() + a.height() - self.height() - 12)
        self.restore()
        self.save()

    def make_menu(self):
        menu = QMenu()
        menu.setStyleSheet(STYLE)
        label = menu.addAction("昔涟  /  往昔的涟漪")
        label.setEnabled(False)
        menu.addSeparator()
        menu.addAction("摸摸头 ♡", self.pet_head)
        menu.addAction("醒来" if self.state == "sleep" else "小睡一会儿", self.sleep_toggle)
        menu.addAction("散步一下", self.walk)
        menu.addSeparator()
        for key, label in (("wander", "自动散步"), ("topmost", "始终置顶"), ("quiet", "安静陪伴")):
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.options[key])
            action.toggled.connect(lambda checked, k=key: self.set_option(k, checked))
        size = menu.addMenu("小人大小")
        for text, value in (("小巧 · 75%", .75), ("标准 · 100%", 1), ("大一点 · 125%", 1.25), ("超可爱 · 150%", 1.5)):
            action = size.addAction(text)
            action.setCheckable(True)
            action.setChecked(abs(self.scale - value) < .02)
            action.triggered.connect(lambda checked=False, v=value: self.set_scale(v))
        menu.addSeparator()
        menu.addAction("显示桌宠", self.restore)
        menu.addAction("回到主屏幕", self.home)
        if QSystemTrayIcon.isSystemTrayAvailable():
            menu.addAction("暂时藏起来", self.hide)
        menu.addAction("操作说明", lambda: self.say("单击摸头 · 双击睡觉 / 唤醒\n拖动移动 · 滚轮缩放 · 右键菜单", 9))
        menu.addSeparator()
        menu.addAction("退出桌宠", QApplication.instance().quit)
        return menu

    def update_tray(self):
        old = self.tray.contextMenu()
        self.tray.setContextMenu(self.make_menu())
        if old:
            old.deleteLater()

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.restore()

    def contextMenuEvent(self, event):
        self.state = "idle" if self.state == "walk" else self.state
        menu = self.make_menu()
        menu.exec(event.globalPos())
        menu.deleteLater()

    def enterEvent(self, event):
        self.hover = True
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def leaveEvent(self, event):
        self.hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_anchor = event.globalPosition().toPoint() - self.pos()
            self.drag_start = event.globalPosition().toPoint()
            self.dragged = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drag_anchor is not None:
            if (event.globalPosition().toPoint() - self.drag_start).manhattanLength() > 5:
                self.dragged = True
            if self.dragged:
                self.move(event.globalPosition().toPoint() - self.drag_anchor)
                self.x_float = float(self.x())
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag_anchor is not None:
            self.drag_anchor = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if self.dragged:
                self.keep_visible()
                self.save()
                if self.state != "sleep":
                    self.state = "idle"
                    self.next_action = time.monotonic() + 12
            else:
                # Delay a single click so it cannot consume a sleep/wake double click.
                self.click_timer.start(QApplication.doubleClickInterval())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_timer.stop()
            self.drag_anchor = None
            self.sleep_toggle()

    def wheelEvent(self, event):
        self.set_scale(self.scale + (.05 if event.angleDelta().y() > 0 else -.05))
        event.accept()

    def tick(self):
        now = time.monotonic()
        dt = min(now - self.frame_time, .1)
        self.frame_time = now
        self.phase += dt
        if not self.isVisible():
            return
        if self.drag_anchor is None:
            if self.state in ("happy", "walk") and now >= self.state_until:
                self.state = "idle"
                self.next_action = now + random.uniform(12, 22)
            if self.state == "idle" and self.options["wander"] and now >= self.next_action:
                self.walk()
            if self.state == "walk":
                self.x_float += self.direction * dt * 28 * self.scale
                left, top, right, bottom = self.area()
                if self.x_float < left or self.x_float > right - self.width():
                    self.direction *= -1
                self.x_float = max(left, min(self.x_float, max(left, right - self.width())))
                self.move(round(self.x_float), self.y())
        if now >= self.next_line:
            self.next_line = now + random.uniform(45, 80)
            if not self.options["quiet"] and self.state == "idle":
                self.say(random.choice(LINES), 5)
        for particle in self.particles:
            particle[0] += particle[2] * dt
            particle[1] -= 32 * dt
            particle[3] -= dt
        self.particles = [p for p in self.particles if p[3] > 0]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.scale(self.scale, self.scale)
        t = self.phase
        if self.state == "walk":
            bob, tilt = abs(math.sin(t * 8)) * -7, math.sin(t * 8) * 3
        elif self.state == "happy":
            bob, tilt = -abs(math.sin(t * 5)) * 9, math.sin(t * 5) * 4
        elif self.state == "sleep":
            bob, tilt = math.sin(t * 1.6) * 2, -4
        else:
            bob, tilt = math.sin(t * 2.3) * 3, math.sin(t * 1.4) * 1.3
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(114, 78, 143, 25))
        painter.drawEllipse(QRectF(91, 335, 118, 12))
        sprite = self.sprites[self.state]
        painter.save()
        painter.translate(150, 337 + bob)
        painter.rotate(tilt)
        if self.state == "walk" and self.direction < 0:
            painter.scale(-1, 1)
        target = QRectF(-131, -262, 262, 262)
        painter.drawPixmap(target, sprite, QRectF(sprite.rect()))
        painter.restore()
        for x, y, vx, life in self.particles:
            painter.setOpacity(min(1, life))
            painter.setPen(QColor("#e8a4ca"))
            painter.setFont(QFont("Segoe UI Symbol", 16))
            painter.drawText(QPointF(x, y), "♡")
        painter.setOpacity(1)
        if self.state == "sleep":
            painter.setPen(QColor("#ae88c4"))
            painter.setFont(QFont("Segoe UI", 13))
            painter.drawText(QPointF(220, 126 + math.sin(t) * 4), "z Z")
        if time.monotonic() < self.bubble_until:
            path = QPainterPath()
            path.addRoundedRect(QRectF(10, 7, 280, 61), 17, 17)
            path.moveTo(140, 67)
            path.lineTo(151, 78)
            path.lineTo(160, 67)
            painter.fillPath(path, QColor(255, 248, 255, 245))
            painter.setPen(QColor("#dec4e7"))
            painter.drawPath(path)
            painter.setPen(QColor("#765881"))
            painter.setFont(QFont("Microsoft YaHei UI", 9))
            painter.drawText(QRectF(20, 13, 260, 48), Qt.AlignmentFlag.AlignCenter, self.bubble)
        elif self.hover:
            painter.setBrush(QColor(255, 248, 255, 225))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(79, 350, 142, 19), 9, 9)
            painter.setPen(QColor("#9e7ca8"))
            painter.setFont(QFont("Microsoft YaHei UI", 7))
            painter.drawText(QRectF(79, 350, 142, 19), Qt.AlignmentFlag.AlignCenter, "昔涟  ·  右键与我互动")


def single_instance(app):
    socket = QLocalSocket()
    socket.connectToServer("CyreneDesktopPet-v1")
    if socket.waitForConnected(400):
        socket.write(b"show")
        socket.waitForBytesWritten(500)
        socket.disconnectFromServer()
        return None
    server = QLocalServer(app)
    if not server.listen("CyreneDesktopPet-v1"):
        QLocalServer.removeServer("CyreneDesktopPet-v1")
        if not server.listen("CyreneDesktopPet-v1"):
            raise RuntimeError("无法创建桌宠单实例服务。")
    return server


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CyreneDesktopPet")
    app.setOrganizationName("CyreneFanProject")
    app.setQuitOnLastWindowClosed(False)
    if "--smoke-test" in sys.argv:
        import tempfile
        from PySide6.QtTest import QTest
        with tempfile.TemporaryDirectory() as directory:
            pet = Pet(Path(directory) / "settings.json")
            pet.show()
            QTest.qWait(120)
            assert pet.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=QPoint(150, 190))
            QTest.qWait(QApplication.doubleClickInterval() + 50)
            assert pet.state == "happy"
            QTest.mouseDClick(pet, Qt.MouseButton.LeftButton, pos=QPoint(150, 190))
            assert pet.state == "sleep"
            QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=QPoint(150, 190))
            QTest.mouseDClick(pet, Qt.MouseButton.LeftButton, pos=QPoint(150, 190))
            QTest.qWait(QApplication.doubleClickInterval() + 50)
            assert pet.state == "idle"
            pet.walk()
            before = pet.x_float
            QTest.qWait(180)
            assert abs(pet.x_float - before) > .1
            pet.set_option("wander", False)
            assert pet.state == "idle"
            pet.set_scale(1.25)
            assert pet.width() == 375
            pet.home()
            pet.set_scale(1)
            pet.pet_head()
            pet.grab().save(str(Path(__file__).resolve().parent / "preview.png"))
            pet.save()
            assert read_settings(pet.settings_path)["wander"] is False
            pet.tray.hide()
            pet.close()
        print("PASS: transparent window, click, sleep/wake, walking, scale, settings, preview")
        return 0
    server = single_instance(app)
    if server is None:
        return 0
    pet = Pet()
    def show_existing():
        connection = server.nextPendingConnection()
        if connection:
            connection.disconnectFromServer()
            connection.deleteLater()
        pet.restore()
    server.newConnection.connect(show_existing)
    pet.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
