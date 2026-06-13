import numpy as np
import json
import time
import argparse
import sys
try:
    import depthai as dai
except ImportError:
    pass # Will handle this gracefully in main()

def generate_mock_depth_map(base_depth=800, noise_level=5, shape=(400, 640)):
    """Generates a noisy flat surface depth map."""
    noise = np.random.normal(0, noise_level, shape).astype(np.float32)
    return np.full(shape, base_depth, dtype=np.float32) + noise

def create_depthai_pipeline():
    """Configures the OAK-D hardware pipeline for stereo depth."""
    pipeline = dai.Pipeline()

    # Define sources and outputs
    monoLeft = pipeline.create(dai.node.MonoCamera)
    monoRight = pipeline.create(dai.node.MonoCamera)
    depth = pipeline.create(dai.node.StereoDepth)
    xoutDepth = pipeline.create(dai.node.XLinkOut)

    xoutDepth.setStreamName("depth")

    # Properties
    monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

    # High density depth for better volumetric data
    depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    depth.setDepthAlign(dai.CameraBoardSocket.LEFT)

    # Linking
    monoLeft.out.link(depth.left)
    monoRight.out.link(depth.right)
    depth.depth.link(xoutDepth.input)

    return pipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock', action='store_true', help="Run with mock data instead of real OAK-D Lite")
    args = parser.parse_args()

    # --- Setup ---
    # The OAK-D Lite 400p resolution is 640x400
    frame_shape = (400, 640) 
    baseline_depth_map = None
    subsidence_threshold_mm = 50.0  # Anomaly if depth increases by 50mm
    last_print_time = 0
    start_time = time.time() 

    print("🚀 Starting Volumetric Core (Headless Terminal Mode)...")
    
    device = None
    depth_queue = None

    if args.mock:
        print("🔧 Mode: MOCK DATA (Simulation)")
    else:
        if 'depthai' not in sys.modules:
            print("❌ ERROR: 'depthai' library not installed. Run 'pip install depthai' or use --mock.")
            return
        
        print("🎥 Mode: OAK-D Lite (Hardware)")
        print("🔌 Connecting to camera...")
        try:
            pipeline = create_depthai_pipeline()
            device = dai.Device(pipeline)
            depth_queue = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            print("✅ Camera connected successfully!")
        except Exception as e:
            print(f"❌ Failed to connect to OAK-D Lite. Is it plugged in? Error: {e}")
            print("You can run with --mock to simulate it without hardware.")
            return

    # Take a baseline
    print("⏳ Capturing Baseline (Keep camera perfectly still!)...")
    if args.mock:
        baseline_depth_map = generate_mock_depth_map(shape=frame_shape)
    else:
        # Wait a couple seconds for the camera auto-exposure to settle
        time.sleep(2)
        # Grab the first valid frame
        inDepth = depth_queue.get()
        baseline_depth_map = inDepth.getFrame().astype(np.float32)
        
    print("✅ Baseline set. Monitoring for Volume Loss (Subsidence)...")
    if args.mock:
        print("ℹ️  Running mock state machine (Normal -> Operational -> Normal -> Swabakar)...")
    else:
        print("ℹ️  Running live hardware feed! Try the 'Book Drop' test now.")

    try:
        while True:
            current_time = time.time()
            is_swabakar = False # used for mock logic later

            # 1. Get Real-time Depth Map
            if args.mock:
                current_depth_map = generate_mock_depth_map(shape=frame_shape)
                elapsed_time = current_time - start_time
                cycle = int((elapsed_time // 10) % 4)
                is_collapsed = (cycle == 1 or cycle == 3)
                is_swabakar = (cycle == 3)

                if is_collapsed:
                    center_y, center_x = frame_shape[0]//2, frame_shape[1]//2
                    radius = 80
                    y, x = np.ogrid[-center_y:frame_shape[0]-center_y, -center_x:frame_shape[1]-center_x]
                    mask = x*x + y*y <= radius*radius
                    current_depth_map[mask] += 100.0  
            else:
                # Get real frame from OAK-D Lite
                inDepth = depth_queue.get()
                current_depth_map = inDepth.getFrame().astype(np.float32)

            # 2. Differential Processing (Real-time Z - Baseline Z)
            # We ignore 0 values (which mean 'out of range' or 'invalid pixel' in depthai)
            valid_mask = (current_depth_map > 0) & (baseline_depth_map > 0)
            diff_map = np.zeros_like(current_depth_map)
            diff_map[valid_mask] = current_depth_map[valid_mask] - baseline_depth_map[valid_mask]
            
            # 3. Thresholding (Volume Loss Detection)
            max_subsidence = np.max(diff_map)
            volume_loss_detected = bool(max_subsidence > subsidence_threshold_mm)
            
            # 4. Sensor Fusion (Mock Thermal & Gas data)
            temp_c = 35.0 + np.random.uniform(-1, 1)
            co_ppm = 120.0 + np.random.uniform(-5, 5)
            status_text = "NORMAL"
            confidence = "N/A"

            if volume_loss_detected:
                if args.mock and is_swabakar:
                    temp_c += 50.0 
                    co_ppm += 600.0
                    
                if temp_c > 60.0 and co_ppm > 400.0:
                    status_text = "CRITICAL_SWABAKAR"
                    confidence = "HIGH (Volume + Temp + CO)"
                else:
                    status_text = "OPERATIONAL_ACTIVITY"
                    confidence = "LOW (Volume loss only, no heat/gas)"

            # 5. Data Serialization
            payload = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "status": status_text,
                "confidence": confidence,
                "volume_loss_detected": volume_loss_detected,
                "max_subsidence_mm": round(float(max_subsidence), 2),
                "mock_sensors": {
                    "temperature_c": round(temp_c, 2),
                    "co_ppm": round(co_ppm, 2)
                }
            }
            
            if volume_loss_detected or (current_time - last_print_time >= 1.0):
                print(json.dumps(payload))
                last_print_time = current_time

            if args.mock:
                time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n🛑 Execution stopped by user.")
    finally:
        if device is not None:
            device.close()

if __name__ == "__main__":
    main()
