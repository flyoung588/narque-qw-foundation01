# Known working Python base image digest from Core-03; all build-time dependencies installed outside science container.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app \
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
WORKDIR /app
COPY cloud /app/cloud
RUN python -m pip install --no-cache-dir -r /app/cloud/requirements-fixed.txt
COPY foundation01 /app/foundation01
COPY examples /app/examples
COPY run_quantum_once.py /app/run_quantum_once.py
ENTRYPOINT ["python", "-B", "/app/cloud/run_admitted.py"]
