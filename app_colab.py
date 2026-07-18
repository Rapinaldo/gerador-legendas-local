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

# Dicionário de modelos expandido
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
        return "⚠️ Por favor, envie um arquivo de áudio antes de clicar.", None

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
        
        # Transcrição estável na GPU da nuvem (fp16=True ativado para desempenho máximo no Colab)
        print(f"[WHISPER NUVEM] Processando áudio original com modelo {tag_modelo.upper()}...")
        resultado = modelo.transcribe(caminho_local_audio, language=codigo_idioma, fp16=True)
        
        # --- BLOCOS DE TRADUÇÃO VIA MOTOR EXTERNO ---
        if tarefa == "traduzir_en":
            print("[TRADUTOR NUVEM] Convertendo o conteúdo gerado para o Inglês...")
            tradutor = GoogleTranslator(source='auto', target='en')
            if resultado.get("text"):
                resultado["text"] = tradutor.translate(resultado["text"])
            if "segments" in resultado:
                for seg in resultado["segments"]:
                    if seg.get("text", "").strip():
                        seg["text"] = tradutor.translate(seg["text"])
                        
        elif tarefa == "traduzir_pt":
            print("[TRADUTOR NUVEM] Convertendo o conteúdo gerado para o Português...")
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
            mensagem_sucesso = f"✅ Sucesso! Legenda SRT gerada na nuvem.\n📁 Salva na pasta /content/output"
            
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
            mensagem_sucesso = f"✅ Sucesso! Texto estruturado gerado na nuvem.\n📁 Salvo na pasta /content/output"

        return mensagem_sucesso, caminho_final
    except Exception as e:
        return f"❌ Erro no processamento da nuvem: {str(e)}", None
    finally:
        if pasta_gtemp and os.path.exists(pasta_gtemp):
            shutil.rmtree(pasta_gtemp)


# --- CONFIGURAÇÃO VISUAL PREMIUM (Sincronizada) ---
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

with gr.Blocks(theme=tema_customizado, title="Olho de Rapina - Whisper Studio Nuvem") as app:
    
    gr.Markdown(
        """
        # 🎙️ Olho de Rapina — Whisper Studio Nuvem
        *Transcreva áudios, gere legendas sincronizadas e faça traduções inteligentes usando os servidores dedicados do Google.*
        """
    )
    
    with gr.Row():
        with gr.Column(scale=12):
            gr.Markdown("### 🛠️ Configurações do Processamento")
            
            input_audio = gr.Audio(sources=["upload"], type="filepath", label="📁 Selecione ou arraste seu áudio")
            
            with gr.Row():
                input_idioma = gr.Dropdown(choices=list(IDIOMAS.keys()), value="Português", label="🗣️ Idioma Falado Original")
                input_modelo = gr.Dropdown(choices=list(MODELOS.keys()), value="Turbo (Máxima Precisão & Velocidade - Recomendado no Colab)", label="🧠 Modelo de Inteligência Artificial")
            
            input_formato = gr.Radio(
                choices=["Texto Estruturado (.TXT)", "Legenda SRT (.SRT)"], 
                value="Texto Estruturado (.TXT)", 
                label="📄 Formato do Arquivo de Saída"
            )
            
            gr.Markdown(
                """
                > 💡 **Dica de Uso no Colab:**
                > Como você está utilizando o hardware do Google, fique totalmente livre para selecionar o modelo **Turbo**. Ele fornecerá uma precisão espetacular com tempos de resposta curtíssimos sem consumir nada da sua máquina física!
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
            
            output_status = gr.Textbox(label="📡 Status Atual do Sistema", placeholder="Aguardando execução...", interactive=False, lines=4)
            output_arquivo = gr.File(label="📦 Baixe seu Arquivo Pronto Aqui", interactive=False)

    # Vinculos das ações da interface passando as tarefas dinâmicas
    botao_normal.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="transcrever"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_en.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_en"),
        inputs=[input_audio, i, m, f],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_pt.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_pt"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(share=True, debug=True)