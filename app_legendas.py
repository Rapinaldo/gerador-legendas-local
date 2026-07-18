import os
import shutil
import whisper
from datetime import datetime
from whisper.utils import get_writer
import gradio as gr
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

# Dicionário de modelos expandido
MODELOS = {
    "Tiny (Ultra Rápido - Menor Precisão)": "tiny",
    "Base (Rápido - Boa Precisão)": "base",
    "Small (Equilibrado - Recomendado Geral)": "small",
    "Medium (Alta Precisão - Exige +5GB VRAM)": "medium",
    "Turbo (Máxima Precisão & Velocidade - Exige +8GB VRAM)": "turbo"
}

# Variável global para armazenar o modelo carregado
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


def processar_geral(arquivo_audio, idioma_selecionado, modelo_selecionado, formato_saida, tarefa):
    if not arquivo_audio:
        return "⚠️ Por favor, envie um arquivo de áudio antes de clicar.", None

    pasta_gtemp = None
    try:
        pasta_output, pasta_gtemp, nome_arquivo, caminho_local_audio = preparar_audio_local(arquivo_audio)
        codigo_idioma = IDIOMAS.get(idioma_selecionado, "pt")
        tag_modelo = MODELOS.get(modelo_selecionado, "small")
        
        modelo = carregar_modelo_sob_demanda(tag_modelo)
        
        # Transcrição limpa e estável no idioma original para evitar conflitos na tarefa nativa do Whisper
        print(f"[WHISPER] Processando áudio original com modelo {tag_modelo.upper()} no idioma {idioma_selecionado}...")
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=False)
        
        # --- BLOCOS DE TRADUÇÃO VIA MOTOR EXTERNO (MUITO MAIS ESTÁVEL) ---
        if tarefa == "traduzir_en":
            print("[TRADUTOR] Convertendo o conteúdo gerado para o Inglês parágrafo por parágrafo...")
            tradutor = GoogleTranslator(source='auto', target='en')
            
            if resultado.get("text"):
                resultado["text"] = tradutor.translate(resultado["text"])
            if "segments" in resultado:
                for seg in resultado["segments"]:
                    if seg.get("text", "").strip():
                        seg["text"] = tradutor.translate(seg["text"])
                        
        elif tarefa == "traduzir_pt":
            print("[TRADUTOR] Convertendo o conteúdo gerado para o Português parágrafo por parágrafo...")
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
            mensagem_sucesso = f"✅ Sucesso! Legenda SRT gerada com êxito.\n📁 Salva em: output/{nome_base_final}.srt"
            
        # --- GERAÇÃO DE TEXTO PURO (.TXT) ---
        else:
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
            
            texto_formatated = "\n\n".join(paragrafos)
            if not texto_formatated:
                texto_formatated = resultado.get("text", "").strip()
                
            caminho_final = os.path.join(pasta_output, f"{nome_base_final}.txt")
            with open(caminho_final, "w", encoding="utf-8") as f:
                f.write(texto_formatated)
            mensagem_sucesso = f"✅ Sucesso! Texto estruturado com êxito.\n📁 Salvo em: output/{nome_base_final}.txt"
            
        return mensagem_sucesso, caminho_final
        
    except Exception as e:
        return f"❌ Ocorreu um erro durante o processamento: {str(e)}", None
    finally:
        if pasta_gtemp:
            limpar_pasta_temporaria(pasta_gtemp)


# --- CONFIGURAÇÃO VISUAL PREMIUM ---
tema_customizado = gr.themes.Soft(
    primary_hue="slate",
    secondary_hue="blue",
    neutral_hue="gray",
).set(
    body_background_fill="*neutral_950",
    block_background_fill="*neutral_900",
    block_label_text_color="*secondary_400",
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_500"
)

with gr.Blocks(theme=tema_customizado, title="Olho de Rapina - Whisper Studio") as app:
    
    gr.Markdown(
        """
        # 🎙️ Olho de Rapina — Whisper Studio Local
        *Transcreva áudios, gere legendas sincronizadas e faça traduções inteligentes usando inteligência artificial local.*
        """
    )
    
    with gr.Row():
        with gr.Column(scale=12):
            gr.Markdown("### 🛠️ Configurações do Processamento")
            
            input_audio = gr.Audio(
                sources=["upload"], 
                type="filepath", 
                label="📁 Arraste ou selecione seu arquivo de áudio (MP3/WAV)"
            )
            
            with gr.Row():
                input_idioma = gr.Dropdown(
                    choices=list(IDIOMAS.keys()), 
                    value="Português", 
                    label="🗣️ Idioma Falado Original"
                )
                
                input_modelo = gr.Dropdown(
                    choices=list(MODELOS.keys()),
                    value="Small (Equilibrado - Recomendado Geral)",
                    label="🧠 Modelo de Inteligência Artificial"
                )
            
            input_formato = gr.Radio(
                choices=["Texto Estruturado (.TXT)", "Legenda SRT (.SRT)"], 
                value="Texto Estruturado (.TXT)", 
                label="📄 Formato do Arquivo de Saída"
            )
            
            gr.Markdown(
                """
                > ⚠️ **Nota sobre VRAM Dedicada (GPU):**
                > Os modelos **Medium** e **Turbo** oferecem precisão máxima e pontuação contextual impecável, porém exigem uma placa de vídeo dedicada robusta (**recomenda-se de 8GB a 12GB de VRAM física**). Em sistemas mais modestos, utilize o modelo **Small**.
                """
            )
            
            gr.Markdown("### ⚙️ Executar Tarefa")
            with gr.Row():
                botao_normal = gr.Button("🚀 Iniciar Transcrição Original", variant="primary")
            with gr.Row():
                botao_traducao_en = gr.Button("🇬🇧 Traduzir Conteúdo para o Inglês", variant="secondary")
                botao_traducao_pt = gr.Button("🇧🇷 Traduzir Conteúdo para o Português", variant="secondary")
            
        with gr.Column(scale=10):
            gr.Markdown("### 🖥️ Painel de Controle e Monitoramento")
            
            output_status = gr.Textbox(
                label="📡 Status Atual do Sistema", 
                placeholder="Aguardando envio de arquivo...",
                interactive=False,
                lines=4
            )
            
            output_arquivo = gr.File(
                label="📦 Baixe seu Arquivo Pronto Here",
                interactive=False
            )

# Vinculos das ações passando a tarefa correspondente (CORRIGIDO)
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
    app.launch(inbrowser=True, share=False)