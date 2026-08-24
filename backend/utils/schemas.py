from dataclasses import dataclass
from typing import Optional

@dataclass
class AnalyzeTextRequest:
    text: str
    intent: Optional[str] = "pay"

    def __post_init__(self):
        if not self.text:
            raise ValueError("Text is required and cannot be empty.")
        if len(self.text) > 5000:
            raise ValueError("Text length exceeds the maximum limit of 5000 characters.")
        if self.intent is None:
            self.intent = "pay"

@dataclass
class AnalyzeQRRequest:
    qr_data: str

    def __post_init__(self):
        if not self.qr_data:
            raise ValueError("qr_data is required.")
        if len(self.qr_data) > 2000:
            raise ValueError("qr_data exceeds maximum limit of 2000 characters.")

@dataclass
class ReportFraudRequest:
    upi_id: str
    fraud_type: Optional[str] = "Suspicious Transaction"
    description: Optional[str] = None

    def __post_init__(self):
        if not self.upi_id:
            raise ValueError("upi_id is required.")
        if "@" not in self.upi_id:
            raise ValueError("Invalid UPI ID format. Must contain '@'.")
        self.upi_id = self.upi_id.lower().strip()
        
        if not self.fraud_type:
            self.fraud_type = "Suspicious Transaction"
        if self.description and len(self.description) > 1000:
            raise ValueError("description exceeds maximum limit of 1000 characters.")
