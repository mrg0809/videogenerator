# 🪟 Guía de Instalación para Windows

Esta guía proporciona instrucciones detalladas para instalar y usar Video Generator en Windows por primera vez.

## 📋 Requisitos Previos

Antes de comenzar, necesitarás instalar:

### 1. Python 3.8 o Superior

1. **Descarga Python**:
   - Ve a https://www.python.org/downloads/
   - Descarga la última versión de Python 3.8 o superior (recomendado: Python 3.11)

2. **Instala Python**:
   - Ejecuta el instalador descargado
   - ⚠️ **MUY IMPORTANTE**: Marca la casilla **"Add Python to PATH"** en la primera pantalla
   - Selecciona "Install Now"
   - Espera a que termine la instalación
   - Haz clic en "Close"

3. **Verifica la instalación**:
   - Abre el **Símbolo del sistema** (CMD):
     - Presiona `Windows + R`
     - Escribe `cmd` y presiona Enter
   - Escribe: `python --version`
   - Deberías ver algo como: `Python 3.11.x`
   - Si ves un error, reinicia tu computadora e intenta de nuevo

### 2. FFmpeg (Requerido para procesar videos)

FFmpeg es una herramienta esencial para trabajar con videos.

#### Opción A: Instalación Manual (Recomendada)

1. **Descarga FFmpeg**:
   - Ve a https://github.com/BtbN/FFmpeg-Builds/releases
   - Descarga el archivo: `ffmpeg-master-latest-win64-gpl.zip`

2. **Extrae FFmpeg**:
   - Extrae el contenido del ZIP a una ubicación permanente
   - Por ejemplo: `C:\ffmpeg`
   - Dentro deberías ver carpetas: `bin`, `doc`, `presets`

3. **Agrega FFmpeg al PATH**:
   - Abre el **Explorador de archivos**
   - Haz clic derecho en **"Este equipo"** → **"Propiedades"**
   - Haz clic en **"Configuración avanzada del sistema"** (a la izquierda)
   - Haz clic en **"Variables de entorno..."**
   - En "Variables del sistema", busca **"Path"** y haz doble clic
   - Haz clic en **"Nuevo"**
   - Agrega la ruta: `C:\ffmpeg\bin` (o donde hayas extraído FFmpeg)
   - Haz clic en **"Aceptar"** en todas las ventanas
   - **Reinicia tu computadora** para que los cambios surtan efecto

4. **Verifica la instalación**:
   - Abre una nueva ventana del **Símbolo del sistema**
   - Escribe: `ffmpeg -version`
   - Deberías ver información sobre la versión de FFmpeg

#### Opción B: Instalación con Chocolatey (Alternativa)

Si tienes **Chocolatey** instalado:
```cmd
choco install ffmpeg
```

## 🚀 Instalación de Video Generator

### Paso 1: Descargar el Proyecto

#### Opción A: Con Git (Recomendado si tienes Git instalado)

1. Abre el **Símbolo del sistema** o **PowerShell**
2. Navega a donde quieres guardar el proyecto, por ejemplo:
   ```cmd
   cd C:\Users\TuUsuario\Documents
   ```
3. Clona el repositorio:
   ```cmd
   git clone https://github.com/mrg0809/videogenerator.git
   ```
4. Entra al directorio:
   ```cmd
   cd videogenerator
   ```

#### Opción B: Descarga Directa (Sin Git)

1. Ve a https://github.com/mrg0809/videogenerator
2. Haz clic en el botón verde **"Code"**
3. Selecciona **"Download ZIP"**
4. Extrae el archivo ZIP en una ubicación permanente
   - Por ejemplo: `C:\Users\TuUsuario\Documents\videogenerator`
5. Abre el **Símbolo del sistema** y navega a esa carpeta:
   ```cmd
   cd C:\Users\TuUsuario\Documents\videogenerator
   ```

### Paso 2: Crear Acceso Directo en el Escritorio (Opcional pero Recomendado)

1. En el **Símbolo del sistema**, estando en el directorio del proyecto, ejecuta:
   ```cmd
   create_shortcut.bat
   ```
2. Esto creará un acceso directo llamado **"Video Generator"** en tu escritorio
3. Presiona cualquier tecla para cerrar

