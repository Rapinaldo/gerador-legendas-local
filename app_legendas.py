import os
import shutil
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr
from deep_translator import GoogleTranslator  # Nova biblioteca para tradução reversa

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

# Dicionário de modelos expandido
MODELOS = {
    "Tiny (Ultra Rápido - Menor Precisão)": "tiny",
    "Base (Rápido - Boa Precisão)": "base",
    "Small (Equilibrado - Recomendado Geral)": "small",
    "Medium (Alta Precisão - Exige +5GB VRAM)": "medium",
    "Turbo (Máxima Precisão & Velocidade - Exige +8GB VRAM)": "turbo"
}

# Variável global para armazenar o modelo carregado e evitar recarregamentos desnecessários
modelo_atual = None
nome_modelo_carregado = None

def carregar_modelo_sob_demanda(nome_modelo):
    """Carrega o modelo selecionado apenas se ele já não estiver na memória."""
    global modelo_atual, nome_modelo_carregado
    
    if nome_modelo == "turbo":
        nome_modelo = "large-v3-turbo"
        
    if modelo_atual is None or nome_modelo_carregado != nome_modelo:
        print(f"Carregando o modelo Whisper '{nome_modelo}' na memória... Isso pode levar um instante.")
        modelo_atual = whisper.load_model(nome_modelo)
        nome_modelo_carregado = nome_modelo
        print(f"Modelo '{nome_modelo}' pronto para uso!")
    
    return modelo_atual


def preparar_audio_local(arquivo_audio):
    """Função auxiliar para criar as pastas e copiar o áudio para o drive H:"""
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_raiz, "output")
    pasta_gtemp = os.path.join(pasta_output, "gtemp")
    os.makedirs(pasta_gtemp, exist_ok=True)

    nome_arquivo = os.path.basename(arquivo_audio)
    caminho_local_audio = os.path.join(pasta_gtemp, nome_arquivo)
    shutil.copy(arquivo_audio, caminho_local_audio)
    
    return pasta_output, pasta_gtemp, nome_arquivo, caminho_local_audio


def limpar_pasta_temporaria(pasta_gtemp):
    """Remove com segurança todos os arquivos deixados na pasta gtemp."""
    try:
        if os.path.exists(pasta_gtemp):
            shutil.rmtree(pasta_gtemp)
            print("[Limpeza] Pasta temporária 'gtemp' limpa com sucesso.")
    except Exception as e:
        print(f"[Aviso] Não foi possível limpar a pasta temporária: {str(e)}")


def gerir_legenda_srt(arquivo_audio, idioma_selecionado, modelo_selecionado):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    pasta_gtemp = None
    try:
        pasta_output, pasta_gtemp, nome_arquivo, caminho_local_audio = preparar_audio_local(arquivo_audio)
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        tag_modelo = MODELOS.get(modelo_selecionado, "small")
        
        modelo = carregar_modelo_sob_demanda(tag_modelo)
        
        print(f"[SRT] Processando com modelo {tag_modelo.upper()}: {caminho_local_audio} em {idioma_selecionado}")
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gravador_srt = get_writer("srt", pasta_output)
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        nome_final_unico = f"{nome_sem_extensao}_{timestamp}"
        
        opcoes = {"max_line_width": None, "max_line_count": None, "highlight_words": False}
        gravador_srt(resultado, nome_final_unico, opcoes)
        caminho_final_srt = os.path.join(pasta_output, f"{nome_final_unico}.srt")
        
        mensagem_sucesso = f"Sucesso! Legenda SRT gerada com êxito.\nSalva em: output/{nome_final_unico}.srt"
        return mensagem_sucesso, caminho_final_srt
        
    except Exception as e:
        return f"Ocorreu um erro durante o processamento SRT: {str(e)}", None
    finally:
        if pasta_gtemp:
            limpar_pasta_temporaria(pasta_gtemp)


