import os
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr

# Carrega o modelo 'small' na memória (No Colab com GPU T4 gratuita, isso roda voando!)
print("Carregando o modelo Whisper...")
modelo = whisper.load_model("small")
print("Modelo pronto!")

IDIOMAS = {
    "Português": "pt", "Inglês": "en", "Espanhol": "es", 
    "Francês": "fr", "Italiano": "it", "Alemão": "de", "Japonês": "ja"
}

def processar_fala(arquivo_audio, idioma_selecionado, tipo_saida):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    try:
        # No Colab, criamos uma pasta simples no diretório virtual /content/output
        pasta_output = "/content/output"
        os.makedirs(pasta_output, exist_ok=True)

        nome_arquivo = os.path.basename(arquivo_audio)
        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_final_unico = f"{nome_sem_extensao}_{timestamp}"
        
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        resultado = modelo.transcribe(arquivo_audio, language=codigo_idioma, fp16=True) # fp16=True usa o poder da GPU do Colab

        if tipo_saida == "SRT":
            gravador_srt = get_writer("srt", pasta_output)
            gravador_srt(resultado, nome_final_unico, {"max_line_width": None, "max_line_count": None, "highlight_words": False})
            caminho_final = os.path.join(pasta_output, f"{nome_final_unico}.srt")
            mensagem = f"Sucesso! Legenda SRT gerada."
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
            caminho_final = os.path.join(pasta_output, f"{nome_final_unico}.txt")
            with open(caminho_final, "w", encoding="utf-8") as f:
                f.write(texto_formatado)
            mensagem = f"Sucesso! Texto em parágrafos gerado."

        return mensagem, caminho_final
    except Exception as e:
        return f"Erro no processamento: {str(e)}", None

# Interface gráfica adaptada
with gr.Blocks(title="Gerador de Legendas SRT & TXT") as app:
    gr.Markdown("# Gerador Automático de Áudio para Texto (Nuvem / Colab)")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Selecione seu áudio")
            input_idioma = gr.Dropdown(choices=list(IDIOMAS.keys()), value="Português", label="Idioma do áudio")
            
            with gr.Row():
                botao_srt = gr.Button("Gerar Legenda .SRT", variant="primary")
                botao_txt = gr.Button("Transcrever para .TXT", variant="secondary")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status", interactive=False)
            output_arquivo = gr.File(label="Baixe seu arquivo aqui")

    # Passamos um argumento extra indicando o tipo de arquivo para a mesma função economizar memória
    botao_srt.click(fn=lambda a, i: processar_fala(a, i, "SRT"), inputs=[input_audio, input_idioma], outputs=[output_status, output_arquivo])
    botao_txt.click(fn=lambda a, i: processar_fala(a, i, "TXT"), inputs=[input_audio, input_idioma], outputs=[output_status, output_arquivo])

# IMPORTANTE: No Colab precisamos ativar o share=True para gerar o link público acessível
if __name__ == "__main__":
    app.launch(share=True, debug=True)