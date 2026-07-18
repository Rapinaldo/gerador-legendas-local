# 🎙️ Olho de Rapina — Whisper Studio

Um estúdio completo e simplificado para transcrição de áudio, geração de legendas sincronizadas e tradução bidirecional inteligente (Português ↔ Inglês). O sistema opera de forma híbrida: pode ser executado **localmente** (aproveitando a aceleração por hardware da sua GPU) ou na **nuvem** através do Google Colab com um clique.

---

## 🚀 Executar na Nuvem (Google Colab)

Para rodar o estúdio utilizando os servidores e as placas de vídeo gratuitas do Google sem gastar o hardware da sua máquina local, basta clicar no botão abaixo:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/srapina/whisper-studio/blob/main/app_colab.py)

> 💡 **Nota de Uso no Colab:** Ao abrir o ambiente na nuvem, lembre-se de alterar o tipo de ambiente de execução para utilizar a **GPU T4** (_Ambiente de Execução > Alterar tipo de ambiente de execução > T4 GPU_). Isso fará o modelo **Turbo** processar seus arquivos na velocidade da luz!

---

## ✨ Funcionalidades

- **Transcrição de Áudio:** Converte arquivos de áudio (MP3, WAV, etc.) em texto limpo e estruturado em parágrafos.
- **Geração de Legendas (.SRT):** Cria arquivos de legenda com marcações de tempo perfeitamente sincronizadas frase por frase.
- **Tradução Bidirecional Inteligente:**
  - Traduz conteúdos de qualquer idioma de origem para o **Inglês**.
  - Traduz conteúdos de qualquer idioma de origem para o **Português** (preservando a sincronia das legendas SRT).
- **Interface Premium:** Roupagem moderna em modo escuro nativo desenvolvida em Gradio, otimizada para longas sessões de trabalho.
- **Carregamento Inteligente:** Os modelos do Whisper são carregados sob demanda na memória, evitando sobrecarga do sistema.

---

## 🛠️ Requisitos e Instalação (Ambiente Local)

Para rodar o projeto localmente com aceleração por hardware (GPU Nvidia), o ambiente utiliza o mapeamento do CUDA 11.8.

### 1. Clonar o Repositório

```bash
git clone [https://github.com/srapina/whisper-studio.git](https://github.com/srapina/whisper-studio.git)
cd whisper-studio
```
