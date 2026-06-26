import os
import numpy as np

# Use lazy loading for onnxruntime because it takes time to import, or import at module level
# We will import it at the top, but handle exceptions
try:
    import onnxruntime as ort
except ImportError:
    ort = None

class AnomalyDetector:
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Look in the same folder as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "price_anomaly_detector.onnx")
        
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.load_model()
        
    def load_model(self):
        if ort is None:
            print("[AnomalyDetector] warning: onnxruntime is not installed. Anomaly detection disabled.")
            return
        
        if not os.path.exists(self.model_path):
            print(f"[AnomalyDetector] warning: Model file not found at {self.model_path}. Anomaly detection disabled.")
            return
            
        try:
            # Load ONNX session
            self.session = ort.InferenceSession(self.model_path)
            self.input_name = self.session.get_inputs()[0].name
            print(f"[AnomalyDetector] successfully loaded ONNX model from {self.model_path}")
        except Exception as e:
            print(f"[AnomalyDetector] error loading model: {e}")
            self.session = None
            
    def predict(self, price_ratio: float, pct_change: float):
        """
        Predicts if a price update is anomalous.
        Inputs:
          price_ratio: current_price / historical_median
          pct_change: (current_price - last_price) / last_price
        
        Returns:
          is_anomaly: bool (True if anomalous)
          score: float (raw decision score; lower means more anomalous)
        """
        # Fallback if model not loaded
        if self.session is None:
            return False, 0.0
            
        try:
            # Inputs must be float32 with shape (1, 2)
            input_data = np.array([[price_ratio, pct_change]], dtype=np.float32)
            outputs = self.session.run(None, {self.input_name: input_data})
            
            # IsolationForest in ONNX outputs:
            # outputs[0]: label array of shape [N] (value: 1 for normal, -1 for anomaly)
            # outputs[1]: scores array of shape [N, 1] (or similar) representing decision score
            label = int(outputs[0][0])
            is_anomaly = (label == -1)
            
            # Get decision function score if available
            score = 0.0
            if len(outputs) > 1:
                # The score output contains the raw scores.
                # In IsolationForest, lower scores represent more outlier-like instances.
                score = float(outputs[1][0])
                
            return is_anomaly, score
        except Exception as e:
            print(f"[AnomalyDetector] prediction error: {e}")
            return False, 0.0

# Singleton instance
detector = AnomalyDetector()
