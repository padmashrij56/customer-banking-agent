# Enterprise Loan Underwriting Platform - PROVIDED, COMPLETE (Scope Decision
# 4). Participant work for Activity 3.2 is `docker build`, `docker run`,
# verifying the portal loads inside the container, and confirming .env
# passthrough - not authoring this file live.
FROM python:3.12-slim

WORKDIR /app

# System deps for faiss-cpu / numpy wheels build cleanly on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Basic container health check - confirms the Streamlit process is serving,
# not that the underwriting workflow itself is functional (that needs a
# configured OPENAI_API_KEY at runtime, passed in via --env-file .env).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
