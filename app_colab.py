import os
import shutil
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr

# Tenta importar ou instala dinamicamente a biblioteca de tradução na nuvem
try:
    from deep_translator import GoogleTranslator
except ImportError:
    import subprocess
    import sys
    print("[Ambiente] Instalando deep-translator no ecossistema do Colab...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "deep-translator"])
    from deep_translator import GoogleTranslator

# Dicionário de idiomas amigáveis
IDIOMAS = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es",
    "Francês": "fr",
    "Italiano": "it",
    "Alemão": "de",
    "Japonês": "ja"
}

# Dicionário de modelos expandido (Alinhado com a versão Local)
MODELOS = {
    "Tiny (Ultra Rápido - Menor Precisão)": "tiny",
    "Base (Rápido - Boa Precisão)": "base",
    "Small (Equilibrado - Recomendado Geral)": "small",
    "Medium (Alta Precisão)": "medium",
    "Turbo (Máxima Precisão & Velocidade - Recomendado no Colab)": "turbo"
}

# Variável global para gerenciar a memória no Colab
modelo_atual = None
nome_modelo_carregado = None

def carregar_modelo_sob_demanda(nome_modelo):
    """Carrega o modelo selecionado apenas se ele já não estiver na memória."""
    global modelo_atual, nome_modelo_carregado
    
    if nome_modelo == "turbo":
        nome_modelo = "large-v3-turbo"
        
    if modelo_atual is None or nome_modelo_carregado != nome_modelo:
        print(f"Carregando o modelo Whisper '{nome_modelo}' na nuvem... Isso leva apenas alguns segundos.")
        modelo_atual = whisper.load_model(nome_modelo)
        nome_modelo_carregado = nome_modelo
        print(f"Modelo '{nome_modelo}' pronto no ambiente Google Colab!")
    
    return modelo_atual


def processar_geral(arquivo_audio, idioma_selecionado, modelo_selecionado, formato_saida, tarefa):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    pasta_gtemp = None
    try:
        # Estrutura de pastas otimizada para o Linux do Colab
        pasta_output = "/content/output"
        pasta_gtemp = "/content/gtemp"
        os.makedirs(pasta_output, exist_ok=True)
        os.makedirs(pasta_gtemp, exist_ok=True)

        nome_arquivo = os.path.basename(arquivo_audio)
        caminho_local_audio = os.path.join(pasta_gtemp, nome_arquivo)
        shutil.copy(arquivo_audio, caminho_local_audio)

        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        tag_modelo = MODELOS.get(modelo_selecionado, "small")
        
        # Carrega o modelo sob demanda
        modelo = carregar_modelo_sob_demanda(tag_modelo)
        
        # Define os parâmetros de transcrição nativa do Whisper (fp16=True aproveita a GPU do Colab)
        argumentos_transcribe = {"language": codigo_idioma, "fp16": True}
        if tarefa == "traduzir_en":
            argumentos_transcribe["task"] = "translate"
            print(f"[WHISPER NUVEM] Traduzindo áudio com modelo {tag_modelo.upper()} para o Inglês...")
        else:
            print(f"[WHISPER NUVEM] Processando áudio com modelo {tag_modelo.upper()} no idioma {idioma_selecionado}...")
            
        resultado = modelo.transcribe(caminho_local_audio, **argumentos_transcribe)
        
        # Tradução Reversa para o Português (Texto global e segmentos SRT)
        if tarefa == "traduzir_pt":
            print("[TRADUTOR NUVEM] Traduzindo o conteúdo gerado para o Português...")
            tradutor = GoogleTranslator(source='auto', target='pt')
            
            if resultado.get("text"):
                resultado["text"] = tradutor.translate(resultado["text"])
            
            if "segments" in resultado:
                for seg in resultado["segments"]:
                    if seg.get("text", "").strip():
                        seg["text"] = tradutor.translate(seg["text"])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        
        sufixos = {"transcrever": "", "traduzir_en": "_traducao_en", "traduzir_pt": "_traducao_pt"}
        nome_base_final = f"{nome_sem_extensao}{sufixos.get(tarefa, '')}_{timestamp}"

        # --- GERAÇÃO DE LEGENDA (.SRT) ---
        if "SRT" in formato_saida:
            gravador_srt = get_writer("srt", pasta_output)
            opcoes = {"max_line_width": None, "max_line_count": None, "highlight_words": False}
            gravador_srt(resultado, nome_base_final, opcoes)
            caminho_final = os.path.join(pasta_output, f"{nome_base_final}.srt")
            mensagem_sucesso = f"Sucesso! Legenda SRT gerada na nuvem."
            
        # --- GERAÇÃO DE TEXTO PURO (.TXT) ---
        else:
            segmentos = resultado.get("segments", [])
            paragrafos = []
            bloco_atual = []
            
            for i, seg in enumerate(segmentos):
                texto_segmento = seg.get("text", "").strip()
                if not texto_segmento: continue
                bloco_atual.append(texto_segmento)
                if (texto_segmento.endswith(('.', '!', '?')) and len(bloco_atual) >= 3) or (i == len(segmentos) - 1):
                    paragrafos.append(" ".join(bloco_atual))
                    bloco_atual = []
            
            texto_formatado = "\n\n".join(paragrafos)
            if not texto_formatado:
                texto_formatado = resultado.get("text", "").strip()
                
            caminho_final = os.path.join(pasta_output, f"{nome_base_final}.txt")
            with open(caminho_final, "w", encoding="utf-8") as f:
                f.write(texto_formatado)
            mensagem_sucesso = f"Sucesso! Texto estruturado gerado na nuvem."

        return mensagem_sucesso, caminho_final
    except Exception as e:
        return f"Erro no processamento da nuvem: {str(e)}", None
    finally:
        if pasta_gtemp and os.path.exists(pasta_gtemp):
            shutil.rmtree(pasta_gtemp)


