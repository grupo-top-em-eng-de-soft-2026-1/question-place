<div align="center">
  <img src="docs/assets/book-icon-with-background.png" width="300" style="border-radius:24px;" />
</div>

<br>

<h1 align="center">QUESTION PLACE</h1>

Um Web App focado no aprendizado ativo por meio de perguntas e respostas

---

## Como rodar localmente

### 1. Criar e ativar o ambiente virtual

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependências

Com o ambiente virtual ativo, instale os pacotes listados em `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Subir o servidor web

Na raiz do projeto:

```bash
uvicorn app.server:app --reload
```

Ou use o script auxiliar (Linux / macOS):

```bash
bash scripts/run.sh
```

A aplicação ficará disponível em **http://127.0.0.1:8000/** (tela de login na rota `/`).

Para encerrar o servidor, pressione `Ctrl+C` no terminal.

---

## Tecnologias

* Python
* FastAPI
* Amazon Web Services

---

## Desenvolvedores

* JAIME GABRIEL ALVES PEREIRA - https://github.com/JaimeGAlves/
* JOÃO GABRIEL FREITAS CAVALCANTE - https://github.com/joeCavZero/
* JOÃO VICTOR CRUZ SILVA - https://github.com/joaocruzs/
* LETICIA LOPES DE OLIVEIRA - https://github.com/oliveiraleticialopes/
* RAYANNE ELLEN LOPES FIGUEIREDO - https://github.com/RayanneLps/
