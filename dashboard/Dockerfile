# Dashboard Streamlit
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit

EXPOSE 8501
CMD ["python", "-m", "streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0"]
