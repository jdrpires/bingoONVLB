# BingoON

Sistema web para organizadores criarem bingos e conduzirem rodadas com sorteios
sem repetição.

## Desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
flask --app app run --port 5002
```

Acesse `http://localhost:5002`.

## Testes

```bash
pytest
```

## Configuração

- `SECRET_KEY`: chave usada para proteger sessão e formulários.
- `DATABASE_URL`: conexão do banco. O padrão local é SQLite; produção deve usar
  PostgreSQL.

O sorteio dos números é realizado pela própria aplicação. Não é necessário usar
uma API de inteligência artificial para garantir aleatoriedade.

## Produção

O projeto inclui `Dockerfile` e configuração do Gunicorn. Para produção:

- configure `APP_ENV=production`;
- gere uma `SECRET_KEY` longa e aleatória;
- configure `DATABASE_URL` com uma conexão PostgreSQL;
- exponha a porta indicada pela variável `PORT`;
- use `/health` como endpoint de verificação.

Exemplo local com Docker:

```bash
docker build -t bingo-on .
docker run --rm -p 5002:5002 \
  -e APP_ENV=production \
  -e SECRET_KEY="uma-chave-segura" \
  -e DATABASE_URL="sqlite:////tmp/bingo.db" \
  bingo-on
```
