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
    def __init__(self, master, original_text, translated_text, img, x, y, w, h):
        self.root = tk.Toplevel(master)
        self.root.title("Tradução")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True) # Sem bordas
        
        # Posicionar exatamente sobre a área selecionada
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg='black')
        
        # Preparar imagem de fundo (Blur)
        if img:
            # Aplicar blur para esconder o texto original mas manter as cores
            blurred_img = img.filter(ImageFilter.GaussianBlur(radius=15))
            self.photo = ImageTk.PhotoImage(blurred_img)
        else:
            self.photo = None

        # Canvas para desenhar imagem e texto
        self.canvas = tk.Canvas(self.root, width=w, height=h, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)
        
        # Desenhar imagem de fundo
        if self.photo:
            self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        
        # Adicionar um retângulo semi-transparente escuro para melhorar contraste
        # Como Tkinter Canvas não suporta alpha em retângulos nativamente de forma fácil,
        # vamos criar uma imagem semi-transparente preta do tamanho da janela.
        self.dark_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 160)) # 160/255 opacidade
        self.dark_photo = ImageTk.PhotoImage(self.dark_overlay)
        self.canvas.create_image(0, 0, image=self.dark_photo, anchor='nw')
        
        # Desenhar Texto Traduzido
        # Usar sombra preta para legibilidade em qualquer fundo
        font_spec = (Config.FONT_FAMILY, Config.FONT_SIZE, 'bold')
        
        # Ajustar alinhamento para esquerda (nw) para manter formatação de listas
        padding_x = 10
        padding_y = 10
        
        # Sombra
        self.canvas.create_text(padding_x + 1, padding_y + 1, text=translated_text, font=font_spec, fill="black", width=w-(padding_x*2), justify='left', anchor='nw')
        # Texto Principal
        self.canvas.create_text(padding_x, padding_y, text=translated_text, font=font_spec, fill="white", width=w-(padding_x*2), justify='left', anchor='nw')

        # Botão de fechar (desenhado no canvas)
        close_btn = self.canvas.create_text(w-15, 15, text="×", fill="#ff5555", font=("Arial", 16, "bold"))
        self.canvas.tag_bind(close_btn, "<Button-1>", lambda e: self.root.destroy())
        
        # Fechar com ESC
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # Permitir arrastar a janela
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        
        self.x = 0
        self.y = 0

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

