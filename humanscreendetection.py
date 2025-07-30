#!/usr/bin/env python3
"""
Enhanced Human Detection - Multi-Method Approach with Improved Accuracy
Combines motion detection, HOG, and deep learning for better human detection
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import threading
import time
from PIL import Image, ImageTk, ImageGrab

class EnhancedHumanTracker:
    def __init__(self):
        print("🔄 Initializing Enhanced Human Tracker...")
        
        # Initialize detection methods
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Load YOLOv3 model for better detection
        self.yolo_net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.layer_names = self.yolo_net.getLayerNames()
        self.output_layers = [self.layer_names[i[0] - 1] for i in self.yolo_net.getUnconnectedOutLayers()]
        
        # Background subtraction for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False)
        
        # Tracking variables
        self.running = False
        self.capture_thread = None
        self.fps = 15  # Increased frame rate
        self.frame_delay = 1.0 / self.fps
        
        # Detection parameters
        self.detection_methods = {
            'motion': True,
            'hog': True,
            'yolo': True,
            'contour': True
        }
        
        # Motion detection settings
        self.min_motion_area = 1500  # Reduced minimum area
        self.max_motion_area = 80000  # Reduced maximum area
        self.min_aspect_ratio = 1.5  # Adjusted for better human proportions
        self.max_aspect_ratio = 3.5
        
        # HOG settings
        self.hog_threshold = 0.4  # Adjusted threshold
        
        # Stats
        self.capture_count = 0
        self.detection_count = 0
        self.frame_buffer = []
        self.prev_detections = []
        
        # GUI elements
        self.root = None
        self.overlay_window = None
        self.canvas = None
        self.photo = None
        
        # Region selection
        self.selection_region = {'x': 100, 'y': 100, 'width': 1000, 'height': 700}
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.region_visible = False
        
        print("✅ Enhanced Human Tracker initialized")
        self.setup_gui()
    
    def setup_gui(self):
        """Create user interface"""
        self.root = tk.Tk()
        self.root.title("🎯 Enhanced Human Tracker")
        self.root.geometry("600x550")
        self.root.attributes('-topmost', True)
        
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Enhanced Human Tracker", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready for enhanced detection", 
                                     font=('Arial', 10), foreground='green')
        self.status_label.pack(pady=(0, 10))
        
        # Controls
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(controls_frame, text="🚀 Start Detection", 
                                   command=self.toggle_tracking)
        self.start_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Region controls
        region_frame = ttk.LabelFrame(main_frame, text="Detection Region", padding="10")
        region_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.region_btn = ttk.Button(region_frame, text="👁️ Show Detection Area", 
                                    command=self.toggle_region)
        self.region_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Size controls
        size_frame = ttk.Frame(region_frame)
        size_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(size_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.IntVar(value=1000)
        width_scale = ttk.Scale(size_frame, from_=600, to=1600, variable=self.width_var,
                               orient=tk.HORIZONTAL, command=self.update_region_size)
        width_scale.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))
        
        ttk.Label(size_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.IntVar(value=700)
        height_scale = ttk.Scale(size_frame, from_=400, to=1200, variable=self.height_var,
                                orient=tk.HORIZONTAL, command=self.update_region_size)
        height_scale.grid(row=1, column=1, sticky=tk.EW, padx=(5, 0))
        
        size_frame.columnconfigure(1, weight=1)
        
        # Detection methods
        methods_frame = ttk.LabelFrame(main_frame, text="Detection Methods", padding="10")
        methods_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.motion_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(methods_frame, text="🏃 Motion Analysis", 
                       variable=self.motion_var).pack(anchor=tk.W)
        
        self.hog_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(methods_frame, text="🚶 HOG Person Detection", 
                       variable=self.hog_var).pack(anchor=tk.W)
        
        self.yolo_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(methods_frame, text="🧠 Deep Learning (YOLO)", 
                       variable=self.yolo_var).pack(anchor=tk.W)
        
        self.contour_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(methods_frame, text="👤 Shape Analysis", 
                       variable=self.contour_var).pack(anchor=tk.W)
        
        # Sensitivity
        sens_frame = ttk.LabelFrame(main_frame, text="Detection Sensitivity", padding="10")
        sens_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(sens_frame, text="Sensitivity:").pack(anchor=tk.W)
        self.sensitivity_var = tk.DoubleVar(value=0.7)
        sens_scale = ttk.Scale(sens_frame, from_=0.1, to=1.0, variable=self.sensitivity_var,
                              orient=tk.HORIZONTAL)
        sens_scale.pack(fill=tk.X, pady=(5, 0))
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Detection Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="Ready for detection", 
                                    font=('Courier', 9))
        self.stats_label.pack()
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                               text="• Uses multiple advanced detection methods\n• Combines motion, HOG and deep learning\n• Better accuracy for all scenarios\n• Drag region to reposition",
                               font=('Arial', 8), foreground='gray')
        instructions.pack(pady=(10, 0))
        
        # Start stats update
        self.update_stats()
    
    def toggle_tracking(self):
        """Toggle tracking on/off"""
        if not self.running:
            self.start_tracking()
        else:
            self.stop_tracking()
    
    def start_tracking(self):
        """Start human tracking"""
        self.running = True
        self.start_btn.config(text="⏹️ Stop Detection")
        self.status_label.config(text="🎯 Detection active", foreground='blue')
        
        # Reset background model
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=16, detectShadows=False)
        
        # Reset stats
        self.capture_count = 0
        self.detection_count = 0
        self.frame_buffer = []
        self.prev_detections = []
        
        # Show region
        if not self.region_visible:
            self.show_region()
        
        # Start detection thread
        self.capture_thread = threading.Thread(target=self.detection_loop, daemon=True)
        self.capture_thread.start()
        
        print("🎯 Started human detection")
    
    def stop_tracking(self):
        """Stop tracking"""
        self.running = False
        self.start_btn.config(text="🚀 Start Detection")
        self.status_label.config(text="🛑 Detection stopped", foreground='orange')
        print("🛑 Detection stopped")
    
    def detection_loop(self):
        """Main detection loop with multiple methods"""
        while self.running:
            start_time = time.time()
            
            try:
                # Capture screen
                frame = self.capture_screen()
                if frame is None:
                    continue
                
                # Detect humans using multiple methods
                detections = self.detect_humans_advanced(frame)
                
                # Track detections over time
                tracked_detections = self.track_detections(detections)
                
                # Draw results
                self.draw_detections(frame, tracked_detections)
                
                # Update overlay
                self.update_overlay(frame)
                
                self.capture_count += 1
                
            except Exception as e:
                print(f"Detection error: {e}")
            
            # Frame rate control
            elapsed = time.time() - start_time
            sleep_time = self.frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def capture_screen(self):
        """Capture screen region"""
        try:
            region = self.selection_region
            bbox = (region['x'], region['y'],
                   region['x'] + region['width'],
                   region['y'] + region['height'])
            
            img = ImageGrab.grab(bbox=bbox, all_screens=True)
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Capture error: {e}")
            return None
    
    def detect_humans_advanced(self, frame):
        """Advanced human detection using multiple methods"""
        all_detections = []
        
        # Update sensitivity settings
        sensitivity = self.sensitivity_var.get()
        self.hog_threshold = 0.7 - (sensitivity * 0.5)  # 0.2 to 0.7
        self.min_motion_area = int(1000 + (1 - sensitivity) * 2000)  # 1000-3000
        
        # Method 1: Motion-based detection
        if self.motion_var.get():
            motion_detections = self.detect_motion_humans(frame)
            all_detections.extend([(det, 'motion', 0.6) for det in motion_detections])
        
        # Method 2: HOG people detection
        if self.hog_var.get():
            hog_detections = self.detect_hog_humans(frame)
            all_detections.extend([(det, 'hog', 0.8) for det in hog_detections])
        
        # Method 3: YOLO deep learning
        if self.yolo_var.get():
            yolo_detections = self.detect_yolo_humans(frame)
            all_detections.extend([(det, 'yolo', 0.9) for det in yolo_detections])
        
        # Method 4: Contour shape analysis
        if self.contour_var.get():
            shape_detections = self.detect_human_shapes(frame)
            all_detections.extend([(det, 'shape', 0.5) for det in shape_detections])
        
        # Combine and filter detections
        final_detections = self.combine_detections(all_detections)
        self.detection_count = len(final_detections)
        
        return final_detections
    
    def detect_motion_humans(self, frame):
        """Detect humans based on motion analysis"""
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        human_detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if self.min_motion_area <= area <= self.max_motion_area:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (humans are taller than wide)
                aspect_ratio = h / w if w > 0 else 0
                
                if self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio:
                    # Additional checks for human-like movement
                    if self.is_human_like_motion(contour, x, y, w, h):
                        human_detections.append((x, y, w, h))
        
        return human_detections
    
    def detect_hog_humans(self, frame):
        """HOG-based human detection with optimized parameters"""
        try:
            # Resize for better performance
            height, width = frame.shape[:2]
            if width > 800:
                scale = 800 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized = cv2.resize(frame, (new_width, new_height))
            else:
                resized = frame
                scale = 1.0
            
            # HOG detection
            boxes, weights = self.hog.detectMultiScale(
                resized,
                winStride=(4, 4),  # More sensitive stride
                padding=(8, 8),
                scale=1.03,  # Slightly more scales
                hitThreshold=self.hog_threshold
            )
            
            # Scale back and filter
            human_detections = []
            for i, (x, y, w, h) in enumerate(boxes):
                if scale != 1.0:
                    x = int(x / scale)
                    y = int(y / scale)
                    w = int(w / scale)
                    h = int(h / scale)
                
                # Filter by size and confidence
                if 50 <= w <= 300 and 100 <= h <= 600:
                    confidence = weights[i] if i < len(weights) else 0.5
                    if confidence > self.hog_threshold:
                        human_detections.append((x, y, w, h))
            
            return human_detections
            
        except Exception as e:
            print(f"HOG detection error: {e}")
            return []
    
    def detect_yolo_humans(self, frame):
        """Use YOLOv3 deep learning for human detection"""
        try:
            height, width = frame.shape[:2]
            
            # Preprocess image for YOLO
            blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            self.yolo_net.setInput(blob)
            outs = self.yolo_net.forward(self.output_layers)
            
            # Process detections
            class_ids = []
            confidences = []
            boxes = []
            
            for out in outs:
                for detection in out:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]
                    
                    if confidence > 0.5 and class_id == 0:  # 0 is person in COCO
                        # Object detected
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)
                        
                        # Rectangle coordinates
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)
                        
                        boxes.append([x, y, w, h])
                        confidences.append(float(confidence))
            
            # Apply non-max suppression
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
            
            human_detections = []
            for i in indices:
                i = i[0]
                box = boxes[i]
                x, y, w, h = box
                human_detections.append((x, y, w, h))
            
            return human_detections
            
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return []
    
    def detect_human_shapes(self, frame):
        """Detect human-like shapes using contour analysis"""
        # Convert to grayscale and apply edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 100)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        human_shapes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            if 800 <= area <= 40000:  # Adjusted area range
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check human-like proportions
                aspect_ratio = h / w if w > 0 else 0
                if 1.5 <= aspect_ratio <= 3.5:
                    # Check contour complexity
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if 0.15 <= circularity <= 0.6:  # Adjusted range
                            human_shapes.append((x, y, w, h))
        
        return human_shapes
    
    def is_human_like_motion(self, contour, x, y, w, h):
        """Additional checks for human-like motion patterns"""
        # Check if the contour has reasonable solidity
        area = cv2.contourArea(contour)
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        
        if hull_area > 0:
            solidity = area / hull_area
            if 0.5 <= solidity <= 0.9:  # Adjusted solidity range
                return True
        
        return False
    
    def combine_detections(self, all_detections):
        """Combine detections from multiple methods and remove duplicates"""
        if not all_detections:
            return []
        
        # Group by type
        motion_dets = [(det, conf) for det, dtype, conf in all_detections if dtype == 'motion']
        hog_dets = [(det, conf) for det, dtype, conf in all_detections if dtype == 'hog']
        yolo_dets = [(det, conf) for det, dtype, conf in all_detections if dtype == 'yolo']
        shape_dets = [(det, conf) for det, dtype, conf in all_detections if dtype == 'shape']
        
        final_detections = []
        
        # Prioritize YOLO detections (most reliable)
        for det, conf in yolo_dets:
            final_detections.append((det, 'yolo', conf))
        
        # Add HOG detections that don't overlap with YOLO
        for hog_det, conf in hog_dets:
            overlap = False
            for existing_det, _, _ in final_detections:
                if self.calculate_overlap(hog_det, existing_det) > 0.4:
                    overlap = True
                    break
            if not overlap:
                final_detections.append((hog_det, 'hog', conf))
        
        # Add motion detections that don't overlap
        for motion_det, conf in motion_dets:
            overlap = False
            for existing_det, _, _ in final_detections:
                if self.calculate_overlap(motion_det, existing_det) > 0.3:
                    overlap = True
                    break
            if not overlap:
                final_detections.append((motion_det, 'motion', conf))
        
        # Add shape detections that don't overlap
        for shape_det, conf in shape_dets:
            overlap = False
            for existing_det, _, _ in final_detections:
                if self.calculate_overlap(shape_det, existing_det) > 0.3:
                    overlap = True
                    break
            if not overlap:
                final_detections.append((shape_det, 'shape', conf))
        
        return final_detections
    
    def calculate_overlap(self, det1, det2):
        """Calculate overlap ratio between two detections"""
        x1, y1, w1, h1 = det1
        x2, y2, w2, h2 = det2
        
        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def track_detections(self, detections):
        """Track detections over time for stability"""
        # Simple tracking - could be improved with Kalman filters
        self.prev_detections = detections
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw detection results"""
        colors = {
            'yolo': (0, 255, 0),      # Green - most reliable
            'hog': (0, 165, 255),     # Orange
            'motion': (255, 255, 0),  # Yellow
            'shape': (255, 0, 255)    # Magenta
        }
        
        for i, (detection, det_type, confidence) in enumerate(detections):
            x, y, w, h = detection
            color = colors.get(det_type, (255, 255, 255))
            
            # Draw thick rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw center point
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), 5, color, -1)
            
            # Draw label with confidence
            label = f"{det_type.upper()}: {confidence:.1f}"
            cv2.putText(frame, label, (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def show_region(self):
        """Show detection region overlay"""
        if self.overlay_window:
            self.overlay_window.destroy()
        
        self.overlay_window = tk.Toplevel(self.root)
        self.overlay_window.title("Detection Region")
        self.overlay_window.attributes('-topmost', True)
        self.overlay_window.attributes('-alpha', 0.75)
        self.overlay_window.overrideredirect(True)
        
        # Position window
        region = self.selection_region
        self.overlay_window.geometry(f"{region['width']}x{region['height']}+{region['x']}+{region['y']}")
        
        # Create canvas
        self.canvas = tk.Canvas(self.overlay_window, 
                               width=region['width'], height=region['height'],
                               bg='black', highlightthickness=4, highlightcolor='cyan')
        self.canvas.pack()
        
        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # Draw border
        self.canvas.create_rectangle(4, 4, region['width']-4, region['height']-4,
                                   outline='cyan', width=4, tags="border")
        
        # Draw title
        self.canvas.create_text(region['width']//2, 30,
                              text="🎯 HUMAN DETECTION AREA - Drag to Move",
                              fill='cyan', font=('Arial', 12, 'bold'))
        
        self.region_visible = True
        self.region_btn.config(text="🙈 Hide Detection Area")
    
    def hide_region(self):
        """Hide detection region"""
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None
            self.canvas = None
        
        self.region_visible = False
        self.region_btn.config(text="👁️ Show Detection Area")
    
    def toggle_region(self):
        """Toggle region visibility"""
        if self.region_visible:
            self.hide_region()
        else:
            self.show_region()
    
    def on_click(self, event):
        """Handle region click"""
        self.dragging = True
        self.drag_start_x = event.x_root - self.selection_region['x']
        self.drag_start_y = event.y_root - self.selection_region['y']
    
    def on_drag(self, event):
        """Handle region drag"""
        if self.dragging:
            new_x = max(0, event.x_root - self.drag_start_x)
            new_y = max(0, event.y_root - self.drag_start_y)
            
            self.selection_region['x'] = new_x
            self.selection_region['y'] = new_y
            
            self.overlay_window.geometry(f"+{new_x}+{new_y}")
    
    def on_release(self, event):
        """Handle region release"""
        self.dragging = False
    
    def update_region_size(self, value=None):
        """Update region size"""
        if self.overlay_window:
            self.selection_region['width'] = int(self.width_var.get())
            self.selection_region['height'] = int(self.height_var.get())
            
            region = self.selection_region
            self.overlay_window.geometry(f"{region['width']}x{region['height']}+{region['x']}+{region['y']}")
            self.canvas.config(width=region['width'], height=region['height'])
            
            # Redraw border
            self.canvas.delete("border")
            self.canvas.create_rectangle(4, 4, region['width']-4, region['height']-4,
                                       outline='cyan', width=4, tags="border")
    
    def update_overlay(self, frame):
        """Update overlay with processed frame"""
        if not self.overlay_window or not self.canvas:
            return
        
        try:
            # Convert to display format
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            
            # Resize to fit canvas
            region = self.selection_region
            img = img.resize((region['width'], region['height']), Image.Resampling.LANCZOS)
            
            self.photo = ImageTk.PhotoImage(image=img)
            
            # Update canvas
            self.canvas.delete("frame")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo, tags="frame")
            self.canvas.tag_raise("border")
            
        except Exception as e:
            print(f"Overlay update error: {e}")
    
    def update_stats(self):
        """Update statistics"""
        if not self.root:
            return
        
        try:
            if self.running:
                stats_text = f"Humans detected: {self.detection_count} | Frames processed: {self.capture_count}"
                if self.capture_count > 0:
                    detection_rate = (self.detection_count / self.capture_count) * 100
                    stats_text += f" | Detection rate: {detection_rate:.1f}%"
            else:
                stats_text = "Ready for detection"
            
            self.stats_label.config(text=stats_text)
        except Exception as e:
            print(f"Stats update error: {e}")
        
        self.root.after(500, self.update_stats)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🎯 Starting Enhanced Human Tracker...")
    tracker = EnhancedHumanTracker()
    tracker.run()