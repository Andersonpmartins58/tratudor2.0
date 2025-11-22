import time

# ... (imports remain the same)

class TranslatorService:
    def __init__(self):
        # mss não é thread-safe se compartilhado entre threads no Windows
        # Vamos instanciar apenas quando necessário
        self.translator = GoogleTranslator(source=Config.SOURCE_LANG, target=Config.TARGET_LANG)
        self._stop_event = threading.Event()
        self._current_thread = None

    def capture_and_translate(self, x, y, width, height, callback):
        """
        Captura única (mantida para compatibilidade ou uso futuro)
        """
        thread = threading.Thread(target=self._worker, args=(x, y, width, height, callback))
        thread.daemon = True
        thread.start()

    def start_continuous_translation(self, x, y, width, height, callback, interval=1.0):
        """
        Inicia o loop de tradução contínua.
        """
        self.stop_continuous_translation() # Parar anterior se houver
        self._stop_event.clear()
        
        self._current_thread = threading.Thread(target=self._continuous_worker, args=(x, y, width, height, callback, interval))
        self._current_thread.daemon = True
        self._current_thread.start()

    def stop_continuous_translation(self):
        """
        Para o loop de tradução.
        """
        self._stop_event.set()
        if self._current_thread:
            self._current_thread.join(timeout=1.0)
            self._current_thread = None

    def _worker(self, x, y, width, height, callback):
        # ... (mantido igual, mas pode ser refatorado para usar lógica comum se quiser)
        try:
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            text = pytesseract.image_to_string(img).strip()
            if not text:
                callback("Sem texto", "...", img)
                return

            translated = self.translator.translate(text)
            callback(text, translated, img)

        except Exception as e:
            callback("Erro", str(e), None)

    def _continuous_worker(self, x, y, width, height, callback, interval):
        last_text = None
        
        try:
            # Criar instância do mss para esta thread
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                
                while not self._stop_event.is_set():
                    start_time = time.time()
                    
                    # 1. Captura
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    # 2. OCR
                    text = pytesseract.image_to_string(img).strip()
                    
                    # 3. Verificar mudança
                    if text and text != last_text:
                        # 4. Traduzir
                        try:
                            translated = self.translator.translate(text)
                            last_text = text
                            callback(text, translated, img)
                        except Exception as e:
                            print(f"Erro na tradução: {e}")
                    elif not text:
                         # Se não tem texto, talvez limpar ou manter o último?
                         # Vamos manter o último por enquanto ou passar vazio se mudou de texto para vazio
                         if last_text:
                             last_text = None
                             # callback("", "", img) # Opcional: limpar tela
                    
                    # 5. Esperar pelo intervalo descontando o tempo de processamento
                    elapsed = time.time() - start_time
                    sleep_time = max(0.1, interval - elapsed)
                    time.sleep(sleep_time)
                    
        except Exception as e:
            print(f"Erro no loop contínuo: {e}")
