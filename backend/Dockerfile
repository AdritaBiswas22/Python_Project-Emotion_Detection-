# Only needed for the Hugging Face Spaces deploy path. Render doesn't use this
# file — it installs requirements.txt and runs uvicorn directly.
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Hugging Face Docker Spaces route traffic to port 7860. That is the one thing
# that differs from the Render setup, which uses $PORT.
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
