from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import time
from datetime import datetime
import traceback
from photo_collage import CollageCreator
from PIL import Image, ImageWin
import win32print
import win32ui
import threading
import queue

class PhotoboothHandler(FileSystemEventHandler):
    def __init__(self, copies=1):
        self.input_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\processed_full"
        self.output_dir = r"C:\Users\junha\OneDrive - University of Southampton\media\media\merged_images"
        os.makedirs(self.output_dir, exist_ok=True)
        self.new_files = []
        self.copies = copies
        
        # Initialize print queue system
        self.print_queue = queue.Queue()
        self.print_thread = threading.Thread(target=self._print_worker, daemon=True)
        self.print_thread.start()
        self.is_printing = False
        
        print(f"[{self._get_timestamp()}] Photobooth processor started")
        print(f"[{self._get_timestamp()}] Watching directory: {self.input_dir}")
        print(f"[{self._get_timestamp()}] Output directory: {self.output_dir}")
        print(f"[{self._get_timestamp()}] Print queue system initialized")
        print(f"[{self._get_timestamp()}] Ready to process collages (will ask for copy count each time)")

    def _get_timestamp(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_copies_for_collage(self):
        """Ask user how many copies to print for this specific collage"""
        print(f"\n{'-'*50}")
        print(f"[{self._get_timestamp()}] COLLAGE READY!")
        print(f"{'-'*50}")
        
        while True:
            try:
                copies_input = input(f"How many copies for this collage? (default: {self.copies}, Enter for default): ").strip()
                
                if copies_input == "":
                    return self.copies  # Use default if user just presses Enter
                
                copies = int(copies_input)
                if copies < 0:
                    print("Enter 0 to skip printing, or a positive number for copies.")
                    continue
                return copies
                
            except ValueError:
                print("Error: Please enter a valid number. Try again.")
                continue
            except KeyboardInterrupt:
                print(f"\n[{self._get_timestamp()}] User interrupted - using default ({self.copies} copies)")
                return self.copies

    def _print_worker(self):
        """Background worker thread that processes print jobs sequentially"""
        while True:
            try:
                # Get next print job from queue (blocks until available)
                print_job = self.print_queue.get()
                
                if print_job is None:  # Shutdown signal
                    break
                    
                image_path, copies = print_job
                self.is_printing = True
                
                print(f"[{self._get_timestamp()}] Starting print job: {os.path.basename(image_path)} ({copies} copies)")
                
                # Send to printer
                for copy_num in range(copies):
                    try:
                        # Print the image using the existing print_image_direct method
                        self.print_image_direct(image_path)
                        print(f"[{self._get_timestamp()}] Sent copy {copy_num + 1}/{copies} to printer")
                        
                        # Small delay between copies to prevent overwhelming printer
                        if copy_num < copies - 1:
                            time.sleep(2)
                            
                    except Exception as e:
                        print(f"[{self._get_timestamp()}] Error printing copy {copy_num + 1}: {e}")
                
                self.is_printing = False
                print(f"[{self._get_timestamp()}] Print job completed: {os.path.basename(image_path)}")
                
                # Mark job as done
                self.print_queue.task_done()
                
                # Check if we can process more files after print job completes
                if self.print_queue.empty() and not self.is_printing and len(self.new_files) >= 3:
                    print(f"[{self._get_timestamp()}] Print queue empty, not printing, and files available - processing next batch...")
                    # Use a small delay and then trigger processing
                    threading.Timer(0.5, self._trigger_processing).start()
                
            except Exception as e:
                print(f"[{self._get_timestamp()}] Error in print worker: {e}")
                self.is_printing = False
                self.print_queue.task_done()

    def _trigger_processing(self):
        """Helper method to trigger processing from print worker thread"""
        if len(self.new_files) >= 3 and self.print_queue.empty() and not self.is_printing:
            print(f"[{self._get_timestamp()}] Triggering delayed processing of {len(self.new_files)} files")
            self.process_files()
        else:
            print(f"[{self._get_timestamp()}] Cannot trigger processing: files={len(self.new_files)}, queue_empty={self.print_queue.empty()}, is_printing={self.is_printing}")

    def add_to_print_queue(self, image_path, copies):
        """Add a print job to the queue"""
        self.print_queue.put((image_path, copies))
        queue_size = self.print_queue.qsize()
        if queue_size > 1:
            print(f"[{self._get_timestamp()}] Added to print queue (position {queue_size})")
        else:
            print(f"[{self._get_timestamp()}] Added to print queue (processing now)")

    def print_image(self, image_path, copies=1):
        """Add image to print queue instead of printing directly"""
        if copies > 0:
            self.add_to_print_queue(image_path, copies)
        else:
            print(f"[{self._get_timestamp()}] Skipping print (0 copies requested)")

    def print_image_direct(self, image_path):
        """Direct printing method (renamed from print_image)"""
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

            # Use 94% of physical dimensions to ensure no overage
            scale_factor = 0.95
            img_width, img_height = img.size
            scaled_width = int(physical_width * scale_factor)
            scaled_height = int(physical_height * scale_factor)
            
            # Actually resize the image to the scaled dimensions to prevent stretching
            img_resized = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
            
            # Center the scaled image within the physical page
            x_offset = -margin_left + (physical_width - scaled_width) // 2
            y_offset = -margin_top + (physical_height - scaled_height) // 2
            
            print(f"[{self._get_timestamp()}] Using {scale_factor*100:.0f}% scale factor")
            print(f"[{self._get_timestamp()}] Physical size: {physical_width}x{physical_height}")
            print(f"[{self._get_timestamp()}] Original image size: {img_width}x{img_height}")
            print(f"[{self._get_timestamp()}] Resized image size: {scaled_width}x{scaled_height}")
            print(f"[{self._get_timestamp()}] Offsets: x={x_offset}, y={y_offset}")
            print(f"[{self._get_timestamp()}] Margins: left={margin_left}, top={margin_top}")
            
            # Print the resized image
            dib = ImageWin.Dib(img_resized)
            dib.draw(hdc.GetHandleOutput(), (x_offset, y_offset, x_offset + scaled_width, y_offset + scaled_height))
            
            # End printing
            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()
            
            print(f"[{self._get_timestamp()}] Successfully sent resized image to printer (97% scale)")
            
        except Exception as e:
            print(f"[{self._get_timestamp()}] ERROR: Failed to print {os.path.basename(image_path)}")
            print(f"[{self._get_timestamp()}] Error details: {str(e)}")
            traceback.print_exc()

    def on_created(self, event):
        if not event.is_directory and event.src_path.startswith(self.input_dir):
            # Check if the file is a temporary file
            if event.src_path.endswith(".tmp"):
                print(f"[{self._get_timestamp()}] Ignoring temporary file: {os.path.basename(event.src_path)}")
                return

            # Add a delay to allow the file to be fully written
            time.sleep(1.0)  # Wait for 1 second to ensure file is released

            max_attempts = 5  # Increased attempts for better reliability
            for attempt in range(max_attempts):
                try:
                    # Check if file exists and is accessible
                    if not os.path.exists(event.src_path):
                        print(f"[{self._get_timestamp()}] File doesn't exist yet, waiting... (Attempt {attempt + 1}/{max_attempts})")
                        time.sleep(1.0)  # Longer wait for file to appear
                        continue
                    
                    # Check file size using os.path.getsize to avoid opening the file
                    file_size = os.path.getsize(event.src_path)
                    if file_size > 0:
                        # Additional check: try to access the file briefly
                        try:
                            with open(event.src_path, 'rb') as f:
                                f.read(1)  # Try to read just 1 byte
                            break  # File is accessible, break the loop
                        except PermissionError:
                            print(f"[{self._get_timestamp()}] File still being written, waiting... (Attempt {attempt + 1}/{max_attempts})")
                            time.sleep(1.0)  # Wait longer for file to be released
                            continue
                    else:
                        print(f"[{self._get_timestamp()}] File is empty, waiting... (Attempt {attempt + 1}/{max_attempts})")
                        time.sleep(1.0)  # Wait before retrying
                        
                except PermissionError as e:
                    print(f"[{self._get_timestamp()}] Permission denied: {str(e)}, retrying... (Attempt {attempt + 1}/{max_attempts})")
                    time.sleep(1.0)  # Wait longer for permission issues
                except Exception as e:
                    print(f"[{self._get_timestamp()}] Error checking file: {str(e)}, retrying... (Attempt {attempt + 1}/{max_attempts})")
                    time.sleep(1.0)  # Wait before retrying
            else:
                print(f"[{self._get_timestamp()}] Failed to access file after {max_attempts} attempts, ignoring: {os.path.basename(event.src_path)}")
                return

            print(f"[{self._get_timestamp()}] New file detected: {os.path.basename(event.src_path)}")
            self.new_files.append(event.src_path)
            print(f"[{self._get_timestamp()}] Files in queue: {len(self.new_files)}/3")
            if len(self.new_files) >= 3:
                # Check both if queue is empty AND if nothing is currently printing
                if self.print_queue.empty() and not self.is_printing:
                    print(f"[{self._get_timestamp()}] Print queue empty and not printing - processing batch of 3 files...")
                    self.process_files()
                else:
                    if not self.print_queue.empty():
                        print(f"[{self._get_timestamp()}] Print queue busy ({self.print_queue.qsize()} jobs) - batch will be processed when queue is empty")
                    elif self.is_printing:
                        print(f"[{self._get_timestamp()}] Currently printing - batch will be processed when print job completes")
                    else:
                        print(f"[{self._get_timestamp()}] Print system busy - batch will be processed later")

    def process_files(self):
        try:
            print(f"[{self._get_timestamp()}] Creating collage...")
            
            # Fix the import path
            creator = CollageCreator(self.new_files[:3])  # Take exactly 3 files
            output_path = creator.create_side_by_side_collage()
            
            print(f"[{self._get_timestamp()}] Successfully created collage: {os.path.basename(output_path)}")
            
            # Ask user for number of copies for this specific collage
            copies_for_this_collage = self.get_copies_for_collage()
            
            if copies_for_this_collage == 0:
                print(f"[{self._get_timestamp()}] Skipping printing (0 copies requested)")
            else:
                print(f"[{self._get_timestamp()}] Adding {copies_for_this_collage} cop{'y' if copies_for_this_collage == 1 else 'ies'} to print queue...")
                self.print_image(output_path, copies_for_this_collage)
            
        except Exception as e:
            print(f"[{self._get_timestamp()}] ERROR: Failed to process images")
            print(f"[{self._get_timestamp()}] Error details: {str(e)}")
            traceback.print_exc()

        # Only remove the files that were processed
        self.new_files = self.new_files[3:] if len(self.new_files) > 3 else []
        
        # Don't automatically process more files - let the print worker handle this
        # when the queue becomes empty
        print(f"[{self._get_timestamp()}] Batch processing complete, {len(self.new_files)} files remaining in queue")

if __name__ == "__main__":
    observer = None
    event_handler = None
    try:
        event_handler = PhotoboothHandler(copies=1)  # Default to 1, will be asked for each collage
        # Use the same path as defined in the handler
        path = event_handler.input_dir
        observer = Observer()
        observer.schedule(event_handler, path, recursive=False)
        observer.start()

        while True:
            time.sleep(1)
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    except KeyboardInterrupt:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Shutting down...")
    finally:
        if observer is not None and observer.is_alive():
            observer.stop()
            observer.join()
        
        # Shutdown print queue gracefully
        if event_handler is not None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Shutting down print queue...")
            event_handler.print_queue.put(None)  # Signal worker to stop
            event_handler.print_thread.join(timeout=5)  # Wait up to 5 seconds
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Print queue shutdown complete")