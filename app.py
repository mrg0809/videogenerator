import os
import uuid
import io
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image
from rembg import remove
import numpy as np

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
VIDEOS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEOS_FOLDER'] = VIDEOS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEOS_FOLDER, exist_ok=True)


def allowed_file(filename, file_type):
    """
    Check if the file extension is allowed based on file type.
    
    Args:
        filename: Name of the file
        file_type: 'video' or 'image'
    
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    elif file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    
    return False


def remove_background_and_composite(product_image_path, background_image_path, output_path, target_size=(1920, 1080)):
    """
    Remove background from product image and composite it onto a custom background.
    
    Args:
        product_image_path: Path to the product image
        background_image_path: Path to the background image (can be None)
        output_path: Path to save the result
        target_size: Target size for the output image (width, height)
    
    Returns:
        str: Path to the processed image
    """
    try:
        # Load product image
        with open(product_image_path, 'rb') as f:
            input_image = f.read()
        
        # Remove background - rembg.remove returns bytes
        output_bytes = remove(input_image)
        
        # Convert bytes to PIL Image using BytesIO
        product_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        
        # Create or load background
        if background_image_path and os.path.exists(background_image_path):
            background = Image.open(background_image_path).convert("RGBA")
            background = background.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Default white background
            background = Image.new('RGBA', target_size, (255, 255, 255, 255))
        
        # Scale product to fit within background while maintaining aspect ratio
        product_width, product_height = product_img.size
        bg_width, bg_height = target_size
        
        # Calculate scaling factor (use 80% of background size max)
        scale_factor = min((bg_width * 0.8) / product_width, (bg_height * 0.8) / product_height)
        new_width = int(product_width * scale_factor)
        new_height = int(product_height * scale_factor)
        
        product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the product
        x = (bg_width - new_width) // 2
        y = (bg_height - new_height) // 2
        
        # Composite product onto background
        background.paste(product_img, (x, y), product_img)
        
        # Convert to RGB and save
        final_image = background.convert('RGB')
        final_image.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    except Exception as e:
        print(f"Error processing image: {e}")
        raise


def composite_without_removal(product_image_path, background_image_path, output_path, target_size=(1920, 1080)):
    """
    Composite product image onto background without removing its background.
    
    Args:
        product_image_path: Path to the product image
        background_image_path: Path to the background image (can be None)
        output_path: Path to save the result
        target_size: Target size for the output image (width, height)
    
    Returns:
        str: Path to the processed image
    """
    try:
        # Load product image
        product_img = Image.open(product_image_path).convert("RGB")
        
        # Create or load background
        if background_image_path and os.path.exists(background_image_path):
            background = Image.open(background_image_path).convert("RGB")
            background = background.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Default white background
            background = Image.new('RGB', target_size, (255, 255, 255))
        
        # Scale product to fit within background while maintaining aspect ratio
        product_width, product_height = product_img.size
        bg_width, bg_height = target_size
        
        # Calculate scaling factor (use 80% of background size max)
        scale_factor = min((bg_width * 0.8) / product_width, (bg_height * 0.8) / product_height)
        new_width = int(product_width * scale_factor)
        new_height = int(product_height * scale_factor)
        
        product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the product
        x = (bg_width - new_width) // 2
        y = (bg_height - new_height) // 2
        
        # Paste product onto background
        background.paste(product_img, (x, y))
        
        # Save the final image
        background.save(output_path, 'JPEG', quality=95)
        
        return output_path
    
    except Exception as e:
        print(f"Error compositing image: {e}")
        raise


def create_carousel_clip(image_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with card-like carousel sliding effect for an image.
    Enhanced with smooth acceleration and deceleration for a more polished look.
    
    Args:
        image_path: Path to the image
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with carousel effect
    """
    try:
        # Load image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function for card-like sliding effect
        def position_func(t):
            # Progress from 0 to 1
            progress = t / duration
            
            # Card-like transition with smooth easing
            # Using cubic ease-in-out for smoother, more natural motion
            if progress < 0.25:
                # Slide in from right with acceleration
                ease = progress / 0.25
                # Cubic ease-in: starts slow, accelerates
                ease = ease * ease * ease
                x = video_size[0] * (1 - ease)
            elif progress > 0.75:
                # Slide out to left with deceleration
                ease = (progress - 0.75) / 0.25
                # Cubic ease-out: starts fast, decelerates
                ease = 1 - (1 - ease) ** 3
                x = -video_size[0] * ease
            else:
                # Stay centered
                x = 0
            
            return (x, 'center')
        
        # Apply position function for smooth card-like motion
        clip = clip.set_position(position_func)
        
        # Apply subtle fade in/out for smoother transitions
        clip = clip.crossfadein(0.3).crossfadeout(0.3)
        
        return clip
    
    except Exception as e:
        print(f"Error creating carousel clip: {e}")
        raise


