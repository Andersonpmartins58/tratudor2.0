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
            # output_type='dict' retorna um dicionário com listas
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            lines = {}
            
            # Agrupar palavras em linhas
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0: # Filtrar confiança baixa/espaços vazios
                    text = data['text'][i].strip()
                    if not text:
                        continue
                        
                    # Chave única para a linha: block_page_par_line
                    key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                    
                    if key not in lines:
                        lines[key] = {
                            'text': [],
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'right': data['left'][i] + data['width'][i],
                            'bottom': data['top'][i] + data['height'][i]
                        }
                    else:
                        # Atualizar limites da caixa da linha
                        l = lines[key]
                        l['text'].append(text)
                        l['left'] = min(l['left'], data['left'][i])
                        l['top'] = min(l['top'], data['top'][i])
                        l['right'] = max(l['right'], data['left'][i] + data['width'][i])
                        l['bottom'] = max(l['bottom'], data['top'][i] + data['height'][i])
            
            if not lines:
                callback([], [], img)
                return

            # Preparar texto para tradução em lote
            sorted_keys = sorted(lines.keys())
            text_blocks = []
            raw_texts = []
            
            for key in sorted_keys:
                line_data = lines[key]
                full_text = " ".join(line_data['text']) # Juntar palavras da linha
                raw_texts.append(full_text)
                
                # Calcular largura e altura final da linha
                w_line = line_data['right'] - line_data['left']
                h_line = line_data['bottom'] - line_data['top']
                
                text_blocks.append({
                    'original': full_text,
                    'x': line_data['left'],
                    'y': line_data['top'],
                    'w': w_line,
                    'h': h_line
                })

            # Traduzir tudo de uma vez (juntando com quebra de linha)
            # Isso economiza chamadas de API e geralmente mantém a estrutura
            full_payload = "\n".join(raw_texts)
            translated_payload = self.translator.translate(full_payload)
            
            if translated_payload:
                translated_lines = translated_payload.split('\n')
                
                # Atribuir traduções de volta aos blocos
                # Nota: O tradutor pode mudar o número de linhas, então precisamos ser cuidadosos.
                # Se o número bater, ótimo. Se não, tentamos mapear ou fallback.
                
                if len(translated_lines) == len(text_blocks):
                    for i, block in enumerate(text_blocks):
                        block['translated'] = translated_lines[i]
                else:
                    # Fallback simples se as linhas não baterem (raro com Google Translate em textos curtos)
                    # Vamos tentar distribuir ou apenas usar o texto original se der erro
                    print("Aviso: Número de linhas traduzidas difere do original.")
                    # Tentar mapear pelo índice até onde der
                    for i, block in enumerate(text_blocks):
                        if i < len(translated_lines):
                            block['translated'] = translated_lines[i]
                        else:
                            block['translated'] = block['original'] # Fallback
            else:
                # Se falhar a tradução, usa o original
                for block in text_blocks:
                    block['translated'] = block['original']

            callback(text_blocks, None, img) # Passamos os blocos estruturados

        except Exception as e:
            print(f"Erro no worker: {e}")
            callback([], None, None)
