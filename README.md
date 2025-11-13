# 🎬 Video Generator - Generador de Videos con Carrusel

Aplicación web Flask que genera videos profesionales combinando un video de introducción con un carrusel de imágenes de productos. Incluye eliminación automática de fondo y reemplazo con fondos personalizados.

## ✨ Características

- **Video de Introducción**: Añade un video al inicio del video final
- **Carrusel de Productos**: Muestra hasta 5 imágenes con efecto de deslizamiento horizontal suave
- **Eliminación de Fondo**: Remueve automáticamente el fondo de las imágenes de productos usando rembg
- **Fondos Personalizados**: Opción de usar una imagen personalizada como fondo para los productos
- **Interfaz Web Intuitiva**: Interfaz moderna y fácil de usar
- **Descarga Directa**: Descarga el video generado directamente desde el navegador

## 🛠️ Tecnologías Utilizadas

- **Flask**: Framework web de Python
- **MoviePy**: Edición y procesamiento de video
- **rembg**: Eliminación automática de fondos de imágenes
- **Pillow (PIL)**: Procesamiento y manipulación de imágenes
- **HTML/CSS/JavaScript**: Interfaz de usuario moderna

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- FFmpeg (requerido por MoviePy)

### Instalación de FFmpeg

#### En Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### En macOS (con Homebrew):
```bash
brew install ffmpeg
```

#### En Windows:
1. Descarga FFmpeg desde https://ffmpeg.org/download.html
2. Extrae los archivos y añade la carpeta `bin` al PATH del sistema

## 🚀 Instalación

1. **Clonar el repositorio**:
```bash
git clone https://github.com/mrg0809/videogenerator.git
cd videogenerator
```

2. **Crear y activar un entorno virtual** (recomendado):
```bash
# En Linux/macOS
python3 -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
venv\Scripts\activate
```

3. **Instalar las dependencias**:
```bash
pip install -r requirements.txt
```

**Nota**: La primera vez que uses `rembg`, descargará automáticamente el modelo de IA (u2net), que puede ser de varios cientos de MB. Esto puede tardar unos minutos dependiendo de tu conexión a internet.

## 🎮 Uso

### Iniciar el Servidor

```bash
python app.py
```

El servidor se iniciará en `http://localhost:5000`

### Uso de la Aplicación Web

1. **Abre tu navegador** y accede a `http://localhost:5000`

2. **Sube los archivos requeridos**:
   - **Video de Introducción** (obligatorio): Un archivo de video (MP4, MOV, o AVI)
   - **Imágenes de Productos** (obligatorio): Entre 1 y 5 imágenes (PNG, JPG, o JPEG)
   - **Fondo Personalizado** (opcional): Una imagen para usar como fondo (PNG, JPG, o JPEG)

3. **Haz clic en "Generar Video"**

4. **Espera** mientras se procesa el video (esto puede tomar varios minutos)

5. **Descarga** el video generado cuando esté listo

## 📁 Estructura del Proyecto

```
videogenerator/
├── app.py                 # Aplicación principal de Flask
├── requirements.txt       # Dependencias de Python
├── README.md             # Este archivo
├── .gitignore            # Archivos a ignorar por Git
├── templates/
│   └── index.html        # Plantilla HTML principal
├── static/
│   └── style.css         # Estilos CSS
├── uploads/              # Directorio temporal para archivos subidos
│   └── .gitkeep
└── videos/               # Directorio para videos generados
    └── .gitkeep
```

## 🔧 Configuración

### Variables de Entorno

Puedes configurar las siguientes variables de entorno:

- `SECRET_KEY`: Clave secreta para Flask (por defecto: 'dev_secret_key_change_in_production')
  - **IMPORTANTE**: En producción, establece una clave secreta segura y aleatoria
- `FLASK_DEBUG`: Modo debug (1 para desarrollo, 0 para producción, por defecto: 1)
  - **IMPORTANTE**: Siempre establece `FLASK_DEBUG=0` en producción por seguridad

#### Ejemplo para producción:

```bash
export SECRET_KEY="tu-clave-secreta-muy-larga-y-aleatoria"
export FLASK_DEBUG=0
python app.py
```

### Límites de Tamaño

- Tamaño máximo de archivo: 500 MB (configurable en `app.py`)
- Máximo de imágenes de productos: 5