def generate_video(intro_path, product_images, background_image_path, output_path, remove_bg=True):
    """
    Generate the final video with intro and carousel of product images.
    
    Args:
        intro_path: Path to intro video
        product_images: List of paths to product images
        background_image_path: Path to custom background image (can be None)
        output_path: Path to save the output video
        remove_bg: Whether to remove background from images (default: True)
    
    Returns:
        str: Path to the generated video
    """
    clips = []
    processed_images = []
    
    try:
        # Load intro video
        print("Loading intro video...")
        intro_clip = VideoFileClip(intro_path)
        clips.append(intro_clip)
        
        # Get video size from intro
        video_size = (intro_clip.w, intro_clip.h)
        
        # Process each product image
        print(f"Processing {len(product_images)} product images...")
        for i, product_image in enumerate(product_images):
            print(f"Processing image {i+1}/{len(product_images)}...")
            
            # Create processed image path
            processed_image_path = os.path.join(
                UPLOAD_FOLDER, 
                f"processed_{uuid.uuid4().hex}.jpg"
            )
            processed_images.append(processed_image_path)
            
            # Remove background and composite if requested
            if remove_bg:
                remove_background_and_composite(
                    product_image, 
                    background_image_path, 
                    processed_image_path,
                    video_size
                )
            else:
                # Just resize and optionally composite on background without removing bg
                composite_without_removal(
                    product_image,
                    background_image_path,
                    processed_image_path,
                    video_size
                )
            
            # Create carousel clip with card effect
            carousel_clip = create_carousel_clip(processed_image_path, duration=3, video_size=video_size)
            clips.append(carousel_clip)
        
        # Concatenate all clips
        print("Concatenating clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Write final video
        print("Rendering final video...")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            preset='medium',
            threads=4
        )
        
        # Close all clips to release resources
        for clip in clips:
            clip.close()
        final_clip.close()
        
        print("Video generation complete!")
        return output_path
    
    except Exception as e:
        print(f"Error generating video: {e}")
        # Clean up clips
        for clip in clips:
            try:
                clip.close()
            except:
                pass
        raise
    
    finally:
        # Clean up processed images
        for img_path in processed_images:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                print(f"Warning: Could not delete processed image {img_path}: {e}")


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/generate_video', methods=['POST'])
def generate_video_route():
    """Handle video generation request."""
    uploaded_files = []
    
    try:
        # Check if files are present
        if 'intro_video' not in request.files:
            flash('No se encontró el video de introducción', 'error')
            return redirect(url_for('index'))
        
        if 'product_images' not in request.files:
            flash('No se encontraron imágenes de productos', 'error')
            return redirect(url_for('index'))
        
        intro_video = request.files['intro_video']
        product_images = request.files.getlist('product_images')
        custom_background = request.files.get('custom_background')
        
        # Get checkbox value for background removal
        remove_bg = request.form.get('remove_background') == 'yes'
        
        # Validate intro video
        if intro_video.filename == '':
            flash('No se seleccionó un video de introducción', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(intro_video.filename, 'video'):
            flash('Formato de video no válido. Use MP4, MOV o AVI', 'error')
            return redirect(url_for('index'))
        
        # Validate product images
        if not product_images or product_images[0].filename == '':
            flash('No se seleccionaron imágenes de productos', 'error')
            return redirect(url_for('index'))
        
        if len(product_images) > 5:
            flash('Máximo 5 imágenes de productos permitidas', 'error')
            return redirect(url_for('index'))
        
        for img in product_images:
            if not allowed_file(img.filename, 'image'):
                flash(f'Formato de imagen no válido: {img.filename}. Use PNG, JPG o JPEG', 'error')
                return redirect(url_for('index'))
        
        # Save intro video
        print("Guardando video de introducción...")
        intro_filename = f"{uuid.uuid4().hex}_{secure_filename(intro_video.filename)}"
        intro_path = os.path.join(app.config['UPLOAD_FOLDER'], intro_filename)
        intro_video.save(intro_path)
        uploaded_files.append(intro_path)
        
        # Save product images
        print("Guardando imágenes de productos...")
        product_image_paths = []
        for img in product_images:
            img_filename = f"{uuid.uuid4().hex}_{secure_filename(img.filename)}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
            img.save(img_path)
            uploaded_files.append(img_path)
            product_image_paths.append(img_path)
        
        # Save custom background if provided
        background_path = None
        if custom_background and custom_background.filename != '':
            if allowed_file(custom_background.filename, 'image'):
                print("Guardando imagen de fondo personalizado...")
                bg_filename = f"{uuid.uuid4().hex}_{secure_filename(custom_background.filename)}"
                background_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)
                custom_background.save(background_path)
                uploaded_files.append(background_path)
            else:
                flash('Formato de imagen de fondo no válido', 'warning')
        
        # Generate output filename
        output_filename = f"video_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['VIDEOS_FOLDER'], output_filename)
        
        # Generate video
        print("Iniciando generación de video...")
        flash('Procesando video... Esto puede tomar varios minutos.', 'info')
        generate_video(intro_path, product_image_paths, background_path, output_path, remove_bg)
        
        # Clean up uploaded files
        print("Limpiando archivos temporales...")
        for file_path in uploaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
        
        flash('¡Video generado exitosamente!', 'success')
        return render_template('index.html', video_filename=output_filename)
    
    except Exception as e:
        print(f"Error en generate_video_route: {e}")
        flash(f'Error al generar el video: {str(e)}', 'error')
        
        # Clean up on error
        for file_path in uploaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        return redirect(url_for('index'))


@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve the generated video file."""
    return send_from_directory(app.config['VIDEOS_FOLDER'], filename, as_attachment=True)


if __name__ == '__main__':
    # Debug mode should only be enabled in development
    # Set FLASK_DEBUG=0 in production environment
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
