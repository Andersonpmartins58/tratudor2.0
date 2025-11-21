# Screen Translator 2.0

Um tradutor de tela rápido, modular e leve, projetado para rodar em segundo plano e sobrepor jogos e aplicações em tela cheia.

## Funcionalidades

*   **Leve e Rápido:** Utiliza `mss` para captura de tela de alta performance.
*   **Não Intrusivo:** Roda na bandeja do sistema (System Tray).
*   **Overlay Transparente:** Interface de seleção que funciona sobre jogos (modo janela sem bordas ou tela cheia em alguns casos).
*   **OCR e Tradução:** Integração com Tesseract OCR e Google Translate.
*   **Atalhos:** Acionamento rápido via teclado.

## Pré-requisitos

1.  **Python 3.8+** instalado.
2.  **Tesseract OCR** instalado.
    *   Baixe e instale o [Tesseract OCR para Windows](https://github.com/UB-Mannheim/tesseract/wiki).
    *   Anote o caminho da instalação (padrão: `C:\Program Files\Tesseract-OCR\tesseract.exe`).

## Instalação

1.  Clone este repositório ou baixe os arquivos.
2.  Abra o terminal na pasta do projeto.
3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configuração:**
    *   Abra o arquivo `config.py`.
    *   Verifique se `TESSERACT_CMD` aponta para o local correto onde você instalou o Tesseract.

## Como Executar

### Opção 1: Atalho Rápido (Recomendado)
Dê dois cliques no arquivo **`run_app.bat`**.
*   O aplicativo iniciará silenciosamente.
*   Verifique o ícone (quadrado azul e branco) na bandeja do sistema (perto do relógio).

### Opção 2: Via Terminal
Se preferir ver logs de erro ou execução:
```bash
python main.py
```

## Como Usar

1.  Certifique-se que o app está rodando (ícone na bandeja).
2.  Pressione o atalho **`Ctrl + Alt + T`**.
3.  A tela ficará escurecida. Clique e arraste o mouse para selecionar a área que contém o texto.
4.  Solte o mouse.
5.  Uma janela aparecerá com o texto original extraído e a tradução.

## Estrutura do Projeto

*   `main.py`: Gerenciamento da aplicação e Tray Icon.
*   `overlay.py`: Interface gráfica de seleção de área.
*   `translator_service.py`: Serviço de OCR e Tradução (roda em background).
*   `config.py`: Arquivo de configurações.
*   `run_app.bat`: Script de inicialização facilitada.
