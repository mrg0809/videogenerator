import os
import uuid
import io
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw
from rembg import remove
import numpy as np
import cv2

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


def is_video_file(filename):
    """
    Check if a file is a video based on its extension.
    
    Args:
        filename: Name of the file
    
    Returns:
        bool: True if the file is a video, False otherwise
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


def remove_background_only(product_image_path, output_path, target_size=(1920, 1080)):
    """
    Remove background from product image and save with transparency.
    
    Args:
        product_image_path: Path to the product image
        output_path: Path to save the result (PNG with alpha)
        target_size: Target size for the output image (width, height)
    
    Returns:
        str: Path to the processed image with transparency
    """
    try:
        # Load product image
        with open(product_image_path, 'rb') as f:
            input_image = f.read()
        
        # Remove background with alpha matting for better edge quality
        output_bytes = remove(
            input_image, 
            alpha_matting=True, 
            alpha_matting_foreground_threshold=270,
            alpha_matting_background_threshold=30,
            alpha_matting_erode_size=15
        )
        
        # Convert bytes to PIL Image using BytesIO
        product_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        
        # Scale product to fit within target size while maintaining aspect ratio
        product_width, product_height = product_img.size
        bg_width, bg_height = target_size
        
        # Calculate scaling factor (use 80% of background size max)
        scale_factor = min((bg_width * 0.8) / product_width, (bg_height * 0.8) / product_height)
        new_width = int(product_width * scale_factor)
        new_height = int(product_height * scale_factor)
        
        product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a transparent canvas of the target size
        transparent_canvas = Image.new('RGBA', target_size, (0, 0, 0, 0))
        
        # Calculate position to center the product
        x = (bg_width - new_width) // 2
        y = (bg_height - new_height) // 2
        
        # Paste product onto transparent canvas
        transparent_canvas.paste(product_img, (x, y), product_img)
        
        # Save as PNG to preserve transparency
        transparent_canvas.save(output_path, 'PNG')
        
        return output_path
    
    except Exception as e:
        print(f"Error removing background: {e}")
        raise


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


def load_and_prepare_video_background(background_video_path, duration, video_size):
    """
    Load a video file and prepare it as a background clip.
    Loops or trims the video to match the target duration.
    
    Args:
        background_video_path: Path to the background video
        duration: Target duration in seconds
        video_size: Target size (width, height)
    
    Returns:
        VideoClip: Prepared background video clip
    """
    # Load background video
    bg_video = VideoFileClip(background_video_path)
    
    # Resize background video to match target size
    bg_video = bg_video.resize(video_size)
    
    # Loop or trim the background video to match duration
    if bg_video.duration < duration:
        # Use MoviePy's loop functionality for memory efficiency
        bg_video = bg_video.loop(duration=duration)
    else:
        bg_video = bg_video.subclip(0, duration)
    
    return bg_video


def create_carousel_clip_with_video_bg(product_image_path, background_video_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with carousel effect and a video background.
    
    Args:
        product_image_path: Path to the product image (already processed with transparent background at target size)
        background_video_path: Path to the background video
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with video background and carousel effect
    """
    try:
        # Load and prepare background video using helper function
        bg_video = load_and_prepare_video_background(background_video_path, duration, video_size)
        
        # Load product image with transparency (already scaled and centered from remove_background_only)
        product_img = Image.open(product_image_path).convert("RGBA")
        
        # Convert to numpy array for MoviePy
        product_array = np.array(product_img)
        
        # Create product clip with the same duration
        # The image is already at video_size with the product centered
        product_clip = ImageClip(product_array, duration=duration, ismask=False)
        
        # Define position function with carousel effect (slide in/out animation)
        def position_func(t):
            progress = t / duration
            
            if progress < 0.35:
                # Slide in from right
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4
                x = video_size[0] * 1.5 * (1 - ease)
            elif progress > 0.65:
                # Slide out to left
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4
                x = -video_size[0] * 1.5 * ease
            else:
                x = 0
            
            return (x, 0)  # Y is 0 since image is already centered on the canvas
        
        # Define resize function for zoom effect
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.35:
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4
                scale = 0.8 + (0.25 * ease)  # Start at 80%, end at 105%
            elif progress > 0.65:
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4
                scale = 1.05 - (0.25 * ease)  # 105% to 80%
            else:
                scale = 1.05  # Hold at 105%
            
            return scale
        
        # Apply position and resize
        product_clip = product_clip.set_position(position_func)
        product_clip = product_clip.resize(resize_func)
        
        # Composite product over background
        final_clip = CompositeVideoClip([bg_video, product_clip], size=video_size)
        
        return final_clip
    
    except Exception as e:
        print(f"Error creating carousel clip with video background: {e}")
        raise


