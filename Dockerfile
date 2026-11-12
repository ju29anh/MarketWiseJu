FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_BASE_URL=""
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 PORT=10000 ENVIRONMENT=production \
    STORAGE_DIR=/app/data STATIC_DIR=/app/frontend_dist \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    MAX_RESEARCH_TRAINING=1 MAX_CONCURRENT_ANALYSES=1
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home appuser
WORKDIR /app/backend
COPY backend/requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist /app/frontend_dist
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data
USER appuser
EXPOSE 10000
CMD ["python", "run.py"]