## 🎨 Personalización

### Duración del Carrusel

Para cambiar la duración de cada imagen en el carrusel, edita el parámetro `duration` en la función `create_carousel_clip()` en `app.py`:

```python
carousel_clip = create_carousel_clip(processed_image_path, duration=3, video_size=video_size)
```

### Resolución del Video

La resolución del video final se basa en el video de introducción. Para forzar una resolución específica, modifica el parámetro `target_size` en la función `remove_background_and_composite()`.

### Efecto de Transición

El efecto de carrusel se puede personalizar modificando la función `position_func` dentro de `create_carousel_clip()` en `app.py`.

## 🧪 Prueba Manual

### Archivos de Prueba Recomendados

Para probar la aplicación, necesitarás:

1. **Video de Intro**: Un video corto (5-10 segundos) en formato MP4
2. **Imágenes de Productos**: 2-3 imágenes de productos con fondos sólidos o complejos
3. **Imagen de Fondo**: Una imagen con buena resolución (1920x1080 recomendado)

### Pasos de Prueba

1. Inicia el servidor con `python app.py`
2. Accede a `http://localhost:5000` en tu navegador
3. Sube los archivos de prueba
4. Observa los mensajes de progreso en la consola del servidor
5. Descarga el video generado cuando esté listo
6. Reproduce el video para verificar:
   - El video de intro se reproduce correctamente
   - Los fondos de las imágenes han sido eliminados
   - Las imágenes tienen el nuevo fondo aplicado
   - El efecto de carrusel funciona suavemente
   - La transición entre imágenes es fluida

## ⚠️ Consideraciones Importantes

### Rendimiento

- El procesamiento de video puede consumir mucha CPU y memoria
- La eliminación de fondo requiere un modelo de IA y puede ser lenta en hardware limitado
- El tiempo de procesamiento depende de:
  - Duración del video de intro
  - Número de imágenes de productos
  - Resolución de las imágenes y videos
  - Especificaciones del hardware

### Almacenamiento

- Los archivos temporales se eliminan automáticamente después de generar el video
- Los videos generados se almacenan en la carpeta `videos/`
- Asegúrate de tener suficiente espacio en disco (recomendado: 5-10 GB libres)

### Seguridad

- **CRÍTICO**: En producción, establece `FLASK_DEBUG=0` para desactivar el modo debug
- En producción, cambia la `SECRET_KEY` por una clave segura y aleatoria
- Considera implementar autenticación si la aplicación es pública
- Limita el tamaño de los archivos subidos según tus necesidades
- Implementa limpieza periódica de videos antiguos
- Considera usar HTTPS en producción
- Valida y sanitiza todas las entradas de usuario

## 🐛 Solución de Problemas

### Error: "No module named 'moviepy'"

Asegúrate de haber instalado las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "FFmpeg not found"

Instala FFmpeg según las instrucciones de la sección "Requisitos Previos".

### Error durante la eliminación de fondo

La primera vez que uses `rembg`, descargará el modelo automáticamente. Asegúrate de tener conexión a internet estable.

### El video generado no tiene audio

Si el video de introducción tiene audio, debería mantenerse. Verifica que el archivo de video original tenga audio y que FFmpeg esté correctamente instalado.

### Memoria insuficiente

Si encuentras errores de memoria, considera:
- Reducir la resolución de las imágenes antes de subirlas
- Usar un video de intro más corto
- Reducir el número de imágenes de productos
- Aumentar la memoria disponible para Python

## 📝 Notas de Desarrollo

- Los archivos subidos se guardan temporalmente con nombres únicos (UUID)
- Las imágenes procesadas se eliminan automáticamente después de generar el video
- El efecto de carrusel usa interpolación suave (ease-in-out)
- La eliminación de fondo preserva el canal alfa para transparencia

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

Desarrollado como parte del proyecto videogenerator.

## 🙏 Agradecimientos

- [MoviePy](https://zulko.github.io/moviepy/) - Edición de video en Python
- [rembg](https://github.com/danielgatis/rembg) - Eliminación de fondos con IA
- [Flask](https://flask.palletsprojects.com/) - Framework web de Python
- [Pillow](https://python-pillow.org/) - Procesamiento de imágenes