def create_card_clip_with_video_bg(product_image_path, background_video_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with card transition effect and a video background.
    
    Args:
        product_image_path: Path to the product image (already processed with transparent background at target size)
        background_video_path: Path to the background video
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with video background and card effect
    """
    try:
        # Load and prepare background video using helper function
        bg_video = load_and_prepare_video_background(background_video_path, duration, video_size)
        
        # Load product image with transparency (already scaled and centered from remove_background_only)
        product_img = Image.open(product_image_path).convert("RGBA")
        product_array = np.array(product_img)
        
        # Create product clip - image is already at video_size with product centered
        product_clip = ImageClip(product_array, duration=duration, ismask=False)
        
        # Card transition position function
        def position_func(t):
            progress = t / duration
            
            if progress < 0.35:
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4
                x = -video_size[0] * 0.8 * (1 - ease)
                y = video_size[1] * 0.4 * (1 - ease)
            elif progress > 0.65:
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4
                x = video_size[0] * 0.8 * ease
                y = -video_size[1] * 0.4 * ease
            else:
                x = 0
                y = 0
            
            return (x, y)  # Position relative to origin since image is already centered on the canvas
        
        # Card resize function
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.35:
                ease = progress / 0.35
                ease = 1 - (1 - ease) ** 4
                scale = 0.7 + (0.4 * ease)  # Start at 70%, end at 110%
            elif progress > 0.65:
                ease = (progress - 0.65) / 0.35
                ease = ease ** 4
                scale = 1.1 - (0.4 * ease)  # 110% to 70%
            else:
                scale = 1.1  # Hold at 110%
            
            return scale
        
        product_clip = product_clip.set_position(position_func)
        product_clip = product_clip.resize(resize_func)
        
        final_clip = CompositeVideoClip([bg_video, product_clip], size=video_size)
        
        return final_clip
    
    except Exception as e:
        print(f"Error creating card clip with video background: {e}")
        raise


def create_filmstrip_clip_with_video_bg(product_image_path, background_video_path, duration=3, video_size=(1920, 1080)):
    """
    Create a video clip with filmstrip transition effect and a video background.
    
    Args:
        product_image_path: Path to the product image (already processed with transparent background at target size)
        background_video_path: Path to the background video
        duration: Duration of the clip in seconds
        video_size: Size of the video (width, height)
    
    Returns:
        VideoClip: The created video clip with video background and filmstrip effect
    """
    try:
        # Load and prepare background video using helper function
        bg_video = load_and_prepare_video_background(background_video_path, duration, video_size)
        
        # Load product image with transparency (already scaled and centered from remove_background_only)
        product_img = Image.open(product_image_path).convert("RGBA")
        product_array = np.array(product_img)
        
        # Create product clip - image is already at video_size with product centered
        product_clip = ImageClip(product_array, duration=duration, ismask=False)
        
        # Filmstrip position function (vertical scrolling)
        def position_func(t):
            progress = t / duration
            
            if progress < 0.4:
                ease = progress / 0.4
                ease = 1 - (1 - ease) ** 4
                y = video_size[1] * 1.3 * (1 - ease)
            elif progress > 0.6:
                ease = (progress - 0.6) / 0.4
                ease = ease ** 4
                y = -video_size[1] * 1.3 * ease
            else:
                y = 0
            
            return (0, y)  # X is 0 since image is already centered on the canvas
        
        # Filmstrip resize function
        def resize_func(t):
            progress = t / duration
            
            if progress < 0.4:
                ease = progress / 0.4
                ease = 1 - (1 - ease) ** 3
                scale = 0.75 + (0.33 * ease)  # Start at 75%, end at 108%
            elif progress > 0.6:
                ease = (progress - 0.6) / 0.4
                ease = ease ** 3
                scale = 1.08 - (0.33 * ease)  # 108% to 75%
            else:
                scale = 1.08  # Hold at 108%
            
            return scale
        
        product_clip = product_clip.set_position(position_func)
        product_clip = product_clip.resize(resize_func)
        
        final_clip = CompositeVideoClip([bg_video, product_clip], size=video_size)
        
        return final_clip
    
    except Exception as e:
        print(f"Error creating filmstrip clip with video background: {e}")
        raise


def create_product_animation_clip(image_path, duration=5, video_size=(1920, 1080), animation_type='rotate', bg_color=(255, 255, 255)):
    """
    Create an animated video clip of a single product with rotation or movement.
    
    Args:
        image_path: Path to the processed product image (PNG with transparency for rotation)
        duration: Duration of the animation in seconds
        video_size: Size of the video (width, height)
        animation_type: Type of animation ('rotate', 'zoom', 'float', 'spin_zoom')
        bg_color: Background color as RGB tuple (default: white)
    
    Returns:
        VideoClip: The created animated video clip
    """
    try:
        # Load image - keep original size for transparency
        img = Image.open(image_path)
        
        # For rotation animations, we need to preserve transparency
        if animation_type in ['rotate', 'spin_zoom']:
            # Keep RGBA for transparency
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img_array = np.array(img)
        else:
            # For non-rotation animations, resize to video size
            img = img.resize(video_size, Image.Resampling.LANCZOS)
            img_array = np.array(img)
        
        # Create ImageClip
        clip = ImageClip(img_array, duration=duration).set_duration(duration)
        
        if animation_type == 'rotate':
            # 360-degree rotation
            def rotate_func(t):
                angle = (t / duration) * 360
                return angle
            
            # Create a static background layer with the matching color
            background_clip = ColorClip(size=video_size, color=bg_color, duration=duration)
            
            # Rotate just the product image (with transparency)
            # Using expand=False to keep the canvas size constant
            rotated_clip = clip.rotate(rotate_func, expand=False)
            
            # Set the rotated clip to be centered and with transparency
            rotated_clip = rotated_clip.set_position('center')
            
            # Composite the rotated product on top of the static background
            clip = CompositeVideoClip([background_clip, rotated_clip], size=video_size)
            
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
            
            # Create a static background layer with the matching color
            background_clip = ColorClip(size=video_size, color=bg_color, duration=duration)
            
            # Rotate just the product image (with transparency), keeping canvas size constant
            rotated_clip = clip.rotate(rotate_func, expand=False)
            
            # Apply zoom effect
            resized_clip = rotated_clip.resize(resize_func)
            
            # Set position to center
            resized_clip = resized_clip.set_position('center')
            
            # Composite the rotated/resized product on top of the static background
            clip = CompositeVideoClip([background_clip, resized_clip], size=video_size)
        
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
        # Determine background color
        if background_image_path and os.path.exists(background_image_path):
            # Get average color from custom background
            bg_img = Image.open(background_image_path)
            bg_img_resized = bg_img.resize((100, 100))  # Resize for faster processing
            bg_array = np.array(bg_img_resized)
            bg_color = tuple(bg_array.mean(axis=(0, 1)).astype(int).tolist()[:3])
            bg_img.close()
        else:
            # Default white background
            bg_color = (255, 255, 255)
        
        # For rotation animations, we need transparency preserved
        if animation_type in ['rotate', 'spin_zoom']:
            # Create processed image path as PNG to preserve transparency
            processed_image_path = os.path.join(
                UPLOAD_FOLDER, 
                f"processed_{uuid.uuid4().hex}.png"
            )
            
            # Remove background only (keep transparency)
            print("Removing background (keeping transparency for rotation)...")
            remove_background_only(
                product_image_path,
                processed_image_path,
                video_size
            )
        else:
            # For other animations, composite onto background
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
            animation_type=animation_type,
            bg_color=bg_color
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


def calculate_perspective_transform(width, height, angle_degrees, perspective_strength):
    """
    Calculate perspective transformation matrix for simulating 3D rotation.
    
    Args:
        width: Image width
        height: Image height
        angle_degrees: Rotation angle in degrees (0-360)
        perspective_strength: Strength of perspective effect (0.0-1.0)
    
    Returns:
        tuple: (transform_matrix, new_width, new_height) for cv2.warpPerspective
    """
    # Normalize angle to 0-360
    angle = angle_degrees % 360
    
    # Calculate perspective distortion based on angle
    # Maximum distortion at 90° and 270° (side views)
    # Minimum distortion at 0°, 180°, 360° (front/back views)
    angle_rad = np.radians(angle)
    
    # Use sine to create smooth perspective transition
    # At 0° and 180°, cos is ±1 (front view, no perspective)
    # At 90° and 270°, cos is 0 (side view, maximum perspective)
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    
    # Calculate horizontal scale factor based on angle
    # Objects appear narrower when viewed from the side
    h_scale = 1.0 - (abs(sin_angle) * perspective_strength * 0.7)
    
    # Calculate perspective tilt
    # Positive angles tilt right, negative tilt left
    tilt_factor = sin_angle * perspective_strength * 0.3
    
    # Define source points (original image corners)
    src_pts = np.float32([
        [0, 0],              # Top-left
        [width, 0],          # Top-right
        [width, height],     # Bottom-right
        [0, height]          # Bottom-left
    ])
    
    # Calculate new dimensions with padding for rotation
    new_width = int(width * 1.5)
    new_height = int(height * 1.2)
    
    # Center offset
    x_offset = (new_width - width) / 2
    y_offset = (new_height - height) / 2
    
    # Calculate destination points with perspective distortion
    # Apply horizontal scaling and perspective tilt
    dst_pts = np.float32([
        [x_offset + width * (1 - h_scale) / 2 + height * tilt_factor * 0.1,
         y_offset],
        [x_offset + width - width * (1 - h_scale) / 2 + height * tilt_factor * 0.1,
         y_offset],
        [x_offset + width - width * (1 - h_scale) / 2 - height * tilt_factor * 0.1,
         y_offset + height],
        [x_offset + width * (1 - h_scale) / 2 - height * tilt_factor * 0.1,
         y_offset + height]
    ])
    
    # Get perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    return matrix, new_width, new_height


def calculate_smooth_orbital_perspective(width, height, camera_angle_degrees, perspective_strength):
    """
    Calculate smooth perspective transformation for orbital camera effect.
    Uses progressive transformations for fluid motion.
    
    Args:
        width: Image width
        height: Image height
        camera_angle_degrees: Camera position angle in degrees (0-360)
        perspective_strength: Strength of perspective effect (0.0-1.0)
    
    Returns:
        tuple: (transform_matrix, new_width, new_height) for cv2.warpPerspective
    """
    # Normalize angle to 0-360
    angle = camera_angle_degrees % 360
    angle_rad = np.radians(angle)
    
    # Use smooth sinusoidal functions for natural motion
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    
    # Smoother horizontal scale variation (less aggressive)
    # Use squared sine for smoother transitions
    h_scale_factor = (sin_angle ** 2) * perspective_strength * 0.35
    h_scale = 1.0 - h_scale_factor
    
    # Very subtle vertical scaling for depth
    v_scale = 1.0 - (abs(sin_angle) * perspective_strength * 0.08)
    
    # Smooth perspective tilt (3D rotation effect)
    tilt_x = sin_angle * perspective_strength * 0.12
    tilt_y = cos_angle * perspective_strength * 0.04
    
    # Define source points (original image corners)
    src_pts = np.float32([
        [0, 0],              # Top-left
        [width, 0],          # Top-right
        [width, height],     # Bottom-right
        [0, height]          # Bottom-left
    ])
    
    # Calculate new dimensions with minimal padding
    new_width = int(width * 1.2)
    new_height = int(height * 1.1)
    
    # Center offset
    x_offset = (new_width - width) / 2
    y_offset = (new_height - height) / 2
    
    # Calculate scaled dimensions
    scaled_width = width * h_scale
    scaled_height = height * v_scale
    width_margin = (width - scaled_width) / 2
    height_margin = (height - scaled_height) / 2
    
    # Calculate destination points with smooth perspective
    dst_pts = np.float32([
        # Top-left - apply tilt
        [x_offset + width_margin + height * tilt_x * 0.5,
         y_offset + height_margin + width * tilt_y * 0.3],
        # Top-right - apply tilt
        [x_offset + width - width_margin + height * tilt_x * 0.5,
         y_offset + height_margin - width * tilt_y * 0.3],
        # Bottom-right - apply tilt
        [x_offset + width - width_margin - height * tilt_x * 0.5,
         y_offset + height - height_margin - width * tilt_y * 0.3],
        # Bottom-left - apply tilt
        [x_offset + width_margin - height * tilt_x * 0.5,
         y_offset + height - height_margin + width * tilt_y * 0.3]
    ])
    
    # Get perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    return matrix, new_width, new_height


def calculate_orbital_perspective_transform(width, height, camera_angle_degrees, perspective_strength):
    """
    Calculate perspective transformation for orbital camera effect.
    Simulates a camera rotating around a stationary product.
    
    Args:
        width: Image width
        height: Image height
        camera_angle_degrees: Camera position angle in degrees (0-360)
        perspective_strength: Strength of perspective effect (0.0-1.0)
    
    Returns:
        tuple: (transform_matrix, new_width, new_height) for cv2.warpPerspective
    """
    # Normalize angle to 0-360
    angle = camera_angle_degrees % 360
    angle_rad = np.radians(angle)
    
    # Calculate viewing angle effects
    # At 0°/360°: Camera in front, minimal perspective
    # At 90°: Camera at right side, maximum horizontal compression
    # At 180°: Camera at back, minimal perspective
    # At 270°: Camera at left side, maximum horizontal compression
    cos_angle = np.cos(angle_rad)
    sin_angle = np.sin(angle_rad)
    
    # Horizontal compression based on side viewing
    # Product appears narrower when viewed from the side
    h_compression = 1.0 - (abs(sin_angle) * perspective_strength * 0.6)
    
    # Vertical perspective tilt (less pronounced than horizontal)
    v_tilt = sin_angle * perspective_strength * 0.15
    
    # Horizontal shift to simulate orbital camera movement
    h_shift = sin_angle * perspective_strength * width * 0.1
    
    # Define source points (original image corners)
    src_pts = np.float32([
        [0, 0],              # Top-left
        [width, 0],          # Top-right
        [width, height],     # Bottom-right
        [0, height]          # Bottom-left
    ])
    
    # Calculate new dimensions with padding
    new_width = int(width * 1.3)
    new_height = int(height * 1.15)
    
    # Center offset
    x_offset = (new_width - width) / 2
    y_offset = (new_height - height) / 2
    
    # Calculate destination points for orbital perspective
    # Apply horizontal compression and subtle vertical tilt
    compressed_width = width * h_compression
    width_margin = (width - compressed_width) / 2
    
    dst_pts = np.float32([
        # Top-left
        [x_offset + width_margin + h_shift + height * v_tilt * 0.05,
         y_offset],
        # Top-right  
        [x_offset + width - width_margin + h_shift + height * v_tilt * 0.05,
         y_offset],
        # Bottom-right
        [x_offset + width - width_margin + h_shift - height * v_tilt * 0.05,
         y_offset + height],
        # Bottom-left
        [x_offset + width_margin + h_shift - height * v_tilt * 0.05,
         y_offset + height]
    ])
    
    # Get perspective transform matrix
    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    
    return matrix, new_width, new_height


def generate_multi_image_3d_spin_video(image_paths_dict, output_path, frames_per_rotation=60,
                                       perspective_strength=0.3, duration=None,
                                       video_size=(1080, 1920), bg_color=(255, 255, 255)):
    """
    Generate a 3D-like spin/rotation video from multiple product images showing different angles.
    
    Args:
        image_paths_dict: Dictionary with keys 'front', 'back', 'left', 'right' (only 'front' required)
        output_path: Path to save the output video
        frames_per_rotation: Number of frames for complete 360° rotation (default: 60)
        perspective_strength: Strength of perspective effect, 0.0-1.0 (default: 0.3)
        duration: Duration of video in seconds (default: calculated from frames_per_rotation)
        video_size: Output video size (width, height)
        bg_color: Background color as RGB tuple
    
    Returns:
        str: Path to the generated video
    """
    try:
        print(f"Starting multi-image 3D spin video generation...")
        print(f"Available views: {list(image_paths_dict.keys())}")
        print(f"Parameters: {frames_per_rotation} frames, perspective strength: {perspective_strength}")
        
        # Load all available images
        images = {}
        for view, path in image_paths_dict.items():
            if path and os.path.exists(path):
                img = Image.open(path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img_array = np.array(img)
                images[view] = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
                print(f"  Loaded {view} view: {images[view].shape}")
        
        if 'front' not in images:
            raise ValueError("Front view image is required")
        
        # Get reference dimensions from front image
        height, width = images['front'].shape[:2]
        
        # Calculate video duration (default: 30 fps)
        fps = 30
        if duration is None:
            duration = frames_per_rotation / fps
        
        # Clamp perspective strength to valid range
        perspective_strength = max(0.0, min(1.0, perspective_strength))
        
        # Generate frames with perspective transformation
        frames = []
        print(f"Generating {frames_per_rotation} frames...")
        
        for i in range(frames_per_rotation):
            # Calculate camera angle (orbital rotation around product)
            camera_angle = (i / frames_per_rotation) * 360
            
            # Get primary and secondary images for smooth blending
            current_img, next_img, blend_weight = select_image_for_angle_smooth(images, camera_angle)
            
            # For turntable effect: NO 2D rotation of the image!
            # Product stays upright, only perspective changes as camera orbits
            # Copy current image as-is (no rotation)
            img_to_transform = current_img.copy()
            
            # If blending between views, blend them first before perspective
            if next_img is not None and blend_weight > 0:
                # Blend between current and next image (both upright)
                alpha_curr = current_img[:, :, 3:4].astype(float) / 255.0 * (1.0 - blend_weight)
                alpha_next = next_img[:, :, 3:4].astype(float) / 255.0 * blend_weight
                alpha_total = alpha_curr + alpha_next
                alpha_total = np.maximum(alpha_total, 1e-5)  # Avoid division by zero
                
                # Blend RGB channels
                blended_rgb = (current_img[:, :, 0:3].astype(float) * alpha_curr +
                              next_img[:, :, 0:3].astype(float) * alpha_next) / alpha_total
                blended_alpha = (alpha_total * 255.0).clip(0, 255)
                
                img_to_transform = np.dstack([blended_rgb, blended_alpha]).astype(np.uint8)
            
            # Apply smooth orbital camera perspective transformation
            # This simulates camera moving around the stationary product
            perspective_matrix, new_width, new_height = calculate_smooth_orbital_perspective(
                width, height, camera_angle, perspective_strength
            )
            
            # Warp with perspective using high-quality interpolation
            warped = cv2.warpPerspective(img_to_transform, perspective_matrix,
                                        (new_width, new_height),
                                        flags=cv2.INTER_CUBIC,  # Higher quality
                                        borderMode=cv2.BORDER_CONSTANT,
                                        borderValue=(0, 0, 0, 0))
            
            # Create canvas with background color
            canvas = np.zeros((video_size[1], video_size[0], 4), dtype=np.uint8)
            canvas[:, :, 0:3] = bg_color[::-1]  # BGR format
            canvas[:, :, 3] = 255  # Full opacity for background
            
            # If warped image is larger than canvas, scale it down to fit
            if new_width > video_size[0] or new_height > video_size[1]:
                scale = min(video_size[0] / new_width, video_size[1] / new_height) * 0.95
                new_scaled_width = int(new_width * scale)
                new_scaled_height = int(new_height * scale)
                warped = cv2.resize(warped, (new_scaled_width, new_scaled_height), interpolation=cv2.INTER_LINEAR)
                new_width = new_scaled_width
                new_height = new_scaled_height
            
            # Calculate position to center the warped image
            y_offset = (video_size[1] - new_height) // 2
            x_offset = (video_size[0] - new_width) // 2
            
            # Ensure offsets are valid
            y_offset = max(0, y_offset)
            x_offset = max(0, x_offset)
            
            # Calculate boundaries for pasting
            y_end = min(y_offset + new_height, video_size[1])
            x_end = min(x_offset + new_width, video_size[0])
            
            warped_h = y_end - y_offset
            warped_w = x_end - x_offset
            
            # Composite warped image onto canvas with alpha blending
            alpha = warped[:warped_h, :warped_w, 3:4] / 255.0
            canvas[y_offset:y_end, x_offset:x_end, 0:3] = (
                canvas[y_offset:y_end, x_offset:x_end, 0:3] * (1 - alpha) +
                warped[:warped_h, :warped_w, 0:3] * alpha
            ).astype(np.uint8)
            
            # Convert BGRA to RGB for MoviePy
            frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGRA2RGB)
            frames.append(frame_rgb)
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{frames_per_rotation} frames...")
        
        print(f"All frames generated. Creating video...")
        
        # Create video from frames using MoviePy
        from moviepy.editor import ImageSequenceClip
        
        video_clip = ImageSequenceClip(frames, fps=fps)
        video_clip = video_clip.set_duration(duration)
        
        # Write video file
        print("Rendering final video...")
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio=False,
            fps=fps,
            preset='medium',
            threads=4
        )
        
        # Clean up
        video_clip.close()
        
        print("Multi-image 3D spin video generation complete!")
        return output_path
    
    except Exception as e:
        print(f"Error generating multi-image 3D spin video: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise


def select_image_for_angle_smooth(images, angle):
    """
    Select images for smooth blending based on rotation angle.
    Returns two images and a blend weight for seamless transitions.
    
    Args:
        images: Dictionary with keys 'front', 'back', 'left', 'right'
        angle: Current rotation angle (0-360)
    
    Returns:
        tuple: (current_image, next_image, blend_weight)
               blend_weight: 0.0 = use current only, 1.0 = use next only
    """
    # Normalize angle to 0-360
    angle = angle % 360
    
    # Define view centers
    view_angles = {
        'front': 0,
        'right': 90,
        'back': 180,
        'left': 270
    }
    
    # Find which two views we're between
    # Transition zone: 45° before and after each view center (smoother, longer transitions)
    transition_range = 45
    
    # Check each view
    for view_name, view_angle in view_angles.items():
        if view_name not in images:
            continue
            
        # Calculate angular distance (handling wraparound at 0/360)
        dist = abs(angle - view_angle)
        if dist > 180:
            dist = 360 - dist
            
        # If we're close to this view center
        if dist <= transition_range:
            # Determine next view for blending
            next_view = None
            if angle > view_angle or (view_angle == 0 and angle > 340):
                # Moving clockwise
                next_view_name = {
                    'front': 'right',
                    'right': 'back',
                    'back': 'left',
                    'left': 'front'
                }.get(view_name)
                next_view = images.get(next_view_name)
            elif angle < view_angle or (view_angle == 0 and angle < 20):
                # Moving counter-clockwise
                next_view_name = {
                    'front': 'left',
                    'left': 'back',
                    'back': 'right',
                    'right': 'front'
                }.get(view_name)
                next_view = images.get(next_view_name)
            
            # Calculate blend weight (0 at center, 1 at transition edge)
            blend_weight = dist / transition_range if next_view is not None else 0.0
            
            return images[view_name], next_view, blend_weight
    
    # Default: use front view without blending
    return images.get('front', images['front']), None, 0.0


def select_image_for_angle(images, angle):
    """
    Select the appropriate image based on rotation angle with smooth transitions.
    
    Args:
        images: Dictionary with keys 'front', 'back', 'left', 'right'
        angle: Current rotation angle (0-360)
    
    Returns:
        tuple: (selected_image, blend_factor) where blend_factor is 0.0-1.0
    """
    # Normalize angle to 0-360
    angle = angle % 360
    
    # Define angle ranges for each view (with transitions)
    # Front: 315-45° (0° center)
    # Right: 45-135° (90° center)
    # Back: 135-225° (180° center)
    # Left: 225-315° (270° center)
    
    if 0 <= angle < 45 or angle >= 315:
        # Front view
        return images.get('front', images['front']), 1.0
    
    elif 45 <= angle < 90:
        # Transition from front to right
        if 'right' in images:
            # Smooth transition
            transition = (angle - 45) / 45.0  # 0 to 1
            # For now, just use right image with full visibility
            return images['right'], 1.0
        else:
            # Fall back to front with fade
            fade = 1.0 - ((angle - 45) / 90.0)  # 1.0 to 0.5
            return images['front'], max(0.3, fade)
    
    elif 90 <= angle < 135:
        # Right view or transition to back
        if 'right' in images:
            return images['right'], 1.0
        elif 'back' in images and angle > 112:
            # Transition towards back
            return images['back'], 0.7
        else:
            # Fade front image
            return images['front'], 0.3
    
    elif 135 <= angle < 225:
        # Back view
        if 'back' in images:
            return images['back'], 1.0
        else:
            # Use front image flipped horizontally with fade
            front_img = images['front']
            # Flip horizontally
            flipped = cv2.flip(front_img, 1)
            # Calculate fade (minimum at 180°)
            angle_from_back = abs(180 - angle)
            fade = angle_from_back / 45.0  # 0.0 at 180°, 1.0 at 135°/225°
            fade = max(0.1, min(1.0, fade))
            return flipped, fade
    
    elif 225 <= angle < 270:
        # Transition from back to left
        if 'left' in images:
            return images['left'], 1.0
        elif 'back' in images:
            return images['back'], 0.7
        else:
            return images['front'], 0.3
    
    else:  # 270 <= angle < 315
        # Left view or transition to front
        if 'left' in images:
            return images['left'], 1.0
        elif angle > 292:
            # Transition towards front
            return images['front'], 0.8
        else:
            return images['front'], 0.4


def generate_3d_spin_video(image_path, output_path, frames_per_rotation=60, 
                          perspective_strength=0.3, duration=None, 
                          video_size=(1080, 1920), bg_color=(255, 255, 255)):
    """
    Generate a 3D-like spin/rotation video from a product image using perspective transformations.
    
    Args:
        image_path: Path to the product image (should have transparent background)
        output_path: Path to save the output video
        frames_per_rotation: Number of frames for complete 360° rotation (default: 60)
        perspective_strength: Strength of perspective effect, 0.0-1.0 (default: 0.3)
        duration: Duration of video in seconds (default: calculated from frames_per_rotation)
        video_size: Output video size (width, height)
        bg_color: Background color as RGB tuple
    
    Returns:
        str: Path to the generated video
    """
    try:
        print(f"Starting 3D spin video generation...")
        print(f"Parameters: {frames_per_rotation} frames, perspective strength: {perspective_strength}")
        
        # Load image with transparency
        img = Image.open(image_path)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Convert PIL to OpenCV format (BGRA)
        img_array = np.array(img)
        img_bgra = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGRA)
        
        # Get image dimensions
        height, width = img_bgra.shape[:2]
        
        # Calculate video duration (default: 30 fps)
        fps = 30
        if duration is None:
            duration = frames_per_rotation / fps
        
        # Clamp perspective strength to valid range
        perspective_strength = max(0.0, min(1.0, perspective_strength))
        
        # Generate frames with perspective transformation
        frames = []
        print(f"Generating {frames_per_rotation} frames...")
        
        for i in range(frames_per_rotation):
            # Calculate camera angle (orbital rotation around product)
            camera_angle = (i / frames_per_rotation) * 360
            
            # For turntable effect: NO 2D rotation!
            # Product stays upright on turntable, only camera perspective changes
            # Use image as-is (upright), only apply perspective transformation
            
            # Apply smooth orbital camera perspective transformation
            # This simulates camera orbiting around stationary upright product
            perspective_matrix, new_width, new_height = calculate_smooth_orbital_perspective(
                width, height, camera_angle, perspective_strength
            )
            
            # Warp with perspective using high-quality interpolation
            warped = cv2.warpPerspective(img_bgra, perspective_matrix, 
                                        (new_width, new_height),
                                        flags=cv2.INTER_CUBIC,  # Higher quality
                                        borderMode=cv2.BORDER_CONSTANT,
                                        borderValue=(0, 0, 0, 0))
            
            # Apply visibility fade for back side (90-270 degrees)
            # This makes it realistic - we can't see the back of a 2D image
            visibility = 1.0
            if 90 < camera_angle < 270:
                # Fade out when showing the "back" that we don't have
                # Maximum fade at 180° (directly behind)
                angle_from_back = abs(180 - camera_angle)
                visibility = angle_from_back / 90.0  # 0.0 at 180°, 1.0 at 90°/270°
                visibility = max(0.1, min(1.0, visibility))  # Keep minimum 10% visibility
            
            # Apply visibility to alpha channel
            if visibility < 1.0:
                warped[:, :, 3] = (warped[:, :, 3] * visibility).astype(np.uint8)
            
            # Create canvas with background color
            canvas = np.zeros((video_size[1], video_size[0], 4), dtype=np.uint8)
            canvas[:, :, 0:3] = bg_color[::-1]  # BGR format
            canvas[:, :, 3] = 255  # Full opacity for background
            
            # If warped image is larger than canvas, scale it down to fit
            if new_width > video_size[0] or new_height > video_size[1]:
                scale = min(video_size[0] / new_width, video_size[1] / new_height) * 0.95  # 95% to add margin
                new_scaled_width = int(new_width * scale)
                new_scaled_height = int(new_height * scale)
                warped = cv2.resize(warped, (new_scaled_width, new_scaled_height), interpolation=cv2.INTER_LINEAR)
                new_width = new_scaled_width
                new_height = new_scaled_height
            
            # Calculate position to center the warped image
            y_offset = (video_size[1] - new_height) // 2
            x_offset = (video_size[0] - new_width) // 2
            
            # Ensure offsets are valid (should always be true now after scaling)
            y_offset = max(0, y_offset)
            x_offset = max(0, x_offset)
            
            # Calculate boundaries for pasting
            y_end = min(y_offset + new_height, video_size[1])
            x_end = min(x_offset + new_width, video_size[0])
            
            warped_h = y_end - y_offset
            warped_w = x_end - x_offset
            
            # Composite warped image onto canvas with alpha blending
            alpha = warped[:warped_h, :warped_w, 3:4] / 255.0
            canvas[y_offset:y_end, x_offset:x_end, 0:3] = (
                canvas[y_offset:y_end, x_offset:x_end, 0:3] * (1 - alpha) +
                warped[:warped_h, :warped_w, 0:3] * alpha
            ).astype(np.uint8)
            
            # Convert BGRA to RGB for MoviePy
            frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGRA2RGB)
            frames.append(frame_rgb)
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{frames_per_rotation} frames...")
        
        print(f"All frames generated. Creating video...")
        
        # Create video from frames using MoviePy
        from moviepy.editor import ImageSequenceClip
        
        video_clip = ImageSequenceClip(frames, fps=fps)
        video_clip = video_clip.set_duration(duration)
        
        # Write video file
        print("Rendering final video...")
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio=False,
            fps=fps,
            preset='medium',
            threads=4
        )
        
        # Clean up
        video_clip.close()
        
        print("3D spin video generation complete!")
        return output_path
    
    except Exception as e:
        print(f"Error generating 3D spin video: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise


def generate_video(intro_path, product_images, background_path, output_path, outro_path=None, remove_bg=True, transition_type='carousel', video_format='tiktok', background_is_video=False):
    """
    Generate the final video with optional intro/outro and product images using selected transition effect.
    
    Args:
        intro_path: Path to intro video (can be None for no intro)
        product_images: List of paths to product images
        background_path: Path to custom background image or video (can be None)
        output_path: Path to save the output video
        outro_path: Path to outro video (can be None for no outro)
        remove_bg: Whether to remove background from images (default: True)
        transition_type: Type of transition ('carousel', 'card', or 'filmstrip')
        video_format: Video format ('tiktok' for 1080x1920, 'youtube' for 1920x1080)
        background_is_video: Whether the background is a video file (default: False)
    
    Returns:
        str: Path to the generated video
    """
    clips = []
    processed_images = []
    
    try:
        # Determine video size based on format preference
        # TikTok/MercadoLibre format: 1080x1920 (9:16 vertical)
        # YouTube format: 1920x1080 (16:9 horizontal)
        if video_format == 'youtube':
            default_video_size = (1920, 1080)
        else:
            # Default to TikTok format for any other value (including 'tiktok')
            default_video_size = (1080, 1920)
        
        video_size = default_video_size
        
        # Load intro video if provided
        if intro_path:
            print("Loading intro video...")
            intro_clip = VideoFileClip(intro_path)
            
            # Resize intro to match target format if needed
            if (intro_clip.w, intro_clip.h) != video_size:
                print(f"Resizing intro from {intro_clip.w}x{intro_clip.h} to {video_size[0]}x{video_size[1]}...")
                intro_clip = intro_clip.resize(video_size)
            
            clips.append(intro_clip)
        else:
            print("No intro video provided, using product carousel only...")
        
        # Process each product image
        print(f"Processing {len(product_images)} product images...")
        
        # If background is video, we need to use different processing
        if background_is_video and background_path:
            print("Using video background for products...")
            for i, product_image in enumerate(product_images):
                print(f"Processing image {i+1}/{len(product_images)} with video background...")
                
                # For video backgrounds, we need to remove background and keep as PNG with transparency
                processed_image_path = os.path.join(
                    UPLOAD_FOLDER, 
                    f"processed_{uuid.uuid4().hex}.png"
                )
                processed_images.append(processed_image_path)
                
                # Remove background only (keep transparency for compositing)
                if remove_bg:
                    remove_background_only(
                        product_image, 
                        processed_image_path,
                        video_size
                    )
                else:
                    # Just copy the product image resized
                    img = Image.open(product_image).convert("RGBA")
                    product_width, product_height = img.size
                    bg_width, bg_height = video_size
                    scale_factor = min((bg_width * 0.8) / product_width, (bg_height * 0.8) / product_height)
                    new_width = int(product_width * scale_factor)
                    new_height = int(product_height * scale_factor)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    # Create transparent canvas and center product
                    canvas = Image.new('RGBA', video_size, (0, 0, 0, 0))
                    x = (bg_width - new_width) // 2
                    y = (bg_height - new_height) // 2
                    canvas.paste(img, (x, y), img if img.mode == 'RGBA' else None)
                    canvas.save(processed_image_path, 'PNG')
                
                # Create clip with video background and selected transition effect
                if transition_type == 'card':
                    transition_clip = create_card_clip_with_video_bg(processed_image_path, background_path, duration=3, video_size=video_size)
                elif transition_type == 'filmstrip':
                    transition_clip = create_filmstrip_clip_with_video_bg(processed_image_path, background_path, duration=3, video_size=video_size)
                else:  # default to carousel
                    transition_clip = create_carousel_clip_with_video_bg(processed_image_path, background_path, duration=3, video_size=video_size)
                
                clips.append(transition_clip)
        else:
            # Standard processing with image background (or no background)
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
                        background_path, 
                        processed_image_path,
                        video_size
                    )
                else:
                    # Just resize and optionally composite on background without removing bg
                    composite_without_removal(
                        product_image,
                        background_path,
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
        
        # Load outro video if provided
        if outro_path:
            print("Loading outro video...")
            outro_clip = VideoFileClip(outro_path)
            
            # Resize outro to match video format if needed
            if (outro_clip.w, outro_clip.h) != video_size:
                print(f"Resizing outro from {outro_clip.w}x{outro_clip.h} to {video_size[0]}x{video_size[1]}...")
                outro_clip = outro_clip.resize(video_size)
            
            clips.append(outro_clip)
        
        # Ensure we have at least one clip to concatenate
        if not clips:
            raise ValueError("No clips to concatenate. At least one product image must be processed successfully.")
        
        # Concatenate all clips
        print("Concatenating clips...")
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Write final video
        print("Rendering final video...")
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,  # Increased to 30fps for smoother playback (TikTok standard)
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
    """Handle video generation request with optional intro/outro."""
    uploaded_files = []
    
    try:
        # Check if product images are present (required)
        if 'product_images' not in request.files:
            flash('No se encontraron imágenes de productos', 'error')
            return redirect(url_for('index'))
        
        # Get files - intro and outro are now optional
        intro_video = request.files.get('intro_video')
        outro_video = request.files.get('outro_video')
        product_images = request.files.getlist('product_images')
        custom_background = request.files.get('custom_background')
        
        # Get form parameters
        remove_bg = request.form.get('remove_background') == 'yes'
        transition_type = request.form.get('transition_type', 'carousel')
        video_format = request.form.get('video_format', 'tiktok')
        
        # Validate product images (required)
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
        
        # Save intro video if provided (optional)
        intro_path = None
        if intro_video and intro_video.filename != '':
            if not allowed_file(intro_video.filename, 'video'):
                flash('Formato de video de intro no válido. Use MP4, MOV o AVI', 'error')
                return redirect(url_for('index'))
            
            print("Guardando video de introducción...")
            intro_filename = f"{uuid.uuid4().hex}_{secure_filename(intro_video.filename)}"
            intro_path = os.path.join(app.config['UPLOAD_FOLDER'], intro_filename)
            intro_video.save(intro_path)
            uploaded_files.append(intro_path)
        
        # Save outro video if provided (optional)
        outro_path = None
        if outro_video and outro_video.filename != '':
            if not allowed_file(outro_video.filename, 'video'):
                flash('Formato de video de outro no válido. Use MP4, MOV o AVI', 'error')
                return redirect(url_for('index'))
            
            print("Guardando video de cierre...")
            outro_filename = f"{uuid.uuid4().hex}_{secure_filename(outro_video.filename)}"
            outro_path = os.path.join(app.config['UPLOAD_FOLDER'], outro_filename)
            outro_video.save(outro_path)
            uploaded_files.append(outro_path)
        
        # Save product images
        print("Guardando imágenes de productos...")
        product_image_paths = []
        for img in product_images:
            img_filename = f"{uuid.uuid4().hex}_{secure_filename(img.filename)}"
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
            img.save(img_path)
            uploaded_files.append(img_path)
            product_image_paths.append(img_path)
        
        # Save custom background if provided (can be image or video)
        background_path = None
        background_is_video = False
        if custom_background and custom_background.filename != '':
            # Check if background is a video or image
            if is_video_file(custom_background.filename):
                if allowed_file(custom_background.filename, 'video'):
                    print("Guardando video de fondo personalizado...")
                    bg_filename = f"{uuid.uuid4().hex}_{secure_filename(custom_background.filename)}"
                    background_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)
                    custom_background.save(background_path)
                    uploaded_files.append(background_path)
                    background_is_video = True
                else:
                    flash('Formato de video de fondo no válido. Use MP4, MOV o AVI', 'warning')
            elif allowed_file(custom_background.filename, 'image'):
                print("Guardando imagen de fondo personalizado...")
                bg_filename = f"{uuid.uuid4().hex}_{secure_filename(custom_background.filename)}"
                background_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)
                custom_background.save(background_path)
                uploaded_files.append(background_path)
            else:
                flash('Formato de fondo no válido. Use PNG, JPG, JPEG, MP4, MOV o AVI', 'warning')
        
        # Generate output filename
        output_filename = f"video_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['VIDEOS_FOLDER'], output_filename)
        
        # Generate video with optional intro/outro
        print("Iniciando generación de video...")
        flash('Procesando video... Esto puede tomar varios minutos.', 'info')
        generate_video(intro_path, product_image_paths, background_path, output_path, 
                      outro_path=outro_path, remove_bg=remove_bg, transition_type=transition_type, 
                      video_format=video_format, background_is_video=background_is_video)
        
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


@app.route('/generate_3d_spin', methods=['POST'])
def generate_3d_spin_route():
    """Handle 3D spin video generation request with multi-image support."""
    uploaded_files = []
    processed_files = []
    
    try:
        # Check if front image is present (required)
        if 'spin_front_image' not in request.files:
            flash('No se encontró la imagen frontal del producto', 'error')
            return redirect(url_for('index'))
        
        front_image = request.files['spin_front_image']
        back_image = request.files.get('spin_back_image')
        left_image = request.files.get('spin_left_image')
        right_image = request.files.get('spin_right_image')
        custom_background = request.files.get('spin_background')
        
        # Get parameters
        frames_per_rotation = int(request.form.get('frames_per_rotation', 60))
        perspective_strength = float(request.form.get('perspective_strength', 0.3))
        
        # Validate front image
        if front_image.filename == '':
            flash('No se seleccionó la imagen frontal del producto', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(front_image.filename, 'image'):
            flash('Formato de imagen frontal no válido. Use PNG, JPG o JPEG', 'error')
            return redirect(url_for('index'))
        
        # Validate parameters
        if not (30 <= frames_per_rotation <= 120):
            flash('El número de frames debe estar entre 30 y 120', 'error')
            return redirect(url_for('index'))
        
        if not (0.0 <= perspective_strength <= 1.0):
            flash('La fuerza de perspectiva debe estar entre 0.0 y 1.0', 'error')
            return redirect(url_for('index'))
        
        # Determine background color
        bg_color = (255, 255, 255)  # Default white
        if custom_background and custom_background.filename != '':
            if allowed_file(custom_background.filename, 'image'):
                print("Guardando imagen de fondo personalizado...")
                bg_filename = f"{uuid.uuid4().hex}_{secure_filename(custom_background.filename)}"
                background_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)
                custom_background.save(background_path)
                uploaded_files.append(background_path)
                
                # Get average color from custom background
                bg_img = Image.open(background_path)
                bg_img_resized = bg_img.resize((100, 100))
                bg_array = np.array(bg_img_resized)
                bg_color = tuple(bg_array.mean(axis=(0, 1)).astype(int).tolist()[:3])
                bg_img.close()
            else:
                flash('Formato de imagen de fondo no válido', 'warning')
        
        # Save and process images
        image_paths = {}
        
        # Process front image (required)
        print("Procesando imagen frontal...")
        front_filename = f"{uuid.uuid4().hex}_{secure_filename(front_image.filename)}"
        front_path = os.path.join(app.config['UPLOAD_FOLDER'], front_filename)
        front_image.save(front_path)
        uploaded_files.append(front_path)
        
        # Remove background from front (vertical format for TikTok)
        front_processed = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_front_{uuid.uuid4().hex}.png")
        remove_background_only(front_path, front_processed, target_size=(1080, 1920))
        processed_files.append(front_processed)
        image_paths['front'] = front_processed
        
        # Process back image (optional)
        if back_image and back_image.filename != '' and allowed_file(back_image.filename, 'image'):
            print("Procesando imagen trasera...")
            back_filename = f"{uuid.uuid4().hex}_{secure_filename(back_image.filename)}"
            back_path = os.path.join(app.config['UPLOAD_FOLDER'], back_filename)
            back_image.save(back_path)
            uploaded_files.append(back_path)
            
            back_processed = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_back_{uuid.uuid4().hex}.png")
            remove_background_only(back_path, back_processed, target_size=(1080, 1920))
            processed_files.append(back_processed)
            image_paths['back'] = back_processed
        
        # Process left image (optional)
        if left_image and left_image.filename != '' and allowed_file(left_image.filename, 'image'):
            print("Procesando imagen lado izquierdo...")
            left_filename = f"{uuid.uuid4().hex}_{secure_filename(left_image.filename)}"
            left_path = os.path.join(app.config['UPLOAD_FOLDER'], left_filename)
            left_image.save(left_path)
            uploaded_files.append(left_path)
            
            left_processed = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_left_{uuid.uuid4().hex}.png")
            remove_background_only(left_path, left_processed, target_size=(1080, 1920))
            processed_files.append(left_processed)
            image_paths['left'] = left_processed
        
        # Process right image (optional)
        if right_image and right_image.filename != '' and allowed_file(right_image.filename, 'image'):
            print("Procesando imagen lado derecho...")
            right_filename = f"{uuid.uuid4().hex}_{secure_filename(right_image.filename)}"
            right_path = os.path.join(app.config['UPLOAD_FOLDER'], right_filename)
            right_image.save(right_path)
            uploaded_files.append(right_path)
            
            right_processed = os.path.join(app.config['UPLOAD_FOLDER'], f"processed_right_{uuid.uuid4().hex}.png")
            remove_background_only(right_path, right_processed, target_size=(1080, 1920))
            processed_files.append(right_processed)
            image_paths['right'] = right_processed
        
        print(f"Total de imágenes procesadas: {len(image_paths)}")
        print(f"Vistas disponibles: {list(image_paths.keys())}")
        
        # Generate output filename
        output_filename = f"3d_spin_multi_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(app.config['VIDEOS_FOLDER'], output_filename)
        
        # Generate multi-image 3D spin video
        print("Iniciando generación de video 3D con múltiples imágenes...")
        flash('Procesando video 3D con múltiples perspectivas... Esto puede tomar algunos minutos.', 'info')
        generate_multi_image_3d_spin_video(
            image_paths,
            output_path,
            frames_per_rotation=frames_per_rotation,
            perspective_strength=perspective_strength,
            bg_color=bg_color
        )
        
        # Clean up uploaded and processed files
        print("Limpiando archivos temporales...")
        for file_path in uploaded_files + processed_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete file {file_path}: {e}")
        
        flash('¡Video 3D generado exitosamente!', 'success')
        return render_template('index.html', video_filename=output_filename)
    
    except Exception as e:
        print(f"Error en generate_3d_spin_route: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        flash(f'Error al generar el video 3D: {str(e)}', 'error')
        
        # Clean up on error
        for file_path in uploaded_files + processed_files:
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
