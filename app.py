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
    Create a video clip with dramatic CapCut-style carousel effect.
    Images slide with 3D-like perspective, rotation, and smooth scaling.
    
    Args:
        image_path: Path to the image
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with dramatic carousel effect
    """
    try:
        # Load image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function with dramatic sliding and perspective
        def position_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Dramatic slide in from right with acceleration
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4  # Ease-out quartic for smooth deceleration
                x = video_size[0] * 1.5 * (1 - ease)  # Start from 1.5x width for drama
                
            elif progress > 0.65:
                # Dramatic slide out to left with acceleration
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4  # Ease-in quartic for acceleration
                x = -video_size[0] * 1.5 * ease  # Exit to -1.5x width
                
            else:
                # Stay perfectly centered
                x = 0
            
            return (x, 'center')
        
        # Define resize function with dramatic scaling
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Zoom in dramatically from 60% to 105% (slight overshoot)
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4  # Ease-out quartic
                scale = 0.6 + (0.45 * ease)
                
            elif progress > 0.65:
                # Zoom out dramatically from 105% to 60%
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4  # Ease-in quartic
                scale = 1.05 - (0.45 * ease)
                
            else:
                # Stay at 105% for emphasis
                scale = 1.05
            
            return scale
        
        # Apply position and resize for dramatic effect
        clip = clip.set_position(position_func)
        clip = clip.resize(resize_func)
        
        return clip
    
    except Exception as e:
        print(f"Error creating carousel clip: {e}")
        raise


def create_card_transition_clip(image_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with dramatic card-flip style transition.
    Images slide with perspective and scaling for a modern CapCut look.
    
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
        
        # Define position function for card-flip slide effect
        def position_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Slide in from bottom-left with curve
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4  # Ease-out quartic
                x = -video_size[0] * 0.8 * (1 - ease)
                y = video_size[1] * 0.4 * (1 - ease)
            elif progress > 0.65:
                # Slide out to top-right with curve
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4  # Ease-in quartic
                x = video_size[0] * 0.8 * ease
                y = -video_size[1] * 0.4 * ease
            else:
                # Stay centered
                x = 0
                y = 0
            
            return (x, y)
        
        # Define resize function for dramatic zoom
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Zoom in from 50% to 110% for impact
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4
                scale = 0.5 + (0.6 * ease)
            elif progress > 0.65:
                # Zoom out from 110% to 50%
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4
                scale = 1.1 - (0.6 * ease)
            else:
                # Stay at 110% for emphasis
                scale = 1.1
            
            return scale
        
        # Apply position and scaling
        clip = clip.set_position(position_func)
        clip = clip.resize(resize_func)
        
        return clip
    
    except Exception as e:
        print(f"Error creating card transition clip: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise


def create_filmstrip_transition_clip(image_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with dramatic vintage film strip effect.
    Vertical scrolling with cinematic borders and sprocket holes.
    
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
        
        # Create film strip frame effect with vintage borders
        border_size = int(video_size[1] * 0.08)  # 8% of height for borders
        
        # Create vintage film background
        film_bg = Image.new('RGB', video_size, (35, 30, 25))  # Dark brownish-gray
        
        # Calculate image size with borders
        img_height = video_size[1] - (2 * border_size)
        img_width = video_size[0]
        img_resized = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
        
        # Paste image on film background
        film_bg.paste(img_resized, (0, border_size))
        
        # Add film sprocket holes effect (authentic film perforations)
        draw = ImageDraw.Draw(film_bg)
        hole_width = int(video_size[0] * 0.04)
        hole_height = int(border_size * 0.65)
        hole_color = (0, 0, 0)
        
        # Top border holes - evenly spaced
        for i in range(0, video_size[0], int(video_size[0] * 0.08)):
            draw.rectangle([i, border_size//4, i + hole_width, border_size//4 + hole_height], fill=hole_color)
        
        # Bottom border holes - evenly spaced
        for i in range(0, video_size[0], int(video_size[0] * 0.08)):
            y_pos = video_size[1] - border_size + border_size//4
            draw.rectangle([i, y_pos, i + hole_width, y_pos + hole_height], fill=hole_color)
        
        img_array = np.array(film_bg)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        # Define position function for cinematic vertical scrolling
        def position_func(t):
            progress = t / duration
            
            if progress < 0.4:
                # Dramatic scroll in from bottom
                ease = progress / 0.4
                ease = 1 - (1 - ease) ** 4  # Ease-out quartic for smooth stop
                y = video_size[1] * 1.3 * (1 - ease)
            elif progress > 0.6:
                # Dramatic scroll out to top
                ease = (progress - 0.6) / 0.4
                ease = ease ** 4  # Ease-in quartic for acceleration
                y = -video_size[1] * 1.3 * ease
            else:
                # Hold centered for impact
                y = 0
            
            return ('center', y)
        
        # Define resize function for cinematic zoom
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.4:
                # Cinematic zoom in from 65% to 108%
                ease = progress / 0.4
                ease = 1 - (1 - ease) ** 3
                scale = 0.65 + (0.43 * ease)
            elif progress > 0.6:
                # Cinematic zoom out from 108% to 65%
                ease = (progress - 0.6) / 0.4
                ease = ease ** 3
                scale = 1.08 - (0.43 * ease)
            else:
                # Hold at 108% for cinematic effect
                scale = 1.08
            
            return scale
        
        # Apply cinematic effects
        clip = clip.set_position(position_func)
        clip = clip.resize(resize_func)
        
        # Note: No crossfade applied to preserve the filmstrip transition effect
        
        return clip
    
    except Exception as e:
        print(f"Error creating filmstrip transition clip: {e}")
        raise


def create_product_animation_clip(image_path, duration=5, video_size=(1920, 1080), animation_type='rotate'):
    """
    Create an animated video clip of a single product with rotation or movement.
    
    Args:
        image_path: Path to the processed product image
        duration: Duration of the animation in seconds
        video_size: Size of the video (width, height)
        animation_type: Type of animation ('rotate', 'zoom', 'float', 'spin_zoom')
    
    Returns:
        VideoClip: The created animated video clip
    """
    try:
        # Load image
        img = Image.open(image_path)
        img = img.resize(video_size, Image.Resampling.LANCZOS)
        img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration)
        
        if animation_type == 'rotate':
            # 360-degree rotation
            def rotate_func(t):
                angle = (t / duration) * 360
                return angle
            
            clip = clip.rotate(rotate_func)
            
        elif animation_type == 'zoom':
            # Zoom in and out effect
            def resize_func(t):
                progress = t / duration
                # Smooth zoom in then zoom out
                if progress < 0.5:
                    scale = 0.8 + (0.4 * (progress / 0.5))
                else:
                    scale = 1.2 - (0.4 * ((progress - 0.5) / 0.5))
                return scale
            
            clip = clip.resize(resize_func)
            
        elif animation_type == 'float':
            # Floating up and down effect
            def position_func(t):
                progress = t / duration
                # Smooth sine wave motion
                y_offset = np.sin(progress * 4 * np.pi) * (video_size[1] * 0.1)
                return ('center', 'center' if isinstance('center', str) else video_size[1]//2 + y_offset)
            
            def resize_func(t):
                progress = t / duration
                # Subtle scale with float
                scale = 1.0 + (np.sin(progress * 4 * np.pi) * 0.1)
                return scale
            
            clip = clip.set_position(lambda t: ('center', video_size[1]//2 + np.sin((t/duration) * 4 * np.pi) * (video_size[1] * 0.1)))
            clip = clip.resize(resize_func)
            
        elif animation_type == 'spin_zoom':
            # Combined rotation and zoom effect
            def rotate_func(t):
                angle = (t / duration) * 720  # Two full rotations
                return angle
            
            def resize_func(t):
                progress = t / duration
                # Zoom in during first half, zoom out during second half
                if progress < 0.5:
                    scale = 0.7 + (0.6 * (progress / 0.5))
                else:
                    scale = 1.3 - (0.6 * ((progress - 0.5) / 0.5))
                return scale
            
            clip = clip.rotate(rotate_func)
            clip = clip.resize(resize_func)
        
        return clip
    
    except Exception as e:
        print(f"Error creating product animation clip: {e}")
        raise


def generate_product_video(product_image_path, background_image_path, output_path, 
                          duration=5, animation_type='rotate', video_size=(1920, 1080)):
    """
    Generate an animated video from a single product image.
    
    Args:
        product_image_path: Path to the product image
        background_image_path: Path to custom background image (can be None)
        output_path: Path to save the output video
        duration: Duration of the animation in seconds (default: 5)
        animation_type: Type of animation ('rotate', 'zoom', 'float', 'spin_zoom')
        video_size: Size of the video (width, height)
    
    Returns:
        str: Path to the generated video
    """
    processed_image_path = None
    
    try:
        # Create processed image path
        processed_image_path = os.path.join(
            UPLOAD_FOLDER, 
            f"processed_{uuid.uuid4().hex}.jpg"
        )
        
        # Remove background and composite
        print("Removing background and compositing image...")
        remove_background_and_composite(
            product_image_path, 
            background_image_path, 
            processed_image_path,
            video_size
        )
        
        # Create animated clip
        print(f"Creating animated video with {animation_type} effect...")
        animated_clip = create_product_animation_clip(
            processed_image_path, 
            duration=duration, 
            video_size=video_size,
            animation_type=animation_type
        )
        
        # Write final video
        print("Rendering final video...")
        animated_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            threads=4
        )
        
        # Close clip to release resources
        animated_clip.close()
        
        print("Product video generation complete!")
        return output_path
    
    except Exception as e:
        print(f"Error generating product video: {e}")
        raise
    
    finally:
        # Clean up processed image
        if processed_image_path and os.path.exists(processed_image_path):
            try:
                os.remove(processed_image_path)
            except Exception as e:
                print(f"Warning: Could not delete processed image {processed_image_path}: {e}")


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


@app.route('/generate_product_video', methods=['POST'])
def generate_product_video_route():
    """Handle single product animation video generation request."""
    uploaded_files = []
    
    try:
        # Check if product image is present
        if 'product_image' not in request.files:
            flash('No se encontró la imagen del producto', 'error')
            return redirect(url_for('index'))
        
        product_image = request.files['product_image']
        custom_background = request.files.get('product_background')
        
        # Get animation type and duration
        animation_type = request.form.get('animation_type', 'rotate')
        duration = int(request.form.get('duration', 5))
        
        # Validate product image
        if product_image.filename == '':
            flash('No se seleccionó una imagen de producto', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(product_image.filename, 'image'):
            flash('Formato de imagen no válido. Use PNG, JPG o JPEG', 'error')
            return redirect(url_for('index'))
        
        # Save product image
        print("Guardando imagen de producto...")
        product_filename = f"{uuid.uuid4().hex}_{secure_filename(product_image.filename)}"
        product_path = os.path.join(app.config['UPLOAD_FOLDER'], product_filename)
        product_image.save(product_path)
        uploaded_files.append(product_path)
        
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
        output_filename = f"product_video_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['VIDEOS_FOLDER'], output_filename)
        
        # Generate product video
        print("Iniciando generación de video del producto...")
        flash('Procesando video del producto... Esto puede tomar algunos minutos.', 'info')
        generate_product_video(
            product_path, 
            background_path, 
            output_path,
            duration=duration,
            animation_type=animation_type
        )
        
        # Clean up uploaded files
        print("Limpiando archivos temporales...")
        for file_path in uploaded_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
        
        flash('¡Video del producto generado exitosamente!', 'success')
        return render_template('index.html', video_filename=output_filename)
    
    except Exception as e:
        print(f"Error en generate_product_video_route: {e}")
        flash(f'Error al generar el video del producto: {str(e)}', 'error')
        
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
