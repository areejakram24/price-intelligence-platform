import os
import logging
import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

# Uniform system logging wrapper
logger = logging.getLogger(__name__)

class AnomalyDetector:
    """ONNX Runtime abstraction driver running high-density vector evaluation passes."""
    def __init__(self, model_path: str = None):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "price_anomaly_detector.onnx")
        
        self.model_path = model_path
        self.session = None
        self.input_name = None
        self.load_model()
        
    def load_model(self):
        if ort is None:
            logger.warning("[ONNX ML] Runtime platform library 'onnxruntime' missing. Anomaly processing bypassed.")
            return
        
        if not os.path.exists(self.model_path):
            logger.warning(f"[ONNX ML] Serialization artifact binary not found at {self.model_path}. Inference disabled.")
            return
            
        try:
            self.session = ort.InferenceSession(self.model_path)
            self.input_name = self.session.get_inputs()[0].name
            logger.info(f"[ONNX ML] Inference session mapping hooked cleanly onto model: {self.model_path}")
        except Exception as e:
            logger.error(f"[ONNX ML] Critical lifecycle setup fault mapping metadata targets: {e}")
            self.session = None
            
    def predict(self, price_ratio: float, pct_change: float):
        """
        Executes an outlier evaluation pass via a compiled multi-dimensional IsolationForest vector.
        
        Inputs:
          price_ratio: current_price / historical_median
          pct_change: (current_price - last_price) / last_price
        """
        if self.session is None:
            return False, 0.0
            
        try:

            input_data = np.array([[price_ratio, pct_change]], dtype=np.float32)
            outputs = self.session.run(None, {self.input_name: input_data})
            
            label = int(outputs[0][0])
            is_anomaly = (label == -1)
            
            score = float(outputs[1][0]) if len(outputs) > 1 else 0.0
            return is_anomaly, score
            
        except Exception as e:
            logger.error(f"[ONNX ML] Matrix tracking inference math fault encountered: {e}")
            return False, 0.0

detector = AnomalyDetector()