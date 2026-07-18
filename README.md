# Gerador Automático de Legendas e Transcrições Local & Nuvem 🚀

Este é um aplicativo robusto e automatizado baseado no modelo **Whisper (small)** da OpenAI para transcrição de áudio em texto. O sistema oferece duas funções principais:
1. **Gerar Legenda .SRT**: Cria arquivos de legenda perfeitamente sincronizados com marcas de tempo.
2. **Transcrever para .TXT**: Gera transcrições contínuas, estruturadas e organizadas automaticamente em parágrafos profissionais para leitura fluida.

Para total segurança e organização, todos os arquivos gerados recebem um identificador único com a data e hora exatas do processamento (ex: `audio_20260718_010530.srt`), impedindo que gravações antigas sejam sobrescritas por acidente.

---

## 🛠️ Escolha Como Executar o Aplicativo

Você pode utilizar este projeto de duas formas. Escolha a que melhor se adapta à sua máquina abaixo:

### Opção 1: Execução Local (Windows com GPU Dedicada)
Ideal para quem possui uma placa de vídeo dedicada e deseja processar tudo offline, de forma 100% privada e sem depender da internet. Todo o processamento e armazenamento temporário é direcionado para a unidade de dados para poupar espaço no drive do sistema (C:).

#### Passo a Passo:
1. **Instalação Inicial**: Dê um duplo clique no arquivo `INSTALAR.bat`. Ele criará um ambiente virtual isolado Python (`venv`), atualizará os gerenciadores e instalará todas as dependências necessárias, incluindo o suporte a processamento por GPU.
2. **Inicialização**: Sempre que quiser usar o programa, dê um duplo clique no arquivo `INICIAR.bat`. Uma janela de terminal será aberta e, em seguida, a interface gráfica será carregada diretamente no seu navegador padrão.
3. **Encerramento**: Quando terminar, basta fechar a janela do terminal. O script foi projetado para abrir automaticamente a pasta `output` no Windows Explorer assim que o aplicativo for encerrado, agilizando o acesso aos seus arquivos salvos.

---

### Opção 2: Execução na Nuvem (Google Colab - Sem Placa de Vídeo)
Ideal para quem não possui placa de vídeo dedicada no computador, usa notebooks leves ou prefere não instalar nada localmente. O processamento utiliza as GPUs gratuitas fornecidas pelo Google na nuvem.

#### Passo a Passo:
1. Clique no botão oficial abaixo para acessar o ambiente de execução:
   
   [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Rapinaldo/gerador-legendas-local/blob/main/Gerador_Legendas_Colab.ipynb)

2. Se preferir criar um caderno do zero ou rodar manualmente, abra um novo notebook no [Google Colab](https://colab.research.google.com/) e execute o seguinte bloco de código em uma célula:

```bash
# 1. Instala as dependências do Linux e do Python na nuvem do Google
!apt-get install -y ffmpeg
!pip install openai-whisper gradio

# 2. Baixa o script adaptado para nuvem do seu repositório
!wget -O app_colab.py [https://raw.githubusercontent.com/Rapinaldo/gerador-legendas-local/main/app_colab.py](https://raw.githubusercontent.com/Rapinaldo/gerador-legendas-local/main/app_colab.py)

# 3. Executa o aplicativo gerando um link de acesso público temporário
!python app_colab.py