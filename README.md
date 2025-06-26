# BingoONVLB

Aplicação simples de Bingo com integração opcional ao GPT via API da OpenAI.

## Requisitos
- Python 3.8+
- Flask
- Biblioteca `openai` (opcional para geração via IA)

## Uso

1. Defina a variável `OPENAI_API_KEY` com sua chave se quiser usar o GPT.
2. Instale as dependências:
   ```bash
   pip install flask openai
   ```
3. Execute o servidor:
   ```bash
   python app.py
   ```
4. Acesse `http://localhost:5000` no navegador.

Pressione **Sortear** para gerar um número. Uma animação embaralha os valores
na tela antes de exibir o sorteado, que fica marcado em roxo na cartela.
Use o botão **Resetar** para reiniciar o jogo e limpar os números já sorteados.
