# 質問画面（src/web_app.py）を Cloud Run で動かすためのイメージ。手順は README の「社内で試す（Cloud Run）」。
# db/（interface_spec.sqlite と vectors.ruri-v3-310m.npy）は git に入っていないので、ビルドの前に手元で作っておく。
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 HF_HOME=/opt/hf EMBED_DEVICE=cpu
WORKDIR /app

RUN pip install --no-cache-dir torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
COPY deploy/requirements-web.txt /tmp/requirements-web.txt
RUN pip install --no-cache-dir -r /tmp/requirements-web.txt

# 埋め込みモデルをイメージに入れておく（起動のたびに 1GB 余りを取りに行かないように）
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('cl-nagoya/ruri-v3-310m', device='cpu')"
ENV HF_HUB_OFFLINE=1

COPY src/ src/
COPY prompts/ prompts/
COPY db/interface_spec.sqlite db/vectors.ruri-v3-310m.npy db/

# Cloud Run は PORT を渡す
CMD ["python", "src/web_app.py"]
