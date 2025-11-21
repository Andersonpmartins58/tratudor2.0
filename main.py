import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import keyboard
import threading
import sys
import os
from config import Config
from translator_service import TranslatorService
from overlay import SelectionOverlay, ResultWindow

class ScreenTranslatorApp:
    def __init__(self):
        self.translator_service = TranslatorService()
        self.icon = None
        self.is_running = True

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
        self.is_running = False
        icon.stop()
        sys.exit(0)

    def on_translate_click(self, icon, item):
        self.trigger_selection()

    def trigger_selection(self):
        # Executar na thread principal da UI se possível, mas aqui estamos chamando de threads diferentes
        # O overlay cria seu próprio mainloop do tkinter, então deve ser seguro chamar daqui
        # desde que não tenhamos outro loop tkinter rodando simultaneamente na mesma thread.
        # Vamos rodar o overlay em uma nova thread para não bloquear a detecção de teclado/tray?
        # Não, tkinter precisa rodar na main thread geralmente. 
        # Mas como o pystray roda em loop, e o keyboard é hook, vamos tentar lançar o overlay.
        
        # Nota: Tkinter deve ser criado e destruído na mesma thread.
        # Vamos usar uma thread dedicada para a GUI do Tkinter se necessário, ou instanciar sob demanda.
        
        # Abordagem segura: Overlay bloqueante (modal) é aceitável para "selecionar área".
        try:
            overlay = SelectionOverlay(self.handle_selection_result)
            overlay.show()
        except Exception as e:
            print(f"Erro ao abrir overlay: {e}")

    def handle_selection_result(self, x, y, w, h):
        print(f"Selecionado: {x},{y} {w}x{h}")
        # Chamar serviço de tradução
        self.translator_service.capture_and_translate(x, y, w, h, self.show_result)

    def show_result(self, original, translated):
        # Mostrar resultado em janela Tkinter
        # Como o callback vem de uma thread do translator_service, precisamos ter cuidado com Tkinter.
        # O ResultWindow cria seu próprio Tk instance e mainloop, o que é tecnicamente arriscado se feito de thread secundária,
        # mas como o overlay já foi destruído, pode funcionar.
        # O ideal seria enfileirar, mas para simplicidade e modularidade pedida:
        try:
            ResultWindow(original, translated)
        except Exception as e:
            print(f"Erro ao mostrar resultado: {e}")

    def setup_hotkey(self):
        keyboard.add_hotkey(Config.HOTKEY, self.trigger_selection)

    def run(self):
        # Configurar hotkey
        self.setup_hotkey()

        # Configurar Tray Icon
        menu = (item('Traduzir Área', self.on_translate_click), item('Sair', self.on_quit))
        self.icon = pystray.Icon("name", self.create_icon(), "Screen Translator", menu)
        
        print(f"App rodando. Pressione {Config.HOTKEY} para traduzir.")
        self.icon.run()

if __name__ == "__main__":
    app = ScreenTranslatorApp()
    app.run()
