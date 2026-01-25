"""
Contrast-based celestial object detector.

This detector identifies celestial objects by finding regions that contrast
significantly against the local sky background. It handles various object types:
- Bright point sources (stars, planets)
- Faint point sources (dim stars)
- Extended objects (galaxies, nebulae)
- Dense regions (star clusters)
"""

from typing import List
import numpy as np
from PIL import Image as PILImage
from scipy import ndimage
from astropy.stats import sigma_clipped_stats

from src.tools.capture_sky.types import DetectedObject, ImagePosition
from src.tools.capture_sky.object_detector.object_detector_interface import CelestialObjectDetector


class ContrastObjectDetector(CelestialObjectDetector):
    """
    Detects celestial objects using adaptive contrast thresholding.
    
    The algorithm:
    1. Convert to grayscale
    2. Apply Gaussian blur to reduce noise
    3. Compute background statistics using sigma-clipped mean
    4. Create binary mask of pixels above threshold
    5. Find connected components
    6. Filter by size and compute centroids
    """
    
    def __init__(
        self,
        sigma_threshold: float = 3.0,
        min_area_px: int = 4,
        max_area_px: int = 10000,
        blur_sigma: float = 1.0,
        merge_distance_px: float = 5.0
    ):
        """
        Initialize the contrast detector.
        
        Args:
            sigma_threshold: Number of standard deviations above background 
                             to consider a pixel as part of an object.
                             Lower values detect fainter objects but may
                             introduce noise.
            min_area_px: Minimum connected region area to be considered an object.
                        Helps filter out hot pixels and noise.
            max_area_px: Maximum connected region area. Larger regions may be
                        artifacts or very extended objects.
            blur_sigma: Gaussian blur sigma for noise reduction.
                       Higher values smooth more but may merge nearby objects.
            merge_distance_px: Objects closer than this distance will be merged.
                              Helps with clusters that might be over-segmented.
        """
        self.sigma_threshold = sigma_threshold
        self.min_area_px = min_area_px
        self.max_area_px = max_area_px
        self.blur_sigma = blur_sigma
        self.merge_distance_px = merge_distance_px
    
    @property
    def name(self) -> str:
        return "ContrastDetector"
    
    def detect(self, image: PILImage.Image) -> List[DetectedObject]:
        """
        Detect celestial objects in the image.
        
        Args:
            image: PIL Image (RGB or grayscale)
        
        Returns:
            List of DetectedObject sorted by brightness (brightest first)
        """
        # Convert to grayscale numpy array
        if image.mode != 'L':
            gray = image.convert('L')
        else:
            gray = image
        
        img_array = np.array(gray, dtype=np.float64)
        height, width = img_array.shape
        
        # Apply Gaussian blur to reduce noise
        if self.blur_sigma > 0:
            from scipy.ndimage import gaussian_filter
            img_smoothed = gaussian_filter(img_array, sigma=self.blur_sigma)
        else:
            img_smoothed = img_array
        
        # Calculate background statistics using sigma clipping
        # This gives a robust estimate of the sky background
        try:
            mean, median, std = sigma_clipped_stats(img_smoothed, sigma=3.0)
        except Exception:
            # Fallback if sigma_clipped_stats fails
            mean = np.mean(img_smoothed)
            median = np.median(img_smoothed)
            std = np.std(img_smoothed)
        
        # Calculate threshold: pixels significantly above background
        threshold = median + (self.sigma_threshold * std)
        
        # Create binary mask
        binary_mask = img_smoothed > threshold
        
        # Label connected components
        labeled_array, num_features = ndimage.label(binary_mask)  # type: ignore[misc]
        
        if num_features == 0:
            return []
        
        # Analyze each connected component
        detected_objects = []
        
        for label_id in range(1, num_features + 1):
            # Get mask for this component
            component_mask = labeled_array == label_id
            
            # Calculate area
            area = np.sum(component_mask)
            
            # Filter by size
            if area < self.min_area_px or area > self.max_area_px:
                continue
            
            # Get pixel coordinates of the component
            y_coords, x_coords = np.where(component_mask)
            
            # Calculate intensity-weighted centroid for better accuracy
            intensities = img_array[component_mask]
            total_intensity = np.sum(intensities)
            
            if total_intensity > 0:
                x_centroid = np.sum(x_coords * intensities) / total_intensity
                y_centroid = np.sum(y_coords * intensities) / total_intensity
            else:
                x_centroid = np.mean(x_coords)
                y_centroid = np.mean(y_coords)
            
            # Calculate approximate radius (equivalent circle radius)
            radius = np.sqrt(area / np.pi)
            
            # Calculate brightness (peak intensity above background)
            peak_intensity = np.max(intensities)
            brightness = peak_intensity - median
            
            # Determine if point source or extended
            # Point sources have small area relative to their brightness
            is_point_source = bool(area < 50 and radius < 5)
            
            detected_objects.append(DetectedObject(
                position=ImagePosition(pixel_x=float(x_centroid), pixel_y=float(y_centroid), radius_px=float(radius)),
                brightness=float(brightness),
                area_px=float(area),
                is_point_source=is_point_source
            ))
        
        # Merge nearby detections (handles over-segmentation of extended objects)
        detected_objects = self._merge_nearby_objects(detected_objects)
        
        # Sort by brightness (brightest first)
        detected_objects.sort(key=lambda obj: obj.brightness, reverse=True)
        
        return detected_objects
    
    def _merge_nearby_objects(self, objects: List[DetectedObject]) -> List[DetectedObject]:
        """
        Merge objects that are very close together.
        
        This handles cases where a single extended object might be
        detected as multiple connected components.
        """
        if len(objects) <= 1 or self.merge_distance_px <= 0:
            return objects
        
        merged = []
        used = set()
        
        for i, obj1 in enumerate(objects):
            if i in used:
                continue
            
            # Find all objects to merge with this one
            to_merge = [obj1]
            used.add(i)
            
            for j, obj2 in enumerate(objects):
                if j in used:
                    continue
                
                # Calculate distance between centroids
                distance = np.sqrt(
                    (obj1.position.pixel_x - obj2.position.pixel_x)**2 + 
                    (obj1.position.pixel_y - obj2.position.pixel_y)**2
                )
                
                # Also consider if they overlap based on radii
                combined_radius = obj1.position.radius_px + obj2.position.radius_px
                
                if distance < self.merge_distance_px or distance < combined_radius:
                    to_merge.append(obj2)
                    used.add(j)
            
            # Create merged object
            if len(to_merge) == 1:
                merged.append(obj1)
            else:
                # Weighted average by brightness
                total_brightness = sum(o.brightness for o in to_merge)
                if total_brightness > 0:
                    x_merged = sum(o.position.pixel_x * o.brightness for o in to_merge) / total_brightness
                    y_merged = sum(o.position.pixel_y * o.brightness for o in to_merge) / total_brightness
                else:
                    x_merged = np.mean([o.position.pixel_x for o in to_merge])
                    y_merged = np.mean([o.position.pixel_y for o in to_merge])
                
                # Combined properties
                total_area = sum(o.area_px or 0 for o in to_merge)
                max_brightness = max(o.brightness for o in to_merge)
                combined_radius = np.sqrt(total_area / np.pi) if total_area > 0 else max(o.position.radius_px for o in to_merge)
                
                merged.append(DetectedObject(
                    position=ImagePosition(pixel_x=float(x_merged), pixel_y=float(y_merged), radius_px=float(combined_radius)),
                    brightness=float(max_brightness),
                    area_px=float(total_area),
                    is_point_source=False  # Merged objects are typically extended
                ))
        
        return merged
