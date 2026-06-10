# backend/services/ml_classifier.py
"""Naive Bayes machine learning text classifier for categorizing suspicious payment messages."""

import re
import math
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# -------------------------------
# TRAINING CORPUS (UPI SEC SCAM DATASET)
# -------------------------------
TRAINING_DATA: List[Tuple[str, str]] = [
    # Category: cashback_reward
    ("Congratulations! You won Rs 50000 cashback from GPay lottery. Click link to receive to bank account.", "cashback_reward"),
    ("Dear customer, Rs 25000 reward cash is pending in your PhonePe wallet. Claim now.", "cashback_reward"),
    ("GPay Cashback of Rs 10000 has been credited. Click link to claim.", "cashback_reward"),
    ("Paytm reward: You have received scratch card worth Rs 5000 cashback. Click here.", "cashback_reward"),
    ("Lucky lottery winner! Your mobile number won Rs 1,00,000 prize reward. Contact agent to transfer.", "cashback_reward"),
    ("Rs 7500 cashback reward is waiting. Click to claim in bank account.", "cashback_reward"),
    ("Claim your Rs 15000 cashback immediately. UPI voucher transfer pending.", "cashback_reward"),
    ("You received a scratch card cashback from Google Pay. Enter UPI PIN to claim credit.", "cashback_reward"),
    
    # Category: kyc_threat
    ("Dear user, your SBI bank account will block today. Update your KYC card details at link.", "kyc_threat"),
    ("Urgent KYC update: Your SIM card block within 24 hours. Contact bank support helpline at once.", "kyc_threat"),
    ("Alert: Account suspended due to missing PAN card KYC. Click here to verify.", "kyc_threat"),
    ("YBL block alert: Update PAN card details to avoid account suspension. Click to support helpline.", "kyc_threat"),
    ("Your netbanking access is disabled. Please verify KYC details to reactivate account.", "kyc_threat"),
    ("Urgent! Verify your debit card KYC profile within 1 hour or transaction access will be blocked.", "kyc_threat"),
    ("Bank notification: PAN card mismatch found. KYC verification required. Click link immediately.", "kyc_threat"),
    ("Dear customer, your bank login credentials will expire in 2 hours. Tap to verify KYC.", "kyc_threat"),

    # Category: bill_collect
    ("Electricity department alert: Your electricity connection will disconnect tonight due to unpaid bill. Pay immediately.", "bill_collect"),
    ("Your power bill of Rs 4200 is overdue. Disconnection order issued. Pay support VPA to cancel.", "bill_collect"),
    ("Water bill collection request: Rs 1500 overdue. Pay immediately to avoid suspension.", "bill_collect"),
    ("Overdue electricity bill payment request. Disconnection scheduled at 9:30 PM. Pay helpline now.", "bill_collect"),
    ("Broadband bill collection: Rs 999 pending. Pay collector now to avoid internet suspension.", "bill_collect"),
    ("Gas connection warning: Payment of Rs 1200 outstanding. Immediate disconnect if unpaid.", "bill_collect"),
    ("Monthly pipe gas bill collection reminder: Disconnection scheduled at 7 PM. Pay now.", "bill_collect"),
    
    # Category: safe_transaction
    ("Your transaction of Rs 150 to Sharma Grocery was successful. Balance: Rs 4200.", "safe_transaction"),
    ("Salary of Rs 65000 credited to your account. Available balance: Rs 78000.", "safe_transaction"),
    ("UPI transaction alert: Rs 500 debited from your bank account to star cafe.", "safe_transaction"),
    ("Money received: Rs 1200 successfully transferred from Rohan Kumar.", "safe_transaction"),
    ("Recharge of Rs 299 for mobile was successful. Transaction ID: TXN874112", "safe_transaction"),
    ("Dear customer, your request for check book has been received and processed.", "safe_transaction"),
    ("Electricity bill of Rs 2340 paid successfully to BEST power via AutoPay.", "safe_transaction"),
    ("HDFC bank: Rs 800 debited for dining at Dominoes on 02-06-2026.", "safe_transaction")
]

STOP_WORDS: Set[str] = {
    'is', 'the', 'a', 'to', 'and', 'of', 'in', 'your', 'for', 'from', 'has', 'have',
    'been', 'this', 'that', 'with', 'on', 'at', 'an', 'our', 'we', 'you', 'it', 'me',
    'my', 'will', 'was', 'were', 'be', 'by', 'as', 'but'
}


class NaiveBayesScamClassifier:
    """Naive Bayes text classifier mapping input strings to fraud vectors."""
    
    def __init__(self) -> None:
        self.class_counts: Dict[str, int] = defaultdict(int)
        self.word_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.class_word_totals: Dict[str, int] = defaultdict(int)
        self.vocabulary: Set[str] = set()
        self.total_docs: int = 0

    def tokenize(self, text: str) -> List[str]:
        """Cleans and extracts meaningful words from text, filtering stopwords."""
        words = re.findall(r'[a-zA-Z]+', text.lower())
        return [w for w in words if w not in STOP_WORDS and len(w) > 2]

    def train(self, data: List[Tuple[str, str]]) -> None:
        """Trains the Naive Bayes token frequency mapping lists.

        Args:
            data: List of tuples where entry is (text, category).
        """
        self.total_docs += len(data)
        for text, category in data:
            self.class_counts[category] += 1
            tokens = self.tokenize(text)
            for token in tokens:
                self.word_counts[category][token] += 1
                self.class_word_totals[category] += 1
                self.vocabulary.add(token)

    def classify(self, text: str) -> Dict[str, float]:
        """Computes probability vector for the categories.

        Args:
            text: Message body string to analyze.

        Returns:
            Dict[str, float]: Target class classification confidence percentages.
        """
        tokens = self.tokenize(text)
        if not tokens or not self.class_counts:
            if self.class_counts:
                equal_prob = 1.0 / len(self.class_counts)
                return {c: equal_prob for c in self.class_counts}
            return {"unknown": 1.0}

        scores: Dict[str, float] = {}
        vocab_size = len(self.vocabulary)

        for category, count in self.class_counts.items():
            prior = count / self.total_docs
            log_prob = math.log(prior)

            for token in tokens:
                if token in self.vocabulary:
                    word_freq = self.word_counts[category][token]
                    prob = (word_freq + 1) / (self.class_word_totals[category] + vocab_size)
                    log_prob += math.log(prob)

            scores[category] = log_prob

        max_log = max(scores.values())
        exp_scores = {c: math.exp(score - max_log) for c, score in scores.items()}
        total_exp = sum(exp_scores.values())
        
        probabilities = {c: round(v / total_exp, 2) for c, v in exp_scores.items()}
        return probabilities


# Global classifier instance
_classifier = NaiveBayesScamClassifier()


def retrain_model_from_db() -> None:
    """Reloads standard training data and appends SQLite feedback, updating active model."""
    global _classifier
    from services.history_store import get_reported_scams
    
    new_classifier = NaiveBayesScamClassifier()
    new_classifier.train(TRAINING_DATA)
    
    # Train on SQLite user reported feedback data
    db_data = get_reported_scams()
    if db_data:
        new_classifier.train(db_data)
        
    _classifier = new_classifier


# Initialize and pre-train classifier from database on startup
try:
    retrain_model_from_db()
except Exception:
    # Safe fallback if database is not initialized yet during load
    _classifier.train(TRAINING_DATA)


def predict_scam_probabilities(text: str) -> Dict[str, float]:
    """Exposes prediction interface on the active classifier instance."""
    return _classifier.classify(text)
