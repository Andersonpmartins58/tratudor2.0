import os

class Config:
    # Configuração do Tesseract OCR
    # Se o tesseract não estiver no PATH do sistema, descomente a linha abaixo e ajuste o caminho:
    # TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # Idiomas
    SOURCE_LANG = 'auto'
    TARGET_LANG = 'pt' # Português
    
    # Atalho Global
    HOTKEY = 'ctrl+alt+t'
    
    # Configurações de UI
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 12
    BG_COLOR = "#2b2b2b"
    TEXT_COLOR = "#ffffff"
