import pycuda.autoinit
import pycuda.driver as cuda
from flask import Flask, request, jsonify, render_template
from pycuda.compiler import SourceModule
import numpy as np
from PIL import Image
import io
import base64
import math
import time

app = Flask(__name__)

# Inicialización del dispositivo CUDA
cuda.init()
device = cuda.Device(0)  # Asegúrate de que esté disponible

# Definición de los filtros CUDA
kernels = {
    "sobel": """
        __global__ void sobel_filter(float *input, float *output, int width, int height, int maskSize) {
            int x = blockIdx.x * blockDim.x + threadIdx.x;
            int y = blockIdx.y * blockDim.y + threadIdx.y;
            int halfMask = maskSize / 2;

            if (x >= halfMask && x < width - halfMask && y >= halfMask && y < height - halfMask) {
                int idx = y * width + x;
                float Gx = 0.0;
                float Gy = 0.0;

                for (int ky = -halfMask; ky <= halfMask; ky++) {
                    for (int kx = -halfMask; kx <= halfMask; kx++) {
                        int pos = (y + ky) * width + (x + kx);
                        float val = input[pos];
                        Gx += (kx == -1 ? -1 : (kx == 1 ? 1 : 0)) * val;
                        Gy += (ky == -1 ? -1 : (ky == 1 ? 1 : 0)) * val;
                    }
                }

                float magnitude = sqrtf(Gx * Gx + Gy * Gy);
                output[idx] = min(magnitude, 255.0f);
            } else if (x < width && y < height) {
                output[y * width + x] = 0.0f;
            }
        }
    """,
    "highpass": """
        __global__ void highpass_filter(float *input, float *output, int width, int height, int maskSize) {
            int x = blockIdx.x * blockDim.x + threadIdx.x;
            int y = blockIdx.y * blockDim.y + threadIdx.y;
            int halfMask = maskSize / 2;

            if (x >= halfMask && x < width - halfMask && y >= halfMask && y < height - halfMask) {
                int idx = y * width + x;
                float sum = 0.0;
                for (int ky = -halfMask; ky <= halfMask; ky++) {
                    for (int kx = -halfMask; kx <= halfMask; kx++) {
                        int pos = (y + ky) * width + (x + kx);
                        float val = input[pos];
                        sum += (kx == 0 && ky == 0 ? maskSize * maskSize - 1 : -1) * val;
                    }
                }
                output[idx] = min(max(sum, 0.0f), 255.0f);
            } else if (x < width && y < height) {
                output[y * width + x] = 0.0f;
            }
        }
    """,
    "erosion": """
        __global__ void erosion_filter(float *input, float *output, int width, int height, int maskSize) {
            int x = blockIdx.x * blockDim.x + threadIdx.x;
            int y = blockIdx.y * blockDim.y + threadIdx.y;
            int halfMask = maskSize / 2;

            if (x >= halfMask && x < width - halfMask && y >= halfMask && y < height - halfMask) {
                float min_val = 255.0f;

                for (int ky = -halfMask; ky <= halfMask; ky++) {
                    for (int kx = -halfMask; kx <= halfMask; kx++) {
                        int idx = (y + ky) * width + (x + kx);
                        min_val = fminf(min_val, input[idx]);
                    }
                }

                output[y * width + x] = min_val;
            } else {
                output[y * width + x] = input[y * width + x];
            }
        }
    """
}

@app.route('/api/procesar_imagen', methods=['POST'])
def procesar_imagen():
    try:
        start_time = time.time()

        # Crear contexto de CUDA para asegurar procesamiento único
        context = device.make_context()

        data = request.json
        image_data = data['image']
        filtro = data['filtro']
        
        # Obtener el tamaño de la máscara (si aplica)
        mask_size_str = data.get('maskSize', '3x3')
        mask_size = int(mask_size_str.split('x')[0])
        
        # Obtener threads per block en ambas dimensiones
        threads_per_block_x = int(data['threadsPerBlockX'])
        threads_per_block_y = int(data['threadsPerBlockY'])

        # Validación para no exceder el límite de 1024 hilos por bloque en total
        MAX_HILOS_POR_BLOQUE = 1024
        if threads_per_block_x * threads_per_block_y > MAX_HILOS_POR_BLOQUE:
            return jsonify({"error": f"La cantidad total de hilos por bloque no puede exceder {MAX_HILOS_POR_BLOQUE}."}), 400

        # Procesar imagen y asegurar su forma adecuada
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        imagen_np = np.array(image.convert('L')).astype(np.float32)
        height, width = imagen_np.shape

        # Crear el módulo y el kernel
        mod = SourceModule(kernels[filtro])
        filtro_func = mod.get_function(f"{filtro}_filter")

        # Configuración de memoria en GPU
        input_gpu = cuda.mem_alloc(imagen_np.nbytes)
        output_gpu = cuda.mem_alloc(imagen_np.nbytes)
        cuda.memcpy_htod(input_gpu, imagen_np)

        # Configuración de bloques y grid para asegurar procesamiento en cada píxel
        block = (threads_per_block_x, threads_per_block_y, 1)
        grid = (math.ceil(width / block[0]), math.ceil(height / block[1]))

        # Ejecutar el kernel
        if filtro == "erosion" or filtro == "highpass" or filtro == "sobel":
            filtro_func(input_gpu, output_gpu, np.int32(width), np.int32(height), np.int32(mask_size), block=block, grid=grid)
        else:
            filtro_func(input_gpu, output_gpu, np.int32(width), np.int32(height), block=block, grid=grid)

        # Obtener resultados y asegurar que estén en escala de grises
        resultado = np.empty_like(imagen_np)
        cuda.memcpy_dtoh(resultado, output_gpu)
        resultado = np.clip(resultado, 0, 255)
        resultado_image = Image.fromarray(resultado.astype(np.uint8))

        # Convertir la imagen a PNG y enviarla
        buffered = io.BytesIO()
        resultado_image.save(buffered, format="PNG")
        processed_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Liberar el contexto CUDA
        context.pop()

        # Tiempo de procesamiento
        processing_time_seconds = time.time() - start_time
        processing_time_milliseconds = processing_time_seconds * 1000

        return jsonify({
            "processedImageUrl": "data:image/png;base64," + processed_image_str,
            "processingTimeSeconds": round(processing_time_seconds, 4),
            "processingTimeMilliseconds": round(processing_time_milliseconds, 4),
            "maskUsed": mask_size_str,
            "threadCount": threads_per_block_x * threads_per_block_y,
            "blockCount": grid[0] * grid[1]
        })
    
    except Exception as e:
        print("Error procesando imagen:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('Pagina.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
