# PhotoCollage

An automated photobooth system that watches for new images, creates collages, and prints them automatically.

## Overview

This system provides a complete photobooth solution that:
- Monitors a directory for new image files
- Creates 3-photo collages using a custom template
- Manages a print queue for automatic printing
- Handles file processing with robust error handling

## Features

- **Automatic File Detection**: Watches for new images in real-time using filesystem events
- **Template-Based Collages**: Creates professional-looking collages using a PNG template with transparent areas
- **Print Queue Management**: Queues print jobs and processes them sequentially to prevent printer overload
- **User Interaction**: Prompts for number of copies for each collage
- **Error Handling**: Robust file access checking with retry logic for permission issues
- **Scalable Printing**: Automatically scales images to fit within printer boundaries

## System Requirements

- Python 3.7+
- Windows OS (uses win32 libraries for printing)
- PIL/Pillow for image processing
- watchdog for file system monitoring
- pywin32 for Windows printing integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PotatoPirate8/PhotoCollage.git
cd PhotoCollage
```

2. Install required dependencies:
```bash
pip install Pillow watchdog pywin32
```

3. Set up your directory structure:
```
media/
├── processed_full/          # Input directory - place source images here
├── merged_images/           # Output directory - collages saved here
└── template/
    └── template1.png        # Template file with transparent areas for photos
```

## Usage

### Starting the System

Run the main photobooth processor:
```bash
python photobooth_processor.py
```

The system will:
1. Start monitoring the `processed_full` directory
2. Initialize the print queue system
3. Wait for new images to be added

### Adding Images

1. Copy 3 images to the `processed_full` directory
2. The system automatically detects new files
3. Once 3 files are detected, it creates a collage
4. You'll be prompted to specify the number of copies to print
5. The collage is automatically sent to the default printer

### Template Configuration

The system uses `template1.png` with transparent areas where photos will be placed. The current configuration supports:
- 3 photo positions in a vertical layout
- Automatic photo scaling and positioning
- High-quality image resizing

## File Structure

```
PhotoCollage/
├── photobooth_processor.py  # Main application - file monitoring and print queue
├── photo_collage.py         # Collage creation logic
├── README.md               # This file
├── processed_full/         # Input directory for source images
├── merged_images/          # Output directory for finished collages
└── template/
    └── template1.png       # Template file
```

## Configuration

Key configuration options in `photobooth_processor.py`:

```python
# Directory paths
input_dir = r"C:\path\to\processed_full"
output_dir = r"C:\path\to\merged_images"

# Print settings
scale_factor = 0.95  # 95% of physical page size
copies = 1           # Default number of copies
```

Key configuration options in `photo_collage.py`:

```python
# Template and photo positions
template_path = r"C:\path\to\template\template1.png"
photo_positions = [
    (98, 333, 885, 639),   # Top photo position (x, y, width, height)
    (98, 1062, 885, 639),  # Middle photo position
    (98, 1790, 885, 639),  # Bottom photo position
]
```

## How It Works

### File Processing Flow

1. **File Detection**: Watchdog monitors the input directory for new files
2. **File Validation**: System checks file accessibility and size before processing
3. **Batch Processing**: Waits for 3 files before creating a collage
4. **Collage Creation**: Uses PIL to composite images onto the template
5. **Print Queue**: Adds finished collages to a sequential print queue
6. **Printing**: Automatically prints using Windows printing APIs

### Print Queue System

- **Sequential Processing**: Only one print job at a time
- **Queue Management**: Multiple collages can be queued while printing
- **User Control**: Prompts for copy count for each collage
- **Error Handling**: Continues processing even if individual print jobs fail

### Template System

The template system uses PNG files with transparent areas:
- Transparent pixels indicate where photos should be placed
- Photos are automatically scaled and positioned
- High-quality resampling ensures sharp output

## Troubleshooting

### Common Issues

**"Permission denied" errors:**
- Files may still be copying when detected
- System automatically retries with exponential backoff
- Increase retry attempts in configuration if needed

**Print queue not working:**
- Check that default printer is set up correctly
- Verify printer drivers are installed
- Check Windows print spooler service is running

**Images not fitting properly:**
- Verify template transparent areas match photo_positions configuration
- Use the `find_transparent_areas()` function to detect correct positions
- Adjust photo_positions array as needed

**Memory issues with large images:**
- Images are automatically resized during processing
- Consider reducing source image sizes if problems persist

## Development

### Adding New Features

The system is modular and can be extended:

- **New Templates**: Add additional template files and update photo_positions
- **Different Layouts**: Modify photo_positions for different arrangements
- **Enhanced Printing**: Add print settings, paper size detection, etc.
- **Web Interface**: Add a web frontend for remote control
- **Database Logging**: Track printed collages and usage statistics

### Testing

Test the system by:
1. Adding test images to the input directory
2. Verifying collage creation in output directory
3. Testing print functionality with non-critical printer
4. Monitoring logs for error handling

## License

This project is available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section above
- Review log output for specific error messages
- Ensure all dependencies are properly installed
- Verify directory permissions and printer setup
