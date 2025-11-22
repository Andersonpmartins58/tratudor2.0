import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import keyboard
import threading
import sys
import os
import tkinter as tk
from config import Config
from translator_service import TranslatorService
from overlay import SelectionOverlay, ResultWindow

class ScreenTranslatorApp:
    def __init__(self):
        self.translator_service = TranslatorService()
        self.icon = None
        self.is_running = True
        self.result_window = None
        
        # Inicializar Tkinter na thread principal
        self.root = tk.Tk()
        self.root.withdraw() # Esconder a janela principal
        
        # Configurar fechamento
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def create_icon(self):
        # Criar um ícone simples via código para a bandeja
        width = 64
        height = 64
        color1 = "blue"
        color2 = "white"
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((width // 2, 0, width, height // 2), fill=color2)
        dc.rectangle((0, height // 2, width // 2, height), fill=color2)
        return image

    def on_quit(self, icon, item):
        self.quit_app()

    def quit_app(self):
        self.is_running = False
        self.translator_service.stop_continuous_translation()
        if self.icon:
            self.icon.stop()
        
        # Parar loop do Tkinter
        self.root.quit()
        sys.exit(0)

    def on_translate_click(self, icon, item):
        self.trigger_selection()

    def trigger_selection(self):
        # Agendar a execução da GUI na thread principal
        self.root.after(0, self._show_overlay)

    def _show_overlay(self):
        try:
            # Passamos self.root como master
            overlay = SelectionOverlay(self.root, self.handle_selection_result)
            overlay.show()
        except Exception as e:
            print(f"Erro ao abrir overlay: {e}")

    def handle_selection_result(self, x, y, w, h):
        print(f"Selecionado: {x},{y} {w}x{h}")
        
        # Se já houver uma janela aberta, fechar e parar serviço anterior
        if self.result_window:
            self.result_window.destroy()
            self.result_window = None
        
        self.translator_service.stop_continuous_translation()

        # Iniciar serviço de tradução contínua
        # Passamos as coordenadas para usar no overlay depois
        self.translator_service.start_continuous_translation(x, y, w, h, lambda orig, trans, img: self.show_result(orig, trans, img, x, y, w, h))

    def show_result(self, original, translated, img, x, y, w, h):
        # O callback vem de outra thread, então agendamos na main thread
        self.root.after(0, lambda: self._show_result_window(original, translated, img, x, y, w, h))

    def _show_result_window(self, original, translated, img, x, y, w, h):
        try:
            if self.result_window:
                # Atualizar existente
                self.result_window.update_content(translated, img)
            else:
                # Criar nova
                self.result_window = ResultWindow(self.root, original, translated, img, x, y, w, h, on_close=self.on_window_close)
        except Exception as e:
            print(f"Erro ao mostrar resultado: {e}")

    def on_window_close(self):
        print("Janela fechada, parando tradução.")
        self.translator_service.stop_continuous_translation()
        self.result_window = None

    def setup_hotkey(self):
        # keyboard roda em thread própria, então trigger_selection já lida com isso via after()
        keyboard.add_hotkey(Config.HOTKEY, self.trigger_selection)

    def run_tray_icon(self):
        # Configurar Tray Icon em thread separada
        menu = (item('Traduzir Área', self.on_translate_click), item('Sair', self.on_quit))
        self.icon = pystray.Icon("name", self.create_icon(), "Screen Translator", menu)
        self.icon.run()

    def run(self):
        # Configurar hotkey
        self.setup_hotkey()

        # Iniciar Tray Icon em thread separada
        tray_thread = threading.Thread(target=self.run_tray_icon)
        tray_thread.daemon = True
        tray_thread.start()
        
        print(f"App rodando. Pressione {Config.HOTKEY} para traduzir.")
        
        # Iniciar loop principal do Tkinter (bloqueante)
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    app.run()
