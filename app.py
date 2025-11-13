import os
import uuid
import io
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw
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
        
        # Remove background with alpha matting for better edge quality
        # alpha_matting helps improve edge detection and reduce excessive removal
        # Using relaxed parameters to ensure matrix stability and avoid Cholesky warnings
        # These settings prioritize stability while maintaining good edge quality
        output_bytes = remove(
            input_image, 
            alpha_matting=True, 
            alpha_matting_foreground_threshold=270,
            alpha_matting_background_threshold=30,
            alpha_matting_erode_size=15
        )
        
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
    Create a video clip with modern sliding carousel effect.
    Images scale down and slide to the side as they exit,
    while maintaining a smooth, modern transition.
    
    Args:
        image_path: Path to the image
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with modern carousel effect
    """
    try:
        # Load image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function for modern sliding with scale effect
        def position_func(t):
            # Progress from 0 to 1
            progress = t / duration
            
            # Calculate position for modern slide effect - increased distance for visibility
            if progress < 0.3:
                # Slide in from right - full width slide
                ease = progress / 0.3
                ease = 1 - (1 - ease) ** 3  # Ease-out cubic
                x = video_size[0] * (1 - ease)
                
            elif progress > 0.7:
                # Slide out to left - full width slide
                ease = (progress - 0.7) / 0.3
                ease = ease ** 3  # Ease-in cubic
                x = -video_size[0] * ease
                
            else:
                # Stay centered
                x = 0
            
            return (x, 'center')
        
        # Define resize function for scale effect
        def resize_func(t):
            # Progress from 0 to 1
            progress = t / duration
            
            # Calculate scale for modern effect - more dramatic scaling
            if progress < 0.3:
                # Scale up from 70% to 100%
                ease = progress / 0.3
                ease = 1 - (1 - ease) ** 3  # Ease-out cubic
                scale = 0.7 + (0.3 * ease)
                
            elif progress > 0.7:
                # Scale down from 100% to 70%
                ease = (progress - 0.7) / 0.3
                ease = ease ** 3  # Ease-in cubic
                scale = 1.0 - (0.3 * ease)
                
            else:
                # Stay at full size
                scale = 1.0
            
            return scale
        
        # Apply position
        clip = clip.set_position(position_func)
        
        # Apply resize animation
        clip = clip.resize(resize_func)
        
        # Note: No crossfade applied to preserve the transition effect
        
        return clip
    
    except Exception as e:
        print(f"Error creating carousel clip: {e}")
        raise


def create_card_transition_clip(image_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with card-style transition (fade + slide effect).
    Images fade out while sliding to the side, then fade in from the other side.
    
    Args:
        image_path: Path to the image
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with card transition effect
    """
    try:
        # Load image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function for slide effect
        def position_func(t):
            progress = t / duration
            
            if progress < 0.3:
                # Slide in from left with fade in - full width slide
                ease = progress / 0.3
                ease = 1 - (1 - ease) ** 2  # Ease-out
                x = -video_size[0] * (1 - ease)
            elif progress > 0.7:
                # Slide out to right with fade out - full width slide
                ease = (progress - 0.7) / 0.3
                ease = ease ** 2  # Ease-in
                x = video_size[0] * ease
            else:
                # Stay centered
                x = 0
            
            return (x, 'center')
        
        # Define opacity function for fade effect
        def opacity_func(t):
            progress = t / duration
            
            if progress < 0.3:
                # Fade in over 30% of duration
                return progress / 0.3
            elif progress > 0.7:
                # Fade out over last 30% of duration
                return 1 - ((progress - 0.7) / 0.3)
            else:
                # Full opacity
                return 1.0
        
        # Apply position and opacity
        print(f"DEBUG: Applying position_func: {type(position_func)}")
        clip = clip.set_position(position_func)
        print(f"DEBUG: Position applied successfully")
        print(f"DEBUG: Applying opacity_func: {type(opacity_func)}")
        clip = clip.set_opacity(opacity_func)
        print(f"DEBUG: Opacity applied successfully")
        
        return clip
    
    except Exception as e:
        print(f"Error creating card transition clip: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise


def create_filmstrip_transition_clip(image_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with film strip transition (vintage camera negative effect).
    Images resize with a film negative border effect, simulating scrolling through film.
    
    Args:
        image_path: Path to the image
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with film strip transition effect
    """
    try:
        # Load and prepare the main image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        
        # Create film strip frame effect
        # Add dark borders to simulate film negative
        border_size = int(video_size[1] * 0.08)  # 8% of height for borders
        
        # Create a darker background for film effect
        film_bg = Image.new('RGB', video_size, (40, 35, 30))  # Dark brownish
        
        # Calculate image size with borders
        img_height = video_size[1] - (2 * border_size)
        img_width = video_size[0]
        img_resized = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        # Paste image on film background
        film_bg.paste(img_resized, (0, border_size))
        
        # Add film sprocket holes effect (small rectangles on borders)
        draw = ImageDraw.Draw(film_bg)
        hole_width = int(video_size[0] * 0.03)
        hole_height = int(border_size * 0.6)
        hole_color = (0, 0, 0)
        
        # Top border holes
        for i in range(0, video_size[0], int(video_size[0] * 0.1)):
            draw.rectangle([i, border_size//4, i + hole_width, border_size//4 + hole_height], fill=hole_color)
        
        # Bottom border holes
        for i in range(0, video_size[0], int(video_size[0] * 0.1)):
            y_pos = video_size[1] - border_size + border_size//4
            draw.rectangle([i, y_pos, i + hole_width, y_pos + hole_height], fill=hole_color)
        
        img_array = np.array(film_bg)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function for vertical scrolling effect
        def position_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Scroll in from bottom - more dramatic movement
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 2  # Ease-out
                y = video_size[1] * (1 - ease)
            elif progress > 0.65:
                # Scroll out to top - more dramatic movement
                ease = (progress - 0.65) / 0.35
                ease = ease ** 2  # Ease-in
                y = -video_size[1] * ease
            else:
                # Stay centered
                y = 0
            
            return ('center', y)
        
        # Define resize function for zoom effect
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Zoom in from 75% to 100% - more dramatic
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 2
                scale = 0.75 + (0.25 * ease)
            elif progress > 0.65:
                # Zoom out from 100% to 75% - more dramatic
                ease = (progress - 0.65) / 0.35
                ease = ease ** 2
                scale = 1.0 - (0.25 * ease)
            else:
                # Stay at full size
                scale = 1.0
            
            return scale
        
        # Apply effects
        clip = clip.set_position(position_func)
        clip = clip.resize(resize_func)
        
        # Note: No crossfade applied to preserve the filmstrip transition effect
        
        return clip
    
    except Exception as e:
        print(f"Error creating filmstrip transition clip: {e}")
        raise


def generate_video(intro_path, product_images, background_image_path, output_path, remove_bg=True, transition_type='carousel'):
    """
    Generate the final video with intro and product images using selected transition effect.
    
    Args:
        intro_path: Path to intro video
        product_images: List of paths to product images
        background_image_path: Path to custom background image (can be None)
        output_path: Path to save the output video
        remove_bg: Whether to remove background from images (default: True)
        transition_type: Type of transition ('carousel', 'card', or 'filmstrip')
    
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
            
            # Create clip with selected transition effect
            if transition_type == 'card':
                transition_clip = create_card_transition_clip(processed_image_path, duration=3, video_size=video_size)
            elif transition_type == 'filmstrip':
                transition_clip = create_filmstrip_transition_clip(processed_image_path, duration=3, video_size=video_size)
            else:  # default to carousel
                transition_clip = create_carousel_clip(processed_image_path, duration=3, video_size=video_size)
            
            clips.append(transition_clip)
        
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
        
        # Get transition type selection
        transition_type = request.form.get('transition_type', 'carousel')
        
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
        generate_video(intro_path, product_image_paths, background_path, output_path, remove_bg, transition_type)
        
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
