# Reddit LLM Search com WhatsApp Bot

Este projeto implementa um bot para WhatsApp que permite buscar informações no Reddit e processar os resultados usando um modelo de linguagem (LLM). Quando um usuário envia uma mensagem para o número do WhatsApp configurado, o sistema busca conteúdo relevante no Reddit, utiliza um modelo de linguagem para resumir as informações e envia as respostas formatadas de volta para o usuário.

## Funcionalidades

- Recebe mensagens do WhatsApp via Webhook
- Busca conteúdo relevante no Reddit baseado no termo pesquisado
- Gera múltiplas perguntas semelhantes para melhorar os resultados da busca
- Processa o conteúdo usando um modelo de linguagem para gerar resumos em português
- Exibe barras de progresso para acompanhar o status das buscas e do processamento
- Envia os resultados formatados de volta para o usuário via WhatsApp
- Executa o processamento em segundo plano para não bloquear o webhook
- Lida com diferentes tipos de eventos da API do WhatsApp (mensagens e status)

## Requisitos

- Python 3.11 ou superior
- Bibliotecas:
  - Flask >= 2.0.0
  - Flask-Smorest >= 0.35.0
  - Requests >= 2.31.0
  - PRAW (Python Reddit API Wrapper) >= 7.7.0
  - Rich >= 13.7.0
  - python-dotenv >= 1.0.0
  - watchdog (para o script monitor.py)

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/reddit-llm-search.git
   cd reddit-llm-search
   ```

2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use `venv\Scripts\activate`
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as credenciais:
   - Renomeie `config.example.json` para `config.json` e adicione suas credenciais da API do Reddit:
     ```json
     {
       "client_id": "seu_client_id_do_reddit",
       "client_secret": "seu_client_secret_do_reddit",
       "user_agent": "seu_user_agent"
     }
     ```
   - Crie um arquivo `.env` na raiz do projeto e adicione seu token da API do WhatsApp:
     ```plaintext
     WHATSAPP_API_TOKEN=seu_token_aqui
     ```

## Estrutura do Projeto

- `app.py`: Aplicação Flask principal com o webhook para o WhatsApp
- `reddit_llm_search.py`: Implementa a classe RedditLLMSearcher para buscar no Reddit e processar com LLM
- `utils.py`: Contém funções utilitárias como limpeza de texto, carregamento de configurações e truncamento
- `monitor.py`: Script para monitorar alterações nos arquivos Python durante o desenvolvimento
- `requirements.txt`: Lista de dependências do projeto
- `config.json`: Configurações da API do Reddit (não incluso no repositório)
- `config.example.json`: Exemplo de arquivo de configuração para a API do Reddit
- `.env`: Arquivo com variáveis de ambiente (não incluso no repositório)
- `serverless.yml`: Configuração para implantação serverless (opcional)

## Como Usar

1. Inicie o servidor Flask:
   ```bash
   python app.py
   ```

2. Configure o webhook no WhatsApp Business Cloud API para apontar para o seu endpoint:
   ```
   https://seu-dominio.com/webhook
   ```
   
   Para desenvolvimento local, você pode usar ferramentas como ngrok:
   ```bash
   ngrok http 5000
   ```

3. Envie uma mensagem para o número de telefone do WhatsApp associado à sua conta do WhatsApp Business:
   - A mensagem deve conter o termo que você deseja pesquisar no Reddit
   - O sistema confirmará o recebimento da mensagem
   - Em aproximadamente 2 minutos, você receberá os resultados formatados

## Fluxo de Processamento

1. O usuário envia uma mensagem para o número do WhatsApp
2. O webhook recebe a mensagem via POST
3. O sistema envia uma confirmação de recebimento
4. Em segundo plano, o processo de busca no Reddit é iniciado:
   - Gera perguntas semelhantes baseadas no termo original
   - Busca postagens relevantes no Reddit
   - Processa cada resultado usando o modelo de linguagem
   - Formata as respostas e remove tags desnecessárias
5. Os resultados são enviados de volta para o usuário

## Tratamento de Erros

- Verifica se a mensagem recebida contém a chave 'messages' ou 'statuses'
- Trata erros de rate limit da API do Reddit com espera automática
- Implementa retentativas para chamadas ao modelo de linguagem
- Fornece feedback sobre o progresso do processamento

## Monitoramento

O projeto inclui um script `monitor.py` que pode ser usado durante o desenvolvimento para monitorar alterações nos arquivos Python:

```bash
python monitor.py
```

## Implantação

O projeto inclui um arquivo `serverless.yml` para implantação em ambientes serverless, como AWS Lambda.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir um pull request ou relatar problemas.

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para mais detalhes.