### Paso 3: Iniciar Video Generator por Primera Vez

Tienes dos opciones para iniciar la aplicación:

#### Opción A: Usando el Acceso Directo (Más Fácil)

1. Haz doble clic en el acceso directo **"Video Generator"** en tu escritorio
2. Se abrirá una ventana del Símbolo del sistema
3. El script automáticamente:
   - Verificará que Python está instalado
   - Creará un entorno virtual (primera vez solamente)
   - Instalará todas las dependencias necesarias (primera vez solamente)
   - Iniciará el servidor Flask
   - Abrirá tu navegador en http://localhost:5000

#### Opción B: Usando el Script Directamente

1. Abre el **Explorador de archivos**
2. Navega a la carpeta del proyecto
3. Haz doble clic en **`start_windows.bat`**
4. El proceso es el mismo que la Opción A

#### Primera Ejecución (Importante)

La **primera vez** que inicies Video Generator:

1. **La instalación tomará varios minutos**:
   - Se crearán carpetas del entorno virtual
   - Se descargarán e instalarán paquetes de Python
   - Verás muchas líneas de texto en la ventana del Símbolo del sistema

2. **Descarga automática del modelo de IA**:
   - La primera vez que elimines un fondo de una imagen, `rembg` descargará automáticamente el modelo de IA (u2net)
   - Este archivo es de **varios cientos de MB**
   - Puede tardar varios minutos dependiendo de tu conexión a internet
   - Solo necesitas hacer esto una vez

3. **No cierres la ventana del Símbolo del sistema**:
   - Esta ventana debe permanecer abierta mientras uses Video Generator
   - Si la cierras, el servidor se detendrá

## 🎬 Usar Video Generator

### Interfaz Web

Una vez que el servidor esté ejecutándose:

1. Tu navegador debería abrirse automáticamente en http://localhost:5000
2. Si no se abre automáticamente, abre tu navegador y ve a: http://localhost:5000

### Generar tu Primer Video

1. **Sube un video de introducción** (obligatorio):
   - Haz clic en "Seleccionar video de introducción"
   - Selecciona un archivo MP4, MOV o AVI
   - Este video aparecerá al inicio del video final

2. **Sube imágenes de productos** (obligatorio):
   - Haz clic en "Seleccionar imágenes"
   - Puedes seleccionar entre 1 y 5 imágenes (PNG, JPG o JPEG)
   - Estas imágenes se mostrarán después del video de introducción

3. **Sube una imagen de fondo** (opcional):
   - Si quieres un fondo personalizado, sube una imagen
   - Si no subes ninguna, se usará un fondo degradado

4. **Marca "Eliminar fondo automáticamente"** (opcional):
   - Si tus imágenes de productos tienen fondo que quieres remover
   - La IA eliminará el fondo automáticamente

5. **Selecciona el tipo de transición**:
   - **Carrusel**: Deslizamiento horizontal suave
   - **Tarjetas**: Efecto de desvanecimiento
   - **Cinta de Película**: Efecto vintage

6. **Haz clic en "Generar Video"**:
   - El procesamiento puede tardar varios minutos
   - Verás el progreso en la ventana del Símbolo del sistema
   - **NO cierres el navegador ni la ventana del Símbolo del sistema**

7. **Descarga tu video**:
   - Cuando termine, aparecerá un botón de descarga
   - El video también se guarda en la carpeta `videos/` del proyecto

## ⚙️ Configuración Adicional (Opcional)

### Variables de Entorno

Si quieres personalizar la configuración:

1. Crea un archivo `.env` en el directorio del proyecto
2. Agrega estas variables (opcional):
   ```
   SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
   FLASK_DEBUG=0
   ```

## 🛑 Detener el Servidor

Para detener Video Generator:

1. Ve a la ventana del **Símbolo del sistema** donde está ejecutándose
2. Presiona **`Ctrl + C`**
3. Confirma que quieres terminar el proceso (si te lo pregunta)
4. La ventana mostrará "Servidor detenido"

## 🔄 Ejecutar Video Generator Nuevamente

Para ejecutar Video Generator después de la primera vez:

