# Aplicación Web de Convolución de Imágenes con PyCUDA

## Descripción

Esta aplicación web permite procesar imágenes a través de la convolución utilizando diferentes filtros lineales en la GPU. La aplicación está construida utilizando Flask y PyCUDA, y permite seleccionar entre filtros como Sobel, Erosión, y Highpass. La solución está diseñada para ser ejecutada en la nube, proporcionando un servicio web para procesar imágenes de manera eficiente.

## Requisitos

Para ejecutar la aplicación, se necesita tener Docker instalado en tu máquina. También debes tener una GPU NVIDIA compatible con CUDA y cuDNN para aprovechar la aceleración en la nube.

### Dependencias

Las dependencias de la aplicación están listadas en el archivo `requirements.txt`:

- Flask
- PyCUDA
- Numpy (versión 1.22.0)
- Pillow
- SciPy (versión 1.11.4)

## Pasos para ejecutar la aplicación

### 1. Clonar el repositorio

Si aún no has clonado el proyecto, hazlo con el siguiente comando:

```bash
git clone <URL_DEL_REPOSITORIO>
cd <nombre_del_repositorio>
