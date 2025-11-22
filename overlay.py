import tkinter as tk
from screeninfo import get_monitors
from config import Config

class SelectionOverlay:
    def __init__(self, master, on_selection_complete):
        self.on_selection_complete = on_selection_complete
        self.master = master
        self.root = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None

    def show(self):
        # Usar Toplevel em vez de Tk para não conflitar com a root principal
        self.root = tk.Toplevel(self.master)
        self.root.attributes('-alpha', 0.3)  # Transparência
        self.root.attributes('-topmost', True) # Sempre no topo
        self.root.overrideredirect(True) # Sem bordas
        
        # Cobrir todos os monitores
        monitors = get_monitors()
        min_x = min(m.x for m in monitors)
        min_y = min(m.y for m in monitors)
        max_x = max(m.x + m.width for m in monitors)
        max_y = max(m.y + m.height for m in monitors)
        
        width = max_x - min_x
        height = max_y - min_y
        
        self.root.geometry(f"{width}x{height}+{min_x}+{min_y}")
        self.root.configure(bg='black')
        
        self.canvas = tk.Canvas(self.root, width=width, height=height, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.close())
        
        # Focar na janela para capturar o ESC
        self.root.focus_force()

    def close(self):
        if self.root:
            self.root.destroy()
            self.root = None

    def on_button_press(self, event):
        self.start_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        self.start_y = self.root.winfo_pointery() - self.root.winfo_rooty()
        
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2
        )

    def on_move_press(self, event):
        cur_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        cur_y = self.root.winfo_pointery() - self.root.winfo_rooty()
        
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.root.winfo_pointerx() - self.root.winfo_rootx()
        end_y = self.root.winfo_pointery() - self.root.winfo_rooty()
        
        self.close()
        
        # Calcular coordenadas reais da tela
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        
        monitors = get_monitors()
        min_global_x = min(m.x for m in monitors)
        min_global_y = min(m.y for m in monitors)
        
        final_x = x1 + min_global_x
        final_y = y1 + min_global_y
        
        if width > 10 and height > 10:
            self.on_selection_complete(final_x, final_y, width, height)

from PIL import Image, ImageTk, ImageFilter

class ResultWindow:
    def __init__(self, master, text_blocks, img, x, y, w, h, on_close=None):
        self.on_close = on_close
        self.root = tk.Toplevel(master)
        self.root.title("Tradução")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True) # Sem bordas
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg='black')
        
        self.w = w
        self.h = h
        
        # Canvas
        self.canvas = tk.Canvas(self.root, width=w, height=h, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)
        
        # Imagem de fundo (Original, sem blur, pois vamos cobrir apenas o texto)
        self.bg_image_id = self.canvas.create_image(0, 0, anchor='nw')
        
        if img:
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.bg_image_id, image=self.photo)
        
        # Desenhar blocos de texto
        self.draw_text_blocks(text_blocks)

        # Botão de fechar
        close_btn = self.canvas.create_text(w-15, 15, text="×", fill="#ff5555", font=("Arial", 16, "bold"))
        self.canvas.tag_bind(close_btn, "<Button-1>", lambda e: self.destroy())
        
        self.root.bind("<Escape>", lambda e: self.destroy())
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        
        self.x = 0
        self.y = 0

    def draw_text_blocks(self, text_blocks):
        # Limpar desenhos anteriores de texto (se houver update)
        self.canvas.delete("text_block")
        
        if not text_blocks:
            return

        for block in text_blocks:
            bx, by, bw, bh = block['x'], block['y'], block['w'], block['h']
            translated = block.get('translated', '')
            
            # Fundo do texto (para esconder o original)
            # Cor escura para contraste
            self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#2b2b2b", outline="", tags="text_block")
            
            # Texto com ajuste dinâmico de fonte e quebra de linha
            # Começar com um tamanho razoável
            font_size = Config.FONT_SIZE
            min_font_size = 8
            
            # Loop para reduzir fonte até caber na altura
            while font_size >= min_font_size:
                font_spec = (Config.FONT_FAMILY, font_size, 'bold')
                
                # Criar texto temporário para medir
                # width=bw faz o texto quebrar linha automaticamente
                temp_id = self.canvas.create_text(0, 0, text=translated, font=font_spec, width=bw, anchor='nw')
                bbox = self.canvas.bbox(temp_id)
                self.canvas.delete(temp_id)
                
                if not bbox:
                    break # Texto vazio ou erro
                    
                text_h = bbox[3] - bbox[1]
                
                # Se a altura do texto for menor ou igual à altura da caixa (com margem de erro), está bom
                if text_h <= bh + 5: # +5 de tolerância
                    break
                
                font_size -= 1
            
            # Desenhar texto final
            font_spec = (Config.FONT_FAMILY, font_size, 'bold')
            
            # Centralizar verticalmente e horizontalmente
            cx = bx + bw / 2
            cy = by + bh / 2
            
            self.canvas.create_text(cx, cy, text=translated, font=font_spec, fill="white", width=bw, justify='center', tags="text_block")

    def update_content(self, text_blocks, img):
        # Atualizar imagem de fundo se mudar
        if img:
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.itemconfig(self.bg_image_id, image=self.photo)
        
        self.draw_text_blocks(text_blocks)

    def destroy(self):
        if self.on_close:
            self.on_close()
        self.root.destroy()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

