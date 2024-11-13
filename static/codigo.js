// Mostrar la imagen en el canvas de vista previa
function previewImage(event) {
    const canvas = document.getElementById("previewCanvas");
    const ctx = canvas.getContext("2d");
    const reader = new FileReader();
    
    reader.onload = function() {
        const img = new Image();
        img.onload = function() {
            // Ajustamos el tamaño del canvas al tamaño de la imagen
            canvas.width = img.width;
            canvas.height = img.height;

            // Limpiar y dibujar la imagen en el canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = reader.result;
    };
    
    reader.readAsDataURL(event.target.files[0]);
}

// Enviar imagen y opciones de filtro al backend para procesamiento
function procesarImagen() {
    const filtroSeleccionado = document.getElementById("imageSelect").value;
    const maskSize = document.querySelector('input[name="mask"]:checked').value;
    const threadsPerBlock = document.getElementById("threadsPerBlock").value;

    const canvas = document.getElementById("previewCanvas");
    const imageData = canvas.toDataURL("image/png").replace(/^data:image\/(png|jpg);base64,/, "");

    console.log("Datos enviados al servidor:", {
        image: imageData,
        filtro: filtroSeleccionado,
        maskSize: maskSize,
        threadsPerBlock: threadsPerBlock
    });

    // Enviar los datos al backend
    fetch('/api/procesar_imagen', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            image: imageData,
            filtro: filtroSeleccionado,
            maskSize: maskSize,
            threadsPerBlockX: Math.floor(Math.sqrt(threadsPerBlock)), // Dividir en x
            threadsPerBlockY: Math.ceil(Math.sqrt(threadsPerBlock)) // Dividir en y
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error del servidor:', data.error);
        } else {
            const processedCanvas = document.getElementById("processedCanvas");
            const ctx = processedCanvas.getContext("2d");
            const img = new Image();
            img.onload = () => {
                // Ajustar el tamaño del canvas de resultado al tamaño de la imagen procesada
                processedCanvas.width = img.width;
                processedCanvas.height = img.height;

                // Escalar la imagen procesada para ajustarse al canvas manteniendo la proporción
                const maxWidth = processedCanvas.width;
                const maxHeight = processedCanvas.height;
                let width = img.width;
                let height = img.height;

                if (width > maxWidth || height > maxHeight) {
                    const scale = Math.min(maxWidth / width, maxHeight / height);
                    width = width * scale;
                    height = height * scale;
                }

                ctx.clearRect(0, 0, processedCanvas.width, processedCanvas.height);
                ctx.drawImage(img, 0, 0, width, height);
            };
            img.src = data.processedImageUrl;

            // Mostrar la información de procesamiento
            document.getElementById("initialMessage").style.display = "none";
            const infoBox = document.getElementById("infoBox");
            infoBox.style.display = "block";

            // Actualizar la información
            document.getElementById("blockCount").textContent = data.blockCount || "N/A";
            document.getElementById("threadCount").textContent = data.threadCount || "N/A";

            // Formatear el tiempo de procesamiento a 4 decimales en segundos y agregar "seg"
            const processingTime = data.processingTimeSeconds ? parseFloat(data.processingTimeSeconds).toFixed(4) + ' segs' : "N/A";
            document.getElementById("processingTime").textContent = processingTime;

            document.getElementById("maskUsed").textContent = data.maskUsed || "N/A";
        }
    })
    .catch(error => console.error('Error:', error));
}
