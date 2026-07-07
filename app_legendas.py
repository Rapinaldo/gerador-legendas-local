import os
import whisper
from whisper.utils import get_writer
import gradio as gr

# Carrega o modelo 'small' na memória da sua GPU local
print("Carregando o modelo Whisper na GPU... Isso pode levar um instante.")
modelo = whisper.load_model("small")
print("Modelo pronto para uso!")

def processar_legenda_local(arquivo_audio):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar em gerar.", None

    try:
        print(f"Processando o arquivo: {arquivo_audio}")
        # Transcreve o áudio utilizando sua GPU local
        resultado = modelo.transcribe(arquivo_audio, language="pt")

        # Define a pasta atual do script para salvar o arquivo temporário
        pasta_destino = os.path.dirname(os.path.abspath(__file__))
        gravador_srt = get_writer("srt", pasta_destino)
        
        # Extrai o nome original para nomear o arquivo .SRT
        nome_base = os.path.basename(arquivo_audio)
        nome_sem_extensao, _ = os.path.splitext(nome_base)
        caminho_final_srt = os.path.join(pasta_destino, f"{nome_sem_extensao}.srt")

        # Grava a legenda na pasta local
        gravador_srt(resultado, caminho_final_srt, {})
        
        mensagem_sucesso = f"Sucesso! Legenda gerada com êxito.\nVocê pode baixar pelo navegador ou coletar direto na pasta do script."
        return mensagem_sucesso, caminho_final_srt
        
    except Exception as e:
        return f"Ocorreu um erro durante o processamento: {str(e)}", None

# Interface gráfica
with gr.Blocks(title="Gerador de Legendas SRT Local") as app:
    gr.Markdown("# Gerador Automático de Legendas (.SRT) - do Rapina")
    gr.Markdown("Envie seu arquivo de áudio e clique no botão. O arquivo final será disponibilizado para download e salvo na pasta deste script.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Arraste ou selecione seu áudio (MP3/WAV)")
            botao_gerar = gr.Button("Gerar Legenda .SRT", variant="primary")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe sua legenda .SRT aqui")

    botao_gerar.click(
        fn=processar_legenda_local,
        inputs=[input_audio],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    # Roda localmente e abre o navegador automaticamente (sem gerar link público share=False)
    app.launch(inbrowser=True, share=False)