from PIL import Image
import os
from datetime import datetime
import glob
import time

class CollageCreator:
    def __init__(self, input_files=None):
        self.template_path = r"C:\Users\junha\OneDrive - University of Southampton\media\media\template\template1.png"
        self.input_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\processed_full"
        self.output_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\merged_images"
        self.input_files = input_files
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Template photo positions (x, y, width, height) - Updated to match detected transparent areas
        self.photo_positions = [
            (98, 333, 885, 639),    # Top photo - exact match to detected transparent area
            (98, 1062, 885, 639),   # Middle photo - exact match to detected transparent area  
            (98, 1790, 885, 639),   # Bottom photo - exact match to detected transparent area
        ]

    def find_transparent_areas(self):
        """Helper function to find transparent areas in the template"""
        template = Image.open(self.template_path)
        if template.mode != 'RGBA':
            print("Template is not in RGBA mode, converting...")
            template = template.convert('RGBA')
        
        width, height = template.size
        print(f"Template size: {width}x{height}")
        
        # Get pixel data
        pixels = template.load()
        
        # Find transparent regions
        transparent_regions = []
        visited = set()
        
        for y in range(height):
            for x in range(width):
                if (x, y) not in visited:
                    r, g, b, a = pixels[x, y]
                    # Check if pixel is transparent or nearly transparent
                    if a < 50:  # Very transparent
                        # Found a transparent pixel, now find the bounding box
                        min_x, max_x = x, x
                        min_y, max_y = y, y
                        
                        # Flood fill to find the extent of this transparent region
                        stack = [(x, y)]
                        region_pixels = set()
                        
                        while stack:
                            cx, cy = stack.pop()
                            if (cx, cy) in visited or cx < 0 or cx >= width or cy < 0 or cy >= height:
                                continue
                            
                            cr, cg, cb, ca = pixels[cx, cy]
                            if ca >= 50:  # Not transparent enough
                                continue
                            
                            visited.add((cx, cy))
                            region_pixels.add((cx, cy))
                            
                            # Update bounding box
                            min_x = min(min_x, cx)
                            max_x = max(max_x, cx)
                            min_y = min(min_y, cy)
                            max_y = max(max_y, cy)
                            
                            # Add neighboring pixels to check
                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                stack.append((cx + dx, cy + dy))
                        
                        # Only consider regions that are reasonably large (likely photo areas)
                        region_width = max_x - min_x + 1
                        region_height = max_y - min_y + 1
                        
                        if region_width > 100 and region_height > 100:  # Filter out small transparent areas
                            transparent_regions.append({
                                'x': min_x,
                                'y': min_y,
                                'width': region_width,
                                'height': region_height,
                                'area': len(region_pixels)
                            })
        
        # Sort regions by position (top to bottom)
        transparent_regions.sort(key=lambda r: r['y'])
        
        print(f"\nFound {len(transparent_regions)} transparent regions:")
        for i, region in enumerate(transparent_regions):
            print(f"  Region {i+1}: x={region['x']}, y={region['y']}, width={region['width']}, height={region['height']}, area={region['area']} pixels")
        
        print("\nCurrent photo positions:")
        for i, pos in enumerate(self.photo_positions):
            print(f"  Photo {i+1}: x={pos[0]}, y={pos[1]}, width={pos[2]}, height={pos[3]}")
        
        if transparent_regions:
            print("\nSuggested photo positions based on detected transparent areas:")
            for i, region in enumerate(transparent_regions[:3]):  # Only show first 3
                print(f"  Photo {i+1}: ({region['x']}, {region['y']}, {region['width']}, {region['height']})")
        
        return transparent_regions

    def get_latest_photos(self, n=3):
        """Get the photos to use in the collage, excluding temporary files"""
        max_attempts = 3  # Maximum number of retry attempts
        attempt = 0
        
        while attempt < max_attempts:
            try:
                if self.input_files:
                    # Filter out temporary files from the input list
                    valid_files = [f for f in self.input_files if not f.endswith(".tmp")]
                    if len(valid_files) >= n:
                        return valid_files[:n]
                    else:
                        print(f"Not enough valid files in input_files (attempt {attempt + 1}/{max_attempts}). Retrying...")
                        time.sleep(1)  # Wait before retrying
                        attempt += 1
                        continue
                
                # Filter out temporary files from the glob list
                files = glob.glob(os.path.join(self.input_dir, "*.jpg"))
                files = [f for f in files if not f.endswith(".tmp")]
                files.sort(key=os.path.getmtime, reverse=True)
                
                if len(files) >= n:
                    return files[:n]
                else:
                    print(f"Not enough valid JPG files found (attempt {attempt + 1}/{max_attempts}). Retrying...")
                    time.sleep(1)  # Wait before retrying
                    attempt += 1
                    continue
            
            except Exception as e:
                print(f"Error in get_latest_photos (attempt {attempt + 1}/{max_attempts}): {str(e)}")
                time.sleep(1)
                attempt += 1
        
        raise Exception(f"Could not retrieve enough valid photos after {max_attempts} attempts.")

    def create_collage(self, photos):
        """Create a collage using the template and provided photos"""
        template = Image.open(self.template_path)
        
        for photo_path, position in zip(photos, self.photo_positions):
            try:
                # Load the photo
                photo = Image.open(photo_path)
                
                # Get target width and height from position
                target_width = position[2]
                target_height = position[3]
                
                # Calculate scaling factor to fill the entire area exactly
                width_ratio = target_width / photo.width
                height_ratio = target_height / photo.height
                
                # Use the larger ratio to ensure the photo fills the entire area
                scale_factor = max(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = int(photo.width * scale_factor)
                new_height = int(photo.height * scale_factor)
                
                # Resize the photo
                photo = photo.resize((new_width, new_height), Image.LANCZOS)
                
                # Calculate crop offsets to center the image
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                
                # Crop to exact target size to match transparent area exactly
                photo = photo.crop((left, top, right, bottom))
                
                # Ensure the cropped photo is exactly the target size
                if photo.size != (target_width, target_height):
                    photo = photo.resize((target_width, target_height), Image.LANCZOS)
                
                # Paste the photo directly onto the template at exact position
                template.paste(photo, (position[0], position[1]))
                
            except Exception as e:
                print(f"Error processing photo {photo_path}: {str(e)}")
                # Create a blank placeholder if there's an error with exact dimensions
                placeholder = Image.new('RGB', (position[2], position[3]), (200, 200, 200))
                template.paste(placeholder, (position[0], position[1]))
        
        return template

    def create_side_by_side_collage(self):
        """Create the final side-by-side collage and move used photos to prevent reuse"""
        recent_photos = self.get_latest_photos(3)
        if len(recent_photos) < 3:
            raise Exception("Not enough photos found")

        # Create a directory for archived/used images if it doesn't exist
        used_images_dir = os.path.join(self.output_dir, "single_images")
        os.makedirs(used_images_dir, exist_ok=True)

        # Create the collage with the recent photos
        collage = self.create_collage(recent_photos)
        
        # Create the side-by-side image
        total_width = collage.width * 2
        final_image = Image.new('RGB', (total_width, collage.height))
        
        # Paste the collage twice side by side
        final_image.paste(collage, (0, 0))
        final_image.paste(collage, (collage.width, 0))
        
        # Save the collage and get the path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"collage_{timestamp}.jpg")
        final_image.save(output_path)
        
        # Move the used images to the used_images directory to prevent reuse
        for photo_path in recent_photos:
            try:
                # Get just the filename from the path
                filename = os.path.basename(photo_path)
                
                # Create a destination path with timestamp to prevent overwriting
                dest_path = os.path.join(used_images_dir, f"{timestamp}_{filename}")
                
                # Move the file
                os.rename(photo_path, dest_path)
                print(f"Moved {filename} to {dest_path}")
            except Exception as e:
                print(f"Error moving file {photo_path}: {str(e)}")
        
        return output_path

if __name__ == "__main__":
    creator = CollageCreator()
    
    # Add option to check template positioning
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check-template":
        print("Checking template positioning...")
        creator.find_transparent_areas()
    else:
        try:
            output_path = creator.create_side_by_side_collage()
            print(f"Created collage: {output_path}")
        except Exception as e:
            print(f"Error creating collage: {str(e)}")
