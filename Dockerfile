# Imagen base con CUDA y Python, sin cuDNN
FROM nvidia/cuda:12.5.1-devel-ubuntu22.04

# Instalar paquetes necesarios
RUN apt-get update -qq && \
    apt-get install -y -qq python3-pip build-essential && \
    pip3 install --no-cache-dir pycuda flask numpy pillow

# Copiar el código de la aplicación
COPY . /app
WORKDIR /app

# Exponer el puerto para Flask
EXPOSE 5000

# Comando para iniciar Flask
CMD ["python3", "servidor.py"]
