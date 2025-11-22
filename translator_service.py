import time
import mss
import pytesseract
from PIL import Image
from deep_translator import GoogleTranslator
import threading
from config import Config
import os

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
        try:
            with mss.mss() as sct:
                monitor = {"top": y, "left": x, "width": width, "height": height}
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # Usar image_to_data para obter coordenadas de cada palavra
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            paragraphs = {}
            
            # Agrupar palavras em PARÁGRAFOS (block_num, par_num)
            # Isso evita que frases sejam quebradas no meio
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:
                    text = data['text'][i].strip()
                    if not text:
                        continue
                        
                    # Chave única para o parágrafo: block_page_par
                    key = (data['block_num'][i], data['par_num'][i])
                    
                    if key not in paragraphs:
                        paragraphs[key] = {
                            'text': [],
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'right': data['left'][i] + data['width'][i],
                            'bottom': data['top'][i] + data['height'][i]
                        }
                    else:
                        # Atualizar limites da caixa do parágrafo
                        p = paragraphs[key]
                        p['text'].append(text)
                        p['left'] = min(p['left'], data['left'][i])
                        p['top'] = min(p['top'], data['top'][i])
                        p['right'] = max(p['right'], data['left'][i] + data['width'][i])
                        p['bottom'] = max(p['bottom'], data['top'][i] + data['height'][i])
            
            if not paragraphs:
                callback([], [], img)
                return

            # Preparar texto para tradução em lote
            sorted_keys = sorted(paragraphs.keys())
            text_blocks = []
            raw_texts = []
            
            for key in sorted_keys:
                par_data = paragraphs[key]
                full_text = " ".join(par_data['text'])
                raw_texts.append(full_text)
                
                w_par = par_data['right'] - par_data['left']
                h_par = par_data['bottom'] - par_data['top']
                
                text_blocks.append({
                    'original': full_text,
                    'x': par_data['left'],
                    'y': par_data['top'],
                    'w': w_par,
                    'h': h_par
                })

            # Traduzir tudo de uma vez
            full_payload = "\n".join(raw_texts)
            translated_payload = self.translator.translate(full_payload)
            
            if translated_payload:
                translated_lines = translated_payload.split('\n')
                
                if len(translated_lines) == len(text_blocks):
                    for i, block in enumerate(text_blocks):
                        block['translated'] = translated_lines[i]
                else:
                    print("Aviso: Número de parágrafos traduzidos difere do original.")
                    for i, block in enumerate(text_blocks):
                        if i < len(translated_lines):
                            block['translated'] = translated_lines[i]
                        else:
                            block['translated'] = block['original']
            else:
                for block in text_blocks:
                    block['translated'] = block['original']

            callback(text_blocks, None, img)

        except Exception as e:
            print(f"Erro no worker: {e}")
            callback([], None, None)