# Interface gráfica do ambiente de Nuvem (Sincronizada com o layout Local)
with gr.Blocks(title="Gerador de Legendas SRT & TXT Nuvem") as app:
    gr.Markdown("# Gerador Automático de Áudio para Texto (Nuvem / Colab)")
    gr.Markdown("Rode o Whisper utilizando os servidores dedicados e gratuitos do Google de forma veloz.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Selecione ou arraste seu áudio")
            input_idioma = gr.Dropdown(choices=list(IDIOMAS.keys()), value="Português", label="Idioma original falado no áudio")
            
            input_modelo = gr.Dropdown(
                choices=list(MODELOS.keys()), 
                value="Turbo (Máxima Precisão & Velocidade - Recomendado no Colab)", 
                label="Qual modelo de Inteligência Artificial deseja usar?"
            )
            
            input_formato = gr.Radio(
                choices=["Texto Estruturado (.TXT)", "Legenda SRT (.SRT)"], 
                value="Texto Estruturado (.TXT)", 
                label="Qual formato de arquivo final deseja gerar?"
            )
            
            gr.Markdown(
                """
                > 💡 **Dica de Uso no Colab:**
                > Como você está utilizando o hardware do Google, fique totalmente livre para selecionar o modelo **Turbo**. Ele fornecerá uma precisão espetacular com tempos de resposta curtíssimos sem consumir nada do seu hardware físico!
                """
            )
            
            with gr.Row():
                botao_normal = gr.Button("Transcrever Áudio (Original)", variant="primary")
            with gr.Row():
                botao_traducao_en = gr.Button("Traduzir para Inglês", variant="stop")
                botao_traducao_pt = gr.Button("Traduzir para Português", variant="stop")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe seu arquivo aqui")

    # Vinculos das ações da interface passando as tarefas dinâmicas
    botao_normal.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="transcrever"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_en.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_en"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_pt.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_pt"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(share=True, debug=True)