# Testing Guide

## Quick Start for Manual Testing

This guide provides step-by-step instructions to manually test the video generator application.

## Prerequisites

1. Python 3.8 or higher installed
2. FFmpeg installed on your system
3. Sample files for testing:
   - An intro video (MP4, MOV, or AVI format, 5-10 seconds recommended)
   - 2-5 product images (PNG, JPG, or JPEG format)
   - Optional: A background image (1920x1080 recommended)

## Setup Instructions

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Flask server:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   Open your browser and navigate to `http://localhost:5000`

## Test Cases

### Test Case 1: Basic Video Generation (No Custom Background)
1. Upload an intro video
2. Upload 2-3 product images
3. Leave the custom background field empty
4. Click "Generar Video"
5. Wait for processing to complete
6. Download and verify the generated video

**Expected Result:**
- Video starts with the intro
- Product images appear with white background
- Carousel effect shows smooth horizontal transitions
- All backgrounds are properly removed from product images

### Test Case 2: Video Generation with Custom Background
1. Upload an intro video
2. Upload 2-3 product images
3. Upload a custom background image
4. Click "Generar Video"
5. Wait for processing to complete
6. Download and verify the generated video

**Expected Result:**
- Video starts with the intro
- Product images appear on the custom background
- Backgrounds are removed and replaced correctly
- Carousel transitions are smooth

### Test Case 3: Maximum Images
1. Upload an intro video
2. Upload exactly 5 product images
3. Optionally upload a custom background
4. Click "Generar Video"
5. Verify all 5 images appear in the carousel

**Expected Result:**
- All 5 images are processed
- Video duration is appropriate (intro + 15 seconds for 5 images at 3s each)
- No images are skipped

### Test Case 4: Error Handling
Test the following error scenarios:

1. **Missing intro video:** Submit without selecting an intro video
   - Expected: Error message displayed

2. **Missing product images:** Submit without selecting product images
   - Expected: Error message displayed

3. **Too many images:** Try to upload more than 5 product images
   - Expected: Error message or client-side validation

4. **Invalid file format:** Upload a text file as video or image
   - Expected: Error message about invalid format

## What to Verify

When reviewing the generated video:

1. **Video Quality:**
   - Video plays without corruption
   - Resolution matches the intro video
   - No visual artifacts

2. **Background Removal:**
   - Product backgrounds are cleanly removed
   - No residual background elements
   - Product edges are clean

3. **Carousel Effect:**
   - Smooth slide-in from right
   - Images stay centered for visibility
   - Smooth slide-out to left
   - Consistent timing (3 seconds per image)

4. **Transitions:**
   - No jarring cuts between clips
   - Audio from intro is preserved (if present)
   - Proper sequencing (intro → products)

5. **File Management:**
   - Temporary files are cleaned up after generation
   - Generated video is available for download
   - Downloads work correctly

## Performance Notes

- First run may take longer as rembg downloads its AI model (~175MB)
- Processing time depends on:
  - Number and resolution of images
  - Video length and quality
  - System specifications
- Typical processing time: 1-5 minutes for a standard video

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Ensure virtual environment is activated and dependencies are installed

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg using system package manager

### Issue: Very slow processing
**Solution:** Reduce image resolutions or use fewer images

### Issue: Out of memory errors
**Solution:** Close other applications or reduce video quality settings

## Sample Files Recommendations

For best testing results, use:
- **Intro video:** 5-10 seconds, 1920x1080, MP4 format
- **Product images:** High contrast subjects, clear backgrounds, PNG or JPG
- **Background image:** 1920x1080, solid color or simple pattern works best

## Notes

- Generated videos are saved in the `videos/` directory
- Temporary uploads are stored in `uploads/` and automatically cleaned
- Each video gets a unique filename with UUID
- The application runs in debug mode by default (development only)
