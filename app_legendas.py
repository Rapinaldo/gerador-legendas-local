import os
import shutil
import whisper
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

def processar_legenda_local(arquivo_audio, idioma_selecionado):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar em gerar.", None

    try:
        # 1. Configura as pastas locais no seu drive de dados (H:)
        pasta_raiz = os.path.dirname(os.path.abspath(__file__))
        pasta_output = os.path.join(pasta_raiz, "output")
        pasta_gtemp = os.path.join(pasta_output, "gtemp")
        os.makedirs(pasta_gtemp, exist_ok=True)

        # 2. Copia o áudio para a sua pasta gtemp local no drive H:
        nome_arquivo = os.path.basename(arquivo_audio)
        caminho_local_audio = os.path.join(pasta_gtemp, nome_arquivo)
        shutil.copy(arquivo_audio, caminho_local_audio)
        
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        print(f"Processando o arquivo localmente: {caminho_local_audio} no idioma: {idioma_selecionado}")
        
        # 3. O Whisper trabalha usando o arquivo localizado na unidade de dados (H:)
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        # Configura o gravador de SRT na pasta output
        gravador_srt = get_writer("srt", pasta_output)
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        
        opcoes = {
            "max_line_width": None,
            "max_line_count": None,
            "highlight_words": False
        }

        # Gera o arquivo .srt utilizando a variável correta
        gravador_srt(resultado, nome_sem_extensao, opcoes)
        caminho_final_srt = os.path.join(pasta_output, f"{nome_sem_extensao}.srt")
        
        # NOTA: Removemos o os.remove() daqui de dentro para não quebrar o protocolo HTTP do Gradio.
        
        mensagem_sucesso = f"Sucesso! Legenda ({idioma_selecionado}) gerada com êxito.\nSalva em: output/{nome_sem_extensao}.srt"
        return mensagem_sucesso, caminho_final_srt
        
    except Exception as e:
        return f"Ocorreu um erro durante o processamento: {str(e)}", None

# Interface gráfica
with gr.Blocks(title="Gerador de Legendas SRT Local") as app:
    gr.Markdown("# Gerador Automático de Legendas (.SRT) - Multi-idiomas")
    gr.Markdown("Envie seu arquivo de áudio, escolha o idioma falado e clique no botão para gerar a legenda.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Arraste ou selecione seu áudio (MP3/WAV)")
            
            input_idioma = gr.Dropdown(
                choices=list(IDIOMAS.keys()), 
                value="Português", 
                label="Qual o idioma falado no áudio?"
            )
            
            botao_gerar = gr.Button("Gerar Legenda .SRT", variant="primary")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe sua legenda .SRT aqui")

    botao_gerar.click(
        fn=processar_legenda_local,
        inputs=[input_audio, input_idioma],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(inbrowser=True, share=False)