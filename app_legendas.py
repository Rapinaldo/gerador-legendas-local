import os
import shutil
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr

# Carrega o modelo 'small' na memória
print("Carregando o modelo Whisper... Isso pode levar um instante.")
modelo = whisper.load_model("small")
print("Modelo pronto para uso!")

# Mapeamento de idiomas amigáveis
IDIOMAS = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es",
    "Francês": "fr",
    "Italiano": "it",
    "Alemão": "de",
    "Japonês": "ja"
}

def preparar_audio_local(arquivo_audio):
    """Função auxiliar para criar as pastas e copiar o áudio para o drive H:"""
    pasta_raiz = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(pasta_raiz, "output")
    pasta_gtemp = os.path.join(pasta_output, "gtemp")
    os.makedirs(pasta_gtemp, exist_ok=True)

    nome_arquivo = os.path.basename(arquivo_audio)
    caminho_local_audio = os.path.join(pasta_gtemp, nome_arquivo)
    shutil.copy(arquivo_audio, caminho_local_audio)
    
    return pasta_output, nome_arquivo, caminho_local_audio


def gerir_legenda_srt(arquivo_audio, idioma_selecionado):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    try:
        pasta_output, nome_arquivo, caminho_local_audio = preparar_audio_local(arquivo_audio)
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        
        print(f"[SRT] Processando arquivo: {caminho_local_audio} em {idioma_selecionado}")
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        # Gera o ID único baseado em data e hora atual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Configura o gravador de SRT na pasta output
        gravador_srt = get_writer("srt", pasta_output)
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        
        # Junta o nome original do áudio com o ID único
        nome_final_unico = f"{nome_sem_extensao}_{timestamp}"
        
        opcoes = {
            "max_line_width": None,
            "max_line_count": None,
            "highlight_words": False
        }

        # O Whisper gera o arquivo usando o nome único
        gravador_srt(resultado, nome_final_unico, opcoes)
        caminho_final_srt = os.path.join(pasta_output, f"{nome_final_unico}.srt")
        
        mensagem_sucesso = f"Sucesso! Legenda SRT gerada com êxito.\nSalva em: output/{nome_final_unico}.srt"
        return mensagem_sucesso, caminho_final_srt
        
    except Exception as e:
        return f"Ocorreu um erro durante o processamento SRT: {str(e)}", None


def gerir_texto_puro(arquivo_audio, idioma_selecionado):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    try:
        pasta_output, nome_arquivo, caminho_local_audio = preparar_audio_local(arquivo_audio)
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        
        print(f"[TXT] Transcrevendo texto estruturado: {caminho_local_audio} em {idioma_selecionado}")
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        # Acessa os segmentos individuais de fala capturados pelo Whisper
        segmentos = resultado.get("segments", [])
        
        paragrafos = []
        bloco_atual = []
        
        for i, seg in enumerate(segmentos):
            texto_segmento = seg.get("text", "").strip()
            if not texto_segmento:
                continue
                
            bloco_atual.append(texto_segmento)
            
            # Regra para criar parágrafo:
            termina_com_ponto = texto_segmento.endswith(('.', '!', '?'))
            if (termina_com_ponto and len(bloco_atual) >= 3) or (i == len(segmentos) - 1):
                paragrafos.append(" ".join(bloco_atual))
                bloco_atual = []
        
        texto_formatado = "\n\n".join(paragrafos)
        if not texto_formatado:
            texto_formatado = resultado.get("text", "").strip()
        
        # Gera o ID único baseado em data e hora atual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define o nome e caminho único para o arquivo .txt
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        nome_final_unico = f"{nome_sem_extensao}__{timestamp}"
        caminho_final_txt = os.path.join(pasta_output, f"{nome_final_unico}.txt")
        
        # Grava o arquivo de texto com a nova formatação profissional
        with open(caminho_final_txt, "w", encoding="utf-8") as f:
            f.write(texto_formatado)
            
        mensagem_sucesso = f"Sucesso! Texto estruturado em parágrafos com êxito.\nSalva em: output/{nome_final_unico}.txt"
        return mensagem_sucesso, caminho_final_txt
        
    except Exception as e:
        return f"Ocorreu um erro durante a transcrição de texto: {str(e)}", None


# Interface gráfica
with gr.Blocks(title="Gerador de Legendas SRT & TXT Local") as app:
    gr.Markdown("# Gerador Automático de Áudio para Texto - Local")
    gr.Markdown("Envie seu arquivo de áudio, escolha o idioma falado e selecione a ação desejada abaixo.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Arraste ou selecione seu áudio (MP3/WAV)")
            
            input_idioma = gr.Dropdown(
                choices=list(IDIOMAS.keys()), 
                value="Português", 
                label="Qual o idioma falado no áudio?"
            )
            
            with gr.Row():
                botao_srt = gr.Button("Gerar Legenda .SRT", variant="primary")
                botao_txt = gr.Button("Transcrever para .TXT", variant="secondary")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe seu arquivo gerado aqui")

    botao_srt.click(
        fn=gerir_legenda_srt,
        inputs=[input_audio, input_idioma],
        outputs=[output_status, output_arquivo]
    )

    botao_txt.click(
        fn=gerir_texto_puro,
        inputs=[input_audio, input_idioma],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(inbrowser=True, share=False)