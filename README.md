# 🎙️ Olho de Rapina — Whisper Studio

Um estúdio completo e simplificado para transcrição de áudio, geração de legendas sincronizadas e tradução bidirecional inteligente (Português ↔ Inglês). O sistema opera de forma híbrida: pode ser executado **localmente** (aproveitando a aceleração por hardware da sua GPU) ou na **nuvem** através do Google Colab.

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

## 🛠️ Requisitos e Dependências (Ambiente Local)

Para rodar o projeto localmente com aceleração por hardware (GPU Nvidia), o ambiente foi mapeado utilizando o CUDA 11.8.

### Arquivo `requirements.txt`

```text
--extra-index-url [https://download.pytorch.org/whl/cu118](https://download.pytorch.org/whl/cu118)
torch
torchvision
torchaudio
gradio
git+[https://github.com/openai/whisper.git](https://github.com/openai/whisper.git)
deep-translator
```
