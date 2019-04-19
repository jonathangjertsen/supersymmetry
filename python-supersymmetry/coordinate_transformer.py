import numpy as np

class CoordinateTransformer(object):
    def __init__(self, transform):
        self.transform_ = transform
    
    def transform(self, in_vectors, exp=1):
        if len(in_vectors) == 0:
            return np.array(in_vectors)
        if exp != 1:
            return in_vectors @ np.linalg.matrix_power(self.transform_, exp)
        return in_vectors @ self.transform_
    
    def __call__(self, *args, **kwargs):
        return self.transform(*args, **kwargs)
