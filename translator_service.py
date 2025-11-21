import mss
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import threading
from config import Config
import os

# Configurar o caminho do Tesseract se definido
if hasattr(Config, 'TESSERACT_CMD') and os.path.exists(Config.TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

class TranslatorService:
    def __init__(self):
        self.sct = mss.mss()
        self.translator = GoogleTranslator(source=Config.SOURCE_LANG, target=Config.TARGET_LANG)

    def capture_and_translate(self, x, y, width, height, callback):
        """
        Captura a tela, faz OCR e traduz.
        Executa em uma thread separada para não travar a UI.
        Chama o callback(texto_original, texto_traduzido) ao finalizar.
        """
        thread = threading.Thread(target=self._worker, args=(x, y, width, height, callback))
        thread.daemon = True
        thread.start()

    def _worker(self, x, y, width, height, callback):
        try:
            # Captura de tela com mss (muito rápido)
            monitor = {"top": y, "left": x, "width": width, "height": height}
            sct_img = self.sct.grab(monitor)
            
            # Conversão para PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # OCR
            text = pytesseract.image_to_string(img)
            text = text.strip()

            if not text:
                callback("Sem texto detectado", "Nenhum texto foi encontrado na área selecionada.")
                return

            # Tradução
            translated = self.translator.translate(text)
            
            callback(text, translated)

        except Exception as e:
            callback("Erro", f"Ocorreu um erro: {str(e)}")
