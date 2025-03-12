import json
from flask import request, jsonify, Flask
from flask_smorest import Api, Blueprint  # Importa o Api e Blueprint do flask-smorest
from threading import Thread
from reddit_llm_search import RedditLLMSearcher  # Importa a classe do módulo
import requests
import os
import re
from dotenv import load_dotenv
from rich.progress import Progress

app = Flask(__name__)

# Configurações do flask-smorest
app.config['API_TITLE'] = 'WhatsApp Webhook API'  # Adiciona o título da API
app.config['API_VERSION'] = 'v1'  # Adiciona a versão da API
app.config['OPENAPI_VERSION'] = '3.0.2'  # Adiciona a versão do OpenAPI
app.config['OPENAPI_URL_PREFIX'] = '/swagger'  # URL para acessar a documentação
app.config['OPENAPI_SWAGGER_UI'] = True  # Ativa a interface do Swagger UI

api = Api(app)  # Inicializa o Api do flask-smorest

load_dotenv()  # Carrega variáveis de ambiente do arquivo .env
token = os.getenv("WHATSAPP_API_TOKEN")  # Certifique-se de que a variável está definida

# Cria um Blueprint para o webhook
bp = Blueprint('webhook', 'webhook', url_prefix='/webhook')

def clean_llm_response(response: str) -> str:
    """
    Limpa a resposta do modelo de linguagem removendo tags desnecessárias.

    :param response: A resposta do modelo de linguagem.
    :return: A resposta limpa.
    """
    # Remove as tags <think> e </think> da resposta
    cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    return cleaned_response

def process_reddit_search(term, limit, sender_id):
    searcher = RedditLLMSearcher()
    results = searcher.search_reddit(term, limit)

    # Formatar os resultados usando o LLM
    formatted_responses = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processando resultados com LLM...", total=len(results))
        
        for result in results:
            summary = searcher.query_llm(
                f"Resuma o conteúdo abaixo em português e explique como o termo '{term}' se relaciona com ele. "
                f"Mantenha o resumo em 1 parágrafo.",
                result['content']
            )
            cleaned_summary = clean_llm_response(summary)  # Limpa a resposta do LLM
            formatted_responses.append(f"Resultado: {cleaned_summary}\nLink: {result['url']}")
            
            progress.update(task, advance=1)  # Atualiza a barra de progresso após cada resumo processado

    # Enviar a resposta formatada para o WhatsApp
    if formatted_responses:  # Verifica se há respostas formatadas
        for response_message in formatted_responses:
            send_whatsapp_message(sender_id, response_message)
    else:
        send_whatsapp_message(sender_id, "Nenhum resultado encontrado.")

def send_whatsapp_message(sender_id, message):
    # URL da API do WhatsApp Business
    url = "https://graph.facebook.com/v13.0/441867515682175/messages"  # Substitua pelo seu ID de número de telefone

    # Token de acesso
    #token = os.getenv("WHATSAPP_API_TOKEN")  # Certifique-se de que o token está definido nas variáveis de ambiente

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": sender_id,
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"Mensagem enviada para {sender_id}")
    else:
        print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")

@bp.route('', methods=['GET', 'POST'])  # Aceitar GET e POST
#@api.doc(description="Endpoint para receber mensagens do WhatsApp.")
def webhook():
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        if token == 'reddit':
            return request.args.get('hub.challenge'), 200
        return 'Unauthorized', 403

    if request.method == 'POST':
        data = request.get_json()
        print(json.dumps(data, indent=2))  # Exibe a mensagem no console

        # Verifica se a chave 'messages' está presente
        if 'messages' in data['entry'][0]['changes'][0]['value']:
            term = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']  # Termo de pesquisa
            sender_id = data['entry'][0]['changes'][0]['value']['messages'][0]['from']  # ID do remetente
            limit = 5  # Defina o limite desejado

            # Envia uma mensagem informando que o resultado levará cerca de 2 minutos
            initial_response_message = "Recebemos sua pergunta! Você receberá a resposta em cerca de 2 minutos."
            send_whatsapp_message(sender_id, initial_response_message)  # Envia a mensagem inicial

            # Inicia o processamento em segundo plano
            Thread(target=process_reddit_search, args=(term, limit, sender_id)).start()

            return jsonify(status='success'), 200  # Retorna imediatamente
        elif 'statuses' in data['entry'][0]['changes'][0]['value']:
            print("Recebido um status de mensagem, não uma nova mensagem.")
            return jsonify(status='status_received'), 200  # Retorna imediatamente

        return jsonify(status='no_message_found'), 400  # Retorna erro se não encontrar mensagens ou status

api.register_blueprint(bp)  # Registra o Blueprint

if __name__ == '__main__':
    # Ativa o modo debug para recarregar automaticamente
    app.run(port=5000, debug=True) 