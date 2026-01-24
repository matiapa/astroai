#!/usr/bin/env python3
"""
Simple script to run the annotator by capturing from webcam and saving results.

The camera device is configured via the WEBCAM_INDEX environment variable or --camera-index argument.

Usage:
    python run_tool.py [--simbad-radius 30.0] [--camera-index 0]
    python run_tool.py --list-cameras
    python run_tool.py --capture --camera-index 1 --output captured.png
    
    # Set camera via environment variable:
    WEBCAM_INDEX=1 python run_tool.py --simbad-radius 30.0
"""

import os
import json
import argparse
import cv2
from PIL import Image
from tools.analyze_image.analyze_image_tool import analyze_image


def list_available_cameras(max_check: int = 10) -> list:
    """
    Scan for available camera devices on the system.
    
    Args:
        max_check: Maximum number of device indices to check
    
    Returns:
        List of dictionaries with camera info (index, width, height, backend)
    """
    cameras = []
    
    for i in range(max_check):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Try to get backend name
            backend = cap.getBackendName() if hasattr(cap, 'getBackendName') else 'unknown'
            
            cameras.append({
                'index': i,
                'width': width,
                'height': height,
                'backend': backend
            })
            cap.release()
    
    return cameras


def capture_single_image(camera_index: int, warmup_frames: int = 5) -> Image.Image:
    """
    Capture a single image from the specified camera.
    
    Args:
        camera_index: The camera device index to use
        warmup_frames: Number of frames to skip for camera warmup
    
    Returns:
        PIL Image if successful, None otherwise
    """
    print(f"Opening camera {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {camera_index}")
        return None
    
    try:
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera resolution: {width}x{height}")
        
        # Warmup: skip initial frames
        if warmup_frames > 0:
            print(f"Camera warmup: skipping {warmup_frames} frames...")
            for _ in range(warmup_frames):
                cap.read()
        
        # Capture the frame
        print("Capturing frame...")
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("Error: Failed to capture frame")
            return None
        
        # Convert BGR (OpenCV) to RGB (PIL)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        print(f"Captured image: {image.size[0]}x{image.size[1]} pixels")
        
        return image
    
    finally:
        cap.release()
        print("Camera released")


def main():
    parser = argparse.ArgumentParser(description="Run annotator by capturing from webcam")
    parser.add_argument("--simbad-radius", type=float, default=30.0, 
                        help="SIMBAD search radius in arcseconds (default: 30)")
    parser.add_argument("--max-detections", type=int, default=None,
                        help="Maximum number of objects to detect (for debugging)")
    parser.add_argument("--list-cameras", action="store_true", help="List available cameras and exit")
    parser.add_argument("--camera-index", "-c", type=int, default=None, 
                        help="Camera index to use (overrides WEBCAM_INDEX env var)")
    parser.add_argument("--capture", action="store_true", 
                        help="Capture a single image and save it (no analysis)")
    parser.add_argument("--output", "-o", type=str, default="captured.png",
                        help="Output filename for --capture mode (default: captured.png)")
    args = parser.parse_args()

    # Set camera index from argument if provided
    if args.camera_index is not None:
        os.environ["WEBCAM_INDEX"] = str(args.camera_index)
        print(f"Using camera index: {args.camera_index}")

    # List cameras mode
    if args.list_cameras:
        print("Scanning for available cameras...")
        cameras = list_available_cameras()
        if not cameras:
            print("No cameras found!")
            return 1
        print(f"\nFound {len(cameras)} camera(s):\n")
        for cam in cameras:
            print(f"  Index {cam['index']}: {cam['width']}x{cam['height']} ({cam['backend']})")
        print("\nTo use a specific camera:")
        print("  python run_tool.py --camera-index 1 --capture --output test.png")
        print("  python run_tool.py -c 1 --simbad-radius 30.0")
        return 0

    # Capture-only mode
    if args.capture:
        camera_index = args.camera_index if args.camera_index is not None else int(os.environ.get("WEBCAM_INDEX", "0"))
        print(f"=== Quick Capture Mode ===\n")
        
        image = capture_single_image(camera_index)
        if image is None:
            return 1
        
        # Save the image
        image.save(args.output)
        print(f"\n✅ Saved image to: {args.output}")
        return 0

    # Full analysis mode
    print("=== Astronomical Image Analyzer (Detection-First) ===\n")
    camera_index = args.camera_index if args.camera_index is not None else os.environ.get("WEBCAM_INDEX", "0")
    print(f"Camera index: {camera_index}")
    print(f"SIMBAD radius: {args.simbad_radius}\"")
    if args.max_detections:
        print(f"Max detections: {args.max_detections}")
    print()

    result = analyze_image(
        simbad_radius_arcsec=args.simbad_radius,
        max_detections=args.max_detections,
        verbose=True
    )

    if not result["success"]:
        print(f"\n❌ Error: {result['error']}")
        return 1

    # Print summary
    print(f"\n=== Analysis Summary ===")
    print(f"Center: {result['plate_solving']['center']['ra_hms']}, {result['plate_solving']['center']['dec_dms']}")
    if result['plate_solving'].get('field_of_view'):
        fov = result['plate_solving']['field_of_view']
        print(f"FOV: {fov['width_arcmin']:.1f}' x {fov['height_arcmin']:.1f}'")
    print(f"Objects identified: {result['objects']['identified_count']}")
    print(f"Objects unidentified: {result['objects']['unidentified_count']}")

    return 0


if __name__ == "__main__":
    exit(main())
