import tkinter as tk
from screeninfo import get_monitors
from config import Config

class SelectionOverlay:
    def __init__(self, on_selection_complete):
        self.on_selection_complete = on_selection_complete
        self.root = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None

    def show(self):
        self.root = tk.Tk()
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
        
        self.root.mainloop()

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
        
        # Ajustar para coordenadas globais se necessário (depende de como o tkinter mapeia em multi-monitor)
        # O winfo_rootx já deve compensar, mas vamos garantir que passamos coordenadas absolutas para o mss
        # Na verdade, como a janela cobre tudo começando de min_x/min_y, precisamos somar min_x/min_y
        
        monitors = get_monitors()
        min_global_x = min(m.x for m in monitors)
        min_global_y = min(m.y for m in monitors)
        
        final_x = x1 + min_global_x
        final_y = y1 + min_global_y
        
        if width > 10 and height > 10:
            self.on_selection_complete(final_x, final_y, width, height)

class ResultWindow:
    def __init__(self, original_text, translated_text):
        self.root = tk.Tk()
        self.root.title("Tradução")
        self.root.attributes('-topmost', True)
        
        # Posicionar perto do mouse ou no centro
        self.root.geometry("400x300")
        self.root.configure(bg=Config.BG_COLOR)
        
        # Texto Original
        lbl_orig = tk.Label(self.root, text="Original:", fg="#aaaaaa", bg=Config.BG_COLOR, font=(Config.FONT_FAMILY, 10))
        lbl_orig.pack(anchor='w', padx=10, pady=(10,0))
        
        txt_orig = tk.Text(self.root, height=4, bg="#333333", fg="white", borderwidth=0, font=(Config.FONT_FAMILY, Config.FONT_SIZE))
        txt_orig.insert('1.0', original_text)
        txt_orig.config(state='disabled')
        txt_orig.pack(fill='x', padx=10, pady=5)
        
        # Texto Traduzido
        lbl_trans = tk.Label(self.root, text="Tradução:", fg="#aaaaaa", bg=Config.BG_COLOR, font=(Config.FONT_FAMILY, 10))
        lbl_trans.pack(anchor='w', padx=10, pady=(10,0))
        
        txt_trans = tk.Text(self.root, height=6, bg="#333333", fg="#00ff00", borderwidth=0, font=(Config.FONT_FAMILY, Config.FONT_SIZE, 'bold'))
        txt_trans.insert('1.0', translated_text)
        txt_trans.config(state='disabled')
        txt_trans.pack(fill='both', expand=True, padx=10, pady=5)
        
        btn_close = tk.Button(self.root, text="Fechar", command=self.root.destroy, bg="#444444", fg="white", relief="flat")
        btn_close.pack(pady=10)
        
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.mainloop()