def gerir_texto_puro(arquivo_audio, idioma_selecionado, modelo_selecionado, tarefa="transcrever"):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    pasta_gtemp = None
    try:
        pasta_output, pasta_gtemp, nome_arquivo, caminho_local_audio = preparar_audio_local(arquivo_audio)
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        tag_modelo = MODELOS.get(modelo_selecionado, "small")
        
        modelo = carregar_modelo_sob_demanda(tag_modelo)
        
        # Fluxo de Tradução Nativa para o Inglês (Whisper nativo)
        if tarefa == "traduzir_en":
            print(f"[TRADUÇÃO EN] Traduzindo áudio com modelo {tag_modelo.upper()} para o Inglês...")
            resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, task="translate", fp16=False)
        else:
            # Transcrição normal (seja em português, inglês, etc.)
            print(f"[TXT] Transcrevendo com modelo {tag_modelo.upper()}: {caminho_local_audio} em {idioma_selecionado}")
            resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        segmentos = resultado.get("segments", [])
        paragrafos = []
        bloco_atual = []
        
        for i, seg in enumerate(segmentos):
            texto_segmento = seg.get("text", "").strip()
            if not texto_segmento:
                continue
            bloco_atual.append(texto_segmento)
            termina_com_ponto = texto_segmento.endswith(('.', '!', '?'))
            if (termina_com_ponto and len(bloco_atual) >= 3) or (i == len(segmentos) - 1):
                paragrafos.append(" ".join(bloco_atual))
                bloco_atual = []
        
        # Se a tarefa for traduzir para o Português (Tradução Reversa via deep-translator)
        if tarefa == "traduzir_pt" and paragrafos:
            print("[TRADUÇÃO PT] Convertendo blocos de texto estruturados para o Português...")
            paragrafos_traduzidos = []
            tradutor = GoogleTranslator(source='auto', target='pt')
            for p in paragrafos:
                # Traduz bloco por bloco para manter a fidelidade e formatação limpa
                p_traduzido = tradutor.translate(p)
                paragrafos_traduzidos.append(p_traduzido)
            paragrafos = paragrafos_traduzidos

        texto_formatado = "\n\n".join(paragrafos)
        if not texto_formatado and resultado.get("text", ""):
            texto_bruto = resultado.get("text", "").strip()
            if tarefa == "traduzir_pt":
                texto_formatado = GoogleTranslator(source='auto', target='pt').translate(texto_bruto)
            else:
                texto_formatado = texto_bruto
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        
        # Ajuste dinâmico de sufixos conforme a tarefa executada
        sufixos = {"transcrever": "", "traduzir_en": "_traducao_en", "traduzir_pt": "_traducao_pt"}
        nome_final_unico = f"{nome_sem_extensao}{sufixos.get(tarefa, '')}_{timestamp}"
        caminho_final_txt = os.path.join(pasta_output, f"{nome_final_unico}.txt")
        
        with open(caminho_final_txt, "w", encoding="utf-8") as f:
            f.write(texto_formatado)
            
        mensagem_sucesso = f"Sucesso! Arquivo estruturado com êxito.\nSalvo em: output/{nome_final_unico}.txt"
        return mensagem_sucesso, caminho_final_txt
        
    except Exception as e:
        return f"Ocorreu um erro durante o processamento de texto: {str(e)}", None
    finally:
        if pasta_gtemp:
            limpar_pasta_temporaria(pasta_gtemp)


# Interface gráfica expandida
with gr.Blocks(title="Gerador de Legendas SRT & TXT Local") as app:
    gr.Markdown("# Gerador Automático de Áudio para Texto - Local")
    gr.Markdown("Envie seu arquivo de áudio, configure os parâmetros de inteligência e selecione a ação desejada.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Arraste ou selecione seu áudio (MP3/WAV)")
            
            input_idioma = gr.Dropdown(
                choices=list(IDIOMAS.keys()), 
                value="Português", 
                label="Qual o idioma original falado no áudio?"
            )
            
            input_modelo = gr.Dropdown(
                choices=list(MODELOS.keys()),
                value="Small (Equilibrado - Recomendado Geral)",
                label="Qual modelo de Inteligência Artificial deseja usar?"
            )
            
            gr.Markdown(
                """
                > ⚠️ **Nota de Desempenho (VRAM):**
                > * Modelos **Tiny, Base e Small** rodam de forma leve na maioria dos computadores modernos.
                > * Modelos **Medium e Turbo** oferecem precisão avançada e contextual superior, porém **exigem uma placa de vídeo dedicada forte (recomenda-se GPUs de 8GB a 12GB de VRAM)**. Se o seu sistema não possuir os requisitos, o processamento local poderá falhar ou ficar extremamente lento.
                """
            )
            
            # Grid de botões organizados de forma limpa e profissional
            with gr.Row():
                botao_srt = gr.Button("Gerar Legenda .SRT", variant="primary")
                botao_txt = gr.Button("Transcrever para .TXT", variant="secondary")
            with gr.Row():
                botao_traducao_en = gr.Button("Traduzir para Inglês (.TXT)", variant="stop")
                botao_traducao_pt = gr.Button("Traduzir para Português (.TXT)", variant="stop")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe seu arquivo gerado aqui")

    # Vinculos das ações da interface passando as tarefas dinâmicas
    botao_srt.click(
        fn=gerir_legenda_srt,
        inputs=[input_audio, input_idioma, input_modelo],
        outputs=[output_status, output_arquivo]
    )

    botao_txt.click(
        fn=lambda a, i, m: gerir_texto_puro(a, i, m, tarefa="transcrever"),
        inputs=[input_audio, input_idioma, input_modelo],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_en.click(
        fn=lambda a, i, m: gerir_texto_puro(a, i, m, tarefa="traduzir_en"),
        inputs=[input_audio, input_idioma, input_modelo],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_pt.click(
        fn=lambda a, i, m: gerir_texto_puro(a, i, m, tarefa="traduzir_pt"),
        inputs=[input_audio, input_idioma, input_modelo],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(inbrowser=True, share=False)