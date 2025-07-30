import os
import time
import glob
from datetime import datetime
import traceback
from photo_collage import CollageCreator
import win32print
import win32ui
from PIL import Image, ImageWin

# [Other import statements remain unchanged]

class PhotoMonitor:
    def __init__(self):
        self.input_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\processed_full"
        self.output_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\merged_images"
        os.makedirs(self.output_dir, exist_ok=True)
        self.retry_interval = 2  # seconds
        
        print(f"[{self._get_timestamp()}] Photo monitor started")
        print(f"[{self._get_timestamp()}] Watching directory: {self.input_dir}")
        print(f"[{self._get_timestamp()}] Output directory: {self.output_dir}")

    def _get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_latest_jpg_files(self, n=3):
        """Get the latest JPG files in the directory"""
        try:
            # Get all JPG files in the directory
            files = glob.glob(os.path.join(self.input_dir, "*.jpg"))
            
            # Filter out temporary files
            valid_files = [f for f in files if not f.endswith(".tmp")]
            
            # Sort by modification time (newest first)
            valid_files.sort(key=os.path.getmtime, reverse=True)
            
            # Return the newest n files
            return valid_files[:n]
        except Exception as e:
            print(f"[{self._get_timestamp()}] Error getting JPG files: {str(e)}")
            return []

    def process_files(self, files):
        try:
            print(f"[{self._get_timestamp()}] Creating collage from {len(files)} files...")
            
            # Create a collage using the files
            creator = CollageCreator(files)
            output_path = creator.create_side_by_side_collage()
            
            print(f"[{self._get_timestamp()}] Successfully created collage: {os.path.basename(output_path)}")
            
            # Send the collage to printer
            print(f"[{self._get_timestamp()}] Sending to printer...")
            self.print_image(output_path)
                
            return True
        except Exception as e:
            print(f"[{self._get_timestamp()}] ERROR: Failed to process images")
            print(f"[{self._get_timestamp()}] Error details: {str(e)}")
            traceback.print_exc()
            return False

    def print_image(self, image_path):
        try:
            # Get the default printer
            printer_name = win32print.GetDefaultPrinter()
            print(f"[{self._get_timestamp()}] Using printer: {printer_name}")
            
            # Open the image
            img = Image.open(image_path)
            
            # Create the DC for printing
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(printer_name)
            
            # Start printing
            hdc.StartDoc(image_path)
            hdc.StartPage()
            
            # Get physical dimensions and margins
            physical_width = hdc.GetDeviceCaps(110)   # PHYSICALWIDTH
            physical_height = hdc.GetDeviceCaps(111)  # PHYSICALHEIGHT
            margin_left = hdc.GetDeviceCaps(112)      # PHYSICALOFFSETX
            margin_top = hdc.GetDeviceCaps(113)       # PHYSICALOFFSETY
            
            # Calculate printable dimensions
            printable_width = physical_width + margin_left   # Add margin to extend beyond boundaries
            printable_height = physical_height + margin_top  # Add margin to extend beyond boundaries
            
            # Scale image to fit page while maintaining aspect ratio and going beyond margins
            img_width, img_height = img.size
            ratio = max(printable_width/img_width, printable_height/img_height)  # Use max to ensure full coverage
            scaled_width = int(img_width * ratio)
            scaled_height = int(img_height * ratio)
            
            # Calculate position to center the image horizontally but adjust vertically
            x_offset = -margin_left + (physical_width - scaled_width) // 2
            
            # Use a more balanced vertical adjustment (halfway between original and previous)
            vertical_adjustment = int(margin_top)  # Reduced from 1.5 to 0.75
            y_offset = vertical_adjustment + (physical_height - scaled_height) // 2
            
            print(f"[{self._get_timestamp()}] Printing with offsets: x={x_offset}, y={y_offset} (balanced vertical position)")
            
            # Print the image with adjusted position
            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (x_offset, y_offset, x_offset + scaled_width, y_offset + scaled_height))
            
            # End printing
            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()
            
            print(f"[{self._get_timestamp()}] Successfully sent image to printer with balanced vertical position")
            return True
            
        except Exception as e:
            print(f"[{self._get_timestamp()}] ERROR: Failed to print {os.path.basename(image_path)}")
            print(f"[{self._get_timestamp()}] Error details: {str(e)}")
            traceback.print_exc()
            return False

    def run(self):
        print(f"[{self._get_timestamp()}] Starting continuous monitoring...")
        
        while True:
            try:
                # Get latest 3 JPG files
                files = self.get_latest_jpg_files(3)
                
                # Check if we have 3 files
                if len(files) >= 3:
                    print(f"[{self._get_timestamp()}] Found {len(files)} new JPG files, processing...")
                    if self.process_files(files[:3]):
                        print(f"[{self._get_timestamp()}] Successfully processed batch")
                else:
                    print(f"[{self._get_timestamp()}] Not enough JPG files found ({len(files)}/3), waiting...")
                
                # Wait before checking again
                time.sleep(self.retry_interval)
                
            except Exception as e:
                print(f"[{self._get_timestamp()}] Error in monitoring loop: {str(e)}")
                traceback.print_exc()
                time.sleep(self.retry_interval)

if __name__ == "__main__":
    monitor = PhotoMonitor()
    monitor.run()
