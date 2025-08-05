#!/usr/bin/env python3
"""
Create PWA icons from a source image URL
This script downloads an image and creates various sized icons for PWA installation.
"""

import requests
from PIL import Image
import os
import io

def download_and_create_icons():
    # Source image URL (blue 3D star icon)
    image_url = "https://images.unsplash.com/photo-1611162618071-b39a2ec055fb?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzh8MHwxfHNlYXJjaHwxfHxpY29ufGVufDB8fHxibHVlfDE3NTQzNzg1NDV8MA&ixlib=rb-4.1.0&q=85&w=1000"
    
    # Icon sizes needed for PWA
    icon_sizes = [48, 72, 96, 144, 192, 512]
    
    # Create icons directory
    icons_dir = "/app/frontend/public/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    print("📥 Downloading source image...")
    
    try:
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Open with PIL
        source_image = Image.open(io.BytesIO(response.content))
        
        # Convert to RGB if needed (in case of RGBA)
        if source_image.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', source_image.size, (255, 255, 255))
            background.paste(source_image, mask=source_image.split()[-1])  # Use alpha channel as mask
            source_image = background
        elif source_image.mode != 'RGB':
            source_image = source_image.convert('RGB')
        
        print(f"✅ Source image downloaded: {source_image.size}")
        
        # Create icons in different sizes
        for size in icon_sizes:
            print(f"🖼️  Creating {size}x{size} icon...")
            
            # Create a square version of the image
            # First, find the smallest dimension and crop to square
            width, height = source_image.size
            min_size = min(width, height)
            
            # Calculate crop box to center the image
            left = (width - min_size) // 2
            top = (height - min_size) // 2
            right = left + min_size
            bottom = top + min_size
            
            # Crop to square
            square_image = source_image.crop((left, top, right, bottom))
            
            # Resize to target size with high quality
            resized_image = square_image.resize((size, size), Image.LANCZOS)
            
            # Save as PNG with transparency support
            icon_path = f"{icons_dir}/icon-{size}x{size}.png"
            resized_image.save(icon_path, "PNG", optimize=True)
            
            print(f"✅ Created: {icon_path}")
        
        print("\n🎉 All PWA icons created successfully!")
        print(f"📁 Icons location: {icons_dir}")
        
        # List created files
        icon_files = os.listdir(icons_dir)
        icon_files.sort()
        print("\n📋 Created icons:")
        for file in icon_files:
            file_path = os.path.join(icons_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"   • {file} ({file_size:,} bytes)")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download image: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        return False

if __name__ == "__main__":
    success = download_and_create_icons()
    if success:
        print("\n🚀 PWA icons ready for installation!")
    else:
        print("\n💥 Failed to create PWA icons")