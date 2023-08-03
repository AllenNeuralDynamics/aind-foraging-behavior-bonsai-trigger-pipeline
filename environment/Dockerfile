# hash:sha256:8409be578ca524671e9329047f47a98d5f73c748c173482212e184d9b4be10d2
FROM registry.codeocean.allenneuraldynamics.org/codeocean/jupyterlab:3.0.9-miniconda4.9.2-python3.8-ubuntu20.04

ARG DEBIAN_FRONTEND=noninteractive

ARG GIT_ASKPASS
ARG GIT_ACCESS_TOKEN
COPY git-askpass /

RUN pip install -U --no-cache-dir \
    aind-codeocean-api==0.2.3 \
    numpy==1.24.4 \
    pandas==2.0.3

COPY postInstall /
RUN /postInstall
