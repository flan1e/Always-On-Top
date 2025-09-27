import os
import sys
import json
import time
import win32gui
import win32con
import keyboard
import pystray
from PIL import Image, ImageDraw
from windows_toasts import Toast, WindowsToaster


def log(msg):
    try:
        with open("debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except:
        pass


log("Модуль загружен. Начало выполнения.")
topmost_windows = set()
_toaster_instance = None
current_hotkey = "ctrl+alt+t"
HOTKEY_FILE = "hotkey.cfg"


def get_toaster():
    global _toaster_instance
    if _toaster_instance is None:
        _toaster_instance = WindowsToaster('AlwaysOnTop')
    return _toaster_instance


def show_toast(title: str, message: str):
    try:
        toast = Toast()
        toast.text_fields = [title, message]
        toast.duration = "short"
        get_toaster().show_toast(toast)
    except Exception as e:
        log(f"Ошибка уведомления: {e}")


def create_default_icon():
    """Создаёт иконку 64x64 с синей рамкой."""
    image = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 60, 60), outline=(0, 120, 255), width=4)
    return image


def load_hotkey():
    global current_hotkey
    if os.path.exists(HOTKEY_FILE):
        try:
            with open(HOTKEY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                hk = data.get("hotkey", "ctrl+alt+t")
                keyboard.parse_hotkey(hk)  
                current_hotkey = hk
        except Exception as e:
            log(f"Ошибка загрузки горячей клавиши: {e}")
            current_hotkey = "ctrl+alt+t"


def save_hotkey(hk):
    global current_hotkey
    try:
        with open(HOTKEY_FILE, 'w', encoding='utf-8') as f:
            json.dump({"hotkey": hk}, f)
        current_hotkey = hk
    except Exception as e:
        show_toast("Ошибка", f"Не удалось сохранить горячую клавишу: {e}")


def register_hotkey():
    try:
        keyboard.unhook_all_hotkeys()
    except:
        pass
    try:
        keyboard.add_hotkey(current_hotkey, toggle_window_topmost)
    except Exception as e:
        show_toast("Ошибка", f"Неверная комбинация клавиш: {e}")


def toggle_window_topmost():
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return
        window_title = win32gui.GetWindowText(hwnd).strip()
        if not window_title:
            return

        if hwnd in topmost_windows:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            topmost_windows.discard(hwnd)
            show_toast("Always on Top", f"Окно '{window_title}' откреплено")
        else:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            topmost_windows.add(hwnd)
            show_toast("Always on Top", f"Окно '{window_title}' закреплено!")
    except Exception as e:
        show_toast("Ошибка", str(e))


def on_set_hotkey(icon, item):
    show_toast(
        "Изменение горячей клавиши",
        "Отредактируйте файл hotkey.cfg рядом с программой.\n"
        "Пример: ctrl+shift+p\n"
        "Затем перезапустите приложение."
    )


def on_quit(icon, item):
    for hwnd in list(topmost_windows):
        try:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        except:
            pass
    icon.stop()  


def main():
    load_hotkey()
    register_hotkey()
    log("Программа запущена")

    image = create_default_icon()
    menu = pystray.Menu(
        pystray.MenuItem("Set Hotkey…", on_set_hotkey),
        pystray.MenuItem("Exit", on_quit)
    )
    icon = pystray.Icon("AlwaysOnTop", image, "Always on Top", menu)

    try:
        icon.run()
    except Exception as e:
        import traceback
        log(f"КРИТИЧЕСКАЯ ОШИБКА в основном цикле: {e}")
        log(f"Traceback:\n{traceback.format_exc()}")
        if hasattr(sys, '_MEIPASS'):
            time.sleep(5)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("Произошла ошибка:")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")