import sys
import time
import praw
import requests
from rich.console import Console
from rich.table import Table
from rich import box
from typing import List, Dict
from utils import clean_reddit_text, load_config, truncate_text
import re
from rich.progress import Progress
from dotenv import load_dotenv
import os
import json
from flask import request, jsonify, Flask
from flask_smorest import Api, Blueprint
from threading import Thread

console = Console()

#load_dotenv()  # Carrega variáveis de ambiente do arquivo .env
#token = os.getenv("WHATSAPP_API_TOKEN")  # Certifique-se de que a variável está definida


class RedditLLMSearcher:
    def __init__(self, verbose: bool = False):
        """
        Inicializa a classe RedditLLMSearcher.

        :param verbose: Se True, ativa o modo verbose para mais informações durante a execução.
        """
        self.verbose = verbose
        self.reddit = self._init_reddit()

        
    def _init_reddit(self):
        """
        Inicializa a conexão com a API do Reddit usando as credenciais do arquivo de configuração.

        :return: Um objeto Reddit da biblioteca PRAW.
        """
        config = load_config()
        return praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent=config['user_agent']
        )

    def generate_similar_questions(self, term: str) -> List[str]:
        """
        Gera 3 versões semelhantes da pergunta original.

        :param term: O termo de pesquisa original.
        :return: Uma lista de 3 perguntas semelhantes.
        """
        return [
            f"Quais são os principais tópicos sobre '{term}'?",
            f"Como '{term}' é discutido em diferentes contextos?",
            f"Quais são as opiniões populares sobre '{term}'?"
        ]

    def search_reddit(self, term: str, limit: int = 6) -> List[Dict]:
        results = []
        similar_questions = self.generate_similar_questions(term)

        limit_per_question = limit // len(similar_questions)
        if limit % len(similar_questions) != 0:
            limit_per_question += 1

        total_posts = limit_per_question * len(similar_questions)

        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Buscando no Reddit...", total=total_posts)
                for question in similar_questions:
                    search_params = {
                        'query': question,
                        'sort': 'relevant',
                        'time_filter': 'all',
                        'limit': limit_per_question,
                        'syntax': 'plain'
                    }

                    for post in self.reddit.subreddit('all').search(**search_params):
                        content = f"POST: {post.title}\n{post.selftext}"
                        content += '\n'.join([f"COMMENT: {comment.body}" 
                                            for comment in post.comments.list()[:5]])
                        
                        results.append({
                            'content': truncate_text(clean_reddit_text(content)),
                            'url': f"https://reddit.com{post.permalink}"
                        })
                        
                        progress.update(task, advance=1)  # Atualiza o progresso após cada postagem

                        if len(results) >= limit:
                            break
                    if len(results) >= limit:
                        break

        except Exception as e:
            self._handle_api_error(e)
        
        return results

    def query_llm(self, prompt: str, content: str) -> str:
        """
        Envia uma consulta para o modelo de linguagem e retorna a resposta.

        :param prompt: O prompt a ser enviado ao modelo de linguagem.
        :param content: O conteúdo a ser processado pelo modelo.
        :return: A resposta do modelo de linguagem em português.
        """
        retries = 3
        for _ in range(retries):
            try:
                # Otimizando o prompt para garantir que a resposta seja em português
                optimized_prompt = (
                    f"{prompt}\n\n{content}\n\n"
                    "Por favor, forneça a resposta em português."
                )
                response = requests.post(
                    'http://52.207.181.151:11434/api/generate',
                    json={
                        'model': 'deepseek-r1:8b',
                        'prompt': optimized_prompt,
                        'stream': False
                    },
                    timeout=120
                )
                
                return response.json()['response']
            except (requests.exceptions.RequestException, KeyError):
                time.sleep(5)
        return "Erro ao processar o resumo"

    def _handle_api_error(self, error):
        """
        Trata erros da API, incluindo rate limits.

        :param error: O erro a ser tratado.
        """
        if 'RATELIMIT' in str(error):
            console.print("[bold red]Erro de rate limit detectado. Aguarde 2 minutos...")
            time.sleep(120)
        else:
            console.print(f"[red]Erro na API: {error}")

    def display_results(self, term: str, results: List[Dict]):
        """
        Exibe os resultados da pesquisa em uma tabela formatada.

        :param term: O termo de pesquisa original.
        :param results: A lista de resultados a serem exibidos.
        """
        table = Table(title=f"Resultados para: [bold magenta]{term}", box=box.ROUNDED)
        table.add_column("Resumo", width=80)
        table.add_column("Link", width=40)

        with Progress() as progress:
            task = progress.add_task("[cyan]Processando resultados com LLM...", total=len(results))
            for item in results:
                summary = self.query_llm(
                    f"Resuma o conteúdo abaixo em português e explique como o termo '{term}' "
                    f"se relaciona com ele. Mantenha o resumo em 1 parágrafo.",
                    item['content']
                )
                cleaned_summary = self.clean_llm_response(summary)  # Limpa a resposta do LLM
                table.add_row(cleaned_summary, f"[link={item['url']}]{item['url']}[/link]")
                progress.update(task, advance=1)

        console.print(table)

    def clean_llm_response(response: str) -> str:
        """
        Limpa a resposta do modelo de linguagem removendo tags desnecessárias.

        :param response: A resposta do modelo de linguagem.
        :return: A resposta limpa.
        """
        # Remove as tags <think> e </think> da resposta
        cleaned_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        return cleaned_response

    def main():
        """
        Função principal que executa a ferramenta.

        Lê os argumentos da linha de comando e inicia a busca no Reddit.
        """
        if len(sys.argv) < 2:
            console.print("[bold red]Uso: python reddit_llm_search.py [termo] [limite] [--verbose]")
            return

        term = sys.argv[1]
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5  # Pega o limite ou usa 5 como padrão
        verbose = '--verbose' in sys.argv
        
        searcher = RedditLLMSearcher(verbose=verbose)
        results = searcher.search_reddit(term, limit)  # Passa o limite para a busca
        searcher.display_results(term, results)

