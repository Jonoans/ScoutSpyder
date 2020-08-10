FROM python:slim
RUN apt update && apt upgrade -y
RUN useradd -M scoutspyder
COPY --chown=scoutspyder:scoutspyder . /opt/scoutspyder
WORKDIR /opt/scoutspyder
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN rm -rf .git .gitignore Dockerfile requirements.txt update-container.sh docker-compose.yml
USER scoutspyder
WORKDIR /opt/scoutspyder/Backend
EXPOSE 8000
CMD ["uvicorn", "--app-dir", "../Api", "--workers", "2", "--host", "0.0.0.0", "--port", "8000", "ScoutSpyder:app"]