import os
import shutil
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr

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


def processar_fala(arquivo_audio, idioma_selecionado, modelo_selecionado, tipo_saida):
    if not arquivo_audio:
        return "Por favor, envie um arquivo de áudio antes de clicar.", None

    pasta_gtemp = None
    try:
        # Estrutura de pastas otimizada para o Linux do ambiente virtual do Google (/content/)
        pasta_output = "/content/output"
        pasta_gtemp = "/content/gtemp"
        os.makedirs(pasta_output, exist_ok=True)
        os.makedirs(pasta_gtemp, exist_ok=True)

        nome_arquivo = os.path.basename(arquivo_audio)
        caminho_local_audio = os.path.join(pasta_gtemp, nome_arquivo)
        shutil.copy(arquivo_audio, caminho_local_audio)

        nome_sem_extensao, _ = os.path.splitext(nome_arquivo)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_final_unico = f"{nome_sem_extensao}_{timestamp}"
        
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        tag_modelo = MODELOS.get(modelo_selecionado, "small")
        
        # Carrega o modelo sob demanda
        modelo = carregar_modelo_sob_demanda(tag_modelo)
        
        # fp16=True aproveita o poder de aceleração por hardware da GPU gratuita do Colab
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=True)

        if tipo_saida == "SRT":
            gravador_srt = get_writer("srt", pasta_output)
            gravador_srt(resultado, nome_final_unico, {"max_line_width": None, "max_line_count": None, "highlight_words": False})
            caminho_final = os.path.join(pasta_output, f"{nome_final_unico}.srt")
            mensagem = f"Sucesso! Legenda SRT gerada na nuvem."
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
            mensagem = f"Sucesso! Texto em parágrafos gerado na nuvem."

        return mensagem, caminho_final
    except Exception as e:
        return f"Erro no processamento da nuvem: {str(e)}", None
    finally:
        # Garante a limpeza do ambiente virtual para não acumular arquivos repetidos no Colab
        if pasta_gtemp and os.path.exists(pasta_gtemp):
            shutil.rmtree(pasta_gtemp)


# Interface gráfica do ambiente de Nuvem
with gr.Blocks(title="Gerador de Legendas SRT & TXT Nuvem") as app:
    gr.Markdown("# Gerador Automático de Áudio para Texto (Nuvem / Colab)")
    gr.Markdown("Rode o Whisper utilizando os servidores dedicados e gratuitos do Google de forma veloz.")
    
    with gr.Row():
        with gr.Column():
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="Selecione ou arraste seu áudio")
            input_idioma = gr.Dropdown(choices=list(IDIOMAS.keys()), value="Português", label="Idioma do áudio")
            
            # Novo seletor de modelos idêntico ao local
            input_modelo = gr.Dropdown(
                choices=list(MODELOS.keys()), 
                value="Turbo (Máxima Precisão & Velocidade - Recomendado no Colab)", 
                label="Qual modelo de Inteligência Artificial deseja usar?"
            )
            
            gr.Markdown(
                """
                > 💡 **Dica de Uso no Colab:**
                > Como você está utilizando o hardware do Google, fique totalmente livre para selecionar o modelo **Turbo**. Ele fornecerá uma precisão espetacular com tempos de resposta curtíssimos sem consumir nada do seu hardware físico!
                """
            )
            
            with gr.Row():
                botao_srt = gr.Button("Gerar Legenda .SRT", variant="primary")
                botao_txt = gr.Button("Transcrever para .TXT", variant="secondary")
            
        with gr.Column():
            output_status = gr.Textbox(label="Status do Processamento", interactive=False)
            output_arquivo = gr.File(label="Baixe seu arquivo aqui")

    # Passagem correta dos argumentos organizando dinamicamente
    botao_srt.click(fn=lambda a, i, m: processar_fala(a, i, m, "SRT"), inputs=[input_audio, input_idioma, input_modelo], outputs=[output_status, output_arquivo])
    botao_txt.click(fn=lambda a, i, m: processar_fala(a, i, m, "TXT"), inputs=[input_audio, input_idioma, input_modelo], outputs=[output_status, output_arquivo])

# share=True gera obrigatoriamente o link temporário público do Gradio no console do Colab
if __name__ == "__main__":
    app.launch(share=True, debug=True)