1. **Opción Fácil**: Haz doble clic en el acceso directo del escritorio
2. **Opción Manual**: Ejecuta `start_windows.bat` desde la carpeta del proyecto

Las ejecuciones subsecuentes serán **mucho más rápidas** porque:
- El entorno virtual ya está creado
- Las dependencias ya están instaladas
- El modelo de IA ya está descargado

## 🐛 Solución de Problemas

### Error: "Python no está instalado o no está en el PATH"

**Solución**:
1. Verifica que Python esté instalado: `python --version`
2. Si no está instalado, instala Python siguiendo las instrucciones anteriores
3. Asegúrate de marcar "Add Python to PATH" durante la instalación
4. Reinicia tu computadora después de instalar Python

### Error: "FFmpeg not found" o "FFmpeg no está instalado"

**Solución**:
1. Verifica que FFmpeg esté instalado: `ffmpeg -version`
2. Si no está instalado, instala FFmpeg siguiendo las instrucciones anteriores
3. Asegúrate de agregar FFmpeg al PATH del sistema
4. Reinicia tu computadora después de agregar FFmpeg al PATH

### Error: "No se pudieron instalar las dependencias"

**Solución**:
1. Verifica tu conexión a internet
2. Asegúrate de que el archivo `requirements.txt` existe
3. Intenta instalar manualmente:
   ```cmd
   cd C:\ruta\a\videogenerator
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Si continúa fallando, actualiza pip:
   ```cmd
   python -m pip install --upgrade pip
   ```

### El navegador no se abre automáticamente

**Solución**:
1. Abre tu navegador manualmente
2. Ve a: http://localhost:5000
3. El servidor debería estar ejecutándose si no viste errores en el Símbolo del sistema

### "No module named 'moviepy'" u otros errores de módulos

**Solución**:
1. Asegúrate de que el entorno virtual esté activado
2. Reinstala las dependencias:
   ```cmd
   cd C:\ruta\a\videogenerator
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

### El video generado no tiene audio

**Verificación**:
1. Asegúrate de que tu video de introducción tiene audio
2. Verifica que FFmpeg esté correctamente instalado
3. Prueba con un video diferente

### Error de memoria insuficiente

**Solución**:
1. Reduce la resolución de tus imágenes antes de subirlas
2. Usa un video de introducción más corto
3. Reduce el número de imágenes de productos
4. Cierra otros programas para liberar memoria

### El procesamiento es muy lento

**Explicación**:
- El procesamiento de video requiere mucho CPU y memoria
- Es normal que tarde varios minutos
- Factores que afectan el tiempo:
  - Duración del video de introducción
  - Número de imágenes
  - Resolución de imágenes y video
  - Velocidad de tu computadora

**Consejos**:
- Sé paciente y no cierres el navegador o el Símbolo del sistema
- Usa resoluciones más bajas si es posible
- La eliminación de fondo tarda más (desactívala si no la necesitas)

## 📞 Soporte

Si encuentras problemas no listados aquí:

1. Revisa el archivo `README.md` para más información
2. Verifica los mensajes de error en el Símbolo del sistema
3. Abre un issue en GitHub: https://github.com/mrg0809/videogenerator/issues

## 📝 Notas Importantes

- **No compartas tu SECRET_KEY** si configuras una personalizada
- **Los videos generados** se guardan en la carpeta `videos/`
- **Los archivos subidos** se eliminan automáticamente después de generar el video
- **El modelo de IA** se descarga solo la primera vez y se guarda en tu sistema
- **Limpia periódicamente** la carpeta `videos/` para liberar espacio en disco

## ✅ Lista de Verificación

Antes de usar Video Generator, asegúrate de:

- [ ] Python 3.8+ está instalado y en el PATH
- [ ] FFmpeg está instalado y en el PATH
- [ ] Has clonado o descargado el proyecto
- [ ] Has ejecutado `create_shortcut.bat` (opcional)
- [ ] Has ejecutado `start_windows.bat` o el acceso directo
- [ ] El navegador se ha abierto en http://localhost:5000
- [ ] Tienes archivos de prueba listos (video de intro e imágenes)

¡Ahora estás listo para generar videos increíbles con Video Generator! 🎬🎉
