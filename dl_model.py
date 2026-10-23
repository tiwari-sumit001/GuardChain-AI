import torch
import torch.nn as nn

class FraudDetectionMLP(nn.Module):
    def __init__(self, input_dim=30):
        super(FraudDetectionMLP, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(32, 16),
            nn.BatchNorm1d(16),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(16, 1) # Sigmoid is applied in BCEWithLogitsLoss during training, and manually during inference
        )
        
    def forward(self, x):
        return self.network(x)
