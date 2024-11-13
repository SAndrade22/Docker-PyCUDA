import pycuda.driver as cuda
cuda.init()

# Obtén la primera GPU disponible
device = cuda.Device(0)

# Obtén las propiedades del dispositivo
max_threads_per_block = device.get_attribute(cuda.device_attribute.MAX_THREADS_PER_BLOCK)

print(f"El número máximo de hilos por bloque en esta GPU es: {max_threads_per_block}")
