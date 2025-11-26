from PIL import Image, ImageDraw
import os
import glob
import re

def make_circular_logo(input_path, output_path, size=(150, 150)):
    """
    Convert a logo to circular format
    """
    # Open the image
    img = Image.open(input_path).convert("RGBA")
    
    # Resize to desired size
    img = img.resize(size, Image.Resampling.LANCZOS)
    
    # Create a circular mask
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    # Apply the mask to make it circular
    result = Image.new('RGBA', size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    
    # Save the result
    result.save(output_path)
    print(f"Circular logo saved to {output_path}")

def update_html_files():
    """
    Update all HTML files to use the circular logo with larger size
    """
    # Find all HTML files in the project
    html_files = glob.glob("*.html") + glob.glob("*/*.html")
    
    # CSS class for the circular logo (increased size)
    logo_class = 'class="h-20 w-20 rounded-full object-contain mx-auto mb-4"'
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Check if the file contains any logo reference
            if 'assets/logo' in content:
                # Handle all variations of logo references
                # Original logo references
                content = re.sub(
                    r'<img src="assets/logo\.png" alt="MyFigPoint Logo" class="mx-auto h-16 w-auto mb-4">',
                    f'<img src="assets/logo-circular.png" alt="MyFigPoint Logo" {logo_class}>',
                    content
                )
                content = re.sub(
                    r'<img src="assets/logo\.png" alt="MyFigPoint Logo" class="h-8 w-auto">',
                    f'<img src="assets/logo-circular.png" alt="MyFigPoint Logo" {logo_class}>',
                    content
                )
                content = re.sub(
                    r'<img src="assets/logo\.png" alt="MyFigPoint Logo" class="h-8 w-auto"',
                    f'<img src="assets/logo-circular.png" alt="MyFigPoint Logo" {logo_class}',
                    content
                )
                
                # Existing circular logo references (different sizes)
                content = re.sub(
                    r'<img src="assets/logo-circular\.png" alt="MyFigPoint Logo" class="h-12 w-12 rounded-full object-contain mx-auto mb-4">',
                    f'<img src="assets/logo-circular.png" alt="MyFigPoint Logo" {logo_class}>',
                    content
                )
                
                content = re.sub(
                    r'<img src="assets/logo-circular\.png" alt="MyFigPoint Logo" class="h-12 w-12 rounded-full object-contain"',
                    f'<img src="assets/logo-circular.png" alt="MyFigPoint Logo" {logo_class}>',
                    content
                )
                
                # Write the updated content back to the file
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Updated {file_path}")
        except Exception as e:
            print(f"Error updating {file_path}: {e}")

if __name__ == "__main__":
    # Process the logo
    input_logo = "assets/logo.png"
    output_logo = "assets/logo-circular.png"
    
    if os.path.exists(input_logo):
        # Always re-process to ensure the new size
        make_circular_logo(input_logo, output_logo, (150, 150))
        print("Logo processing complete!")
        
        # Update HTML files
        update_html_files()
        print("All HTML files updated to use larger circular logo!")
    else:
        print(f"Input logo not found at {input_logo}")