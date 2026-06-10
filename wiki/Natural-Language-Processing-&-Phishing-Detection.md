# NLP & Phishing Detection 🧠

Fraudsters frequently use WhatsApp, SMS, or mock payment pages to distribute phishing links, fake invoices, or cash prize notifications. SuRaksha uses Natural Language Processing (NLP) combined with fuzzy string matching to block these phishing vectors.

---

## 🤖 Naive Bayes Classifier

The system utilizes a **Multinomial Naive Bayes** machine learning model combined with **TF-IDF (Term Frequency-Inverse Document Frequency)** vectorization to analyze text context and classify messages into threat categories.

### Feature Extraction (TF-IDF)
The text input is processed into numerical vectors representing word frequency adjusted for how common a word is across the entire training corpus:
$$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log\left(\frac{|D|}{|\{d \in D : t \in d\}|}\right)$$

### Naive Bayes Classification
The classifier calculates the probability of a message belonging to a class $C_k$ (e.g. *Phishing Link*, *Urgent Block*, *Legitimate*) using Bayes' Theorem:
$$P(C_k | x_1, \dots, x_n) \propto P(C_k) \prod_{i=1}^{n} P(x_i | C_k)$$

### Classifier Categories
Scans classify text inputs into specific threat taxonomy classes:
- `collect_request`: Social engineering trying to get users to approve payment requests.
- `phishing_urgency`: Phishing claims requiring urgent action (e.g. KYC blocked, electricity cut).
- `cashback_scam`: Fake lottery or cashback rewards.
- `legitimate`: Standard transactional confirmations.

---

## 🇮🇳 Multilingual Threat Mapping

To protect users across diverse regional demographics in India, the text scanning engine implements regex dictionaries across five major languages:

* **English**: Checks for keywords like `won lottery`, `KYC block`, `gift card`, `update password`.
* **Hindi (Devanagari)**: Detects phrases like `लॉटरी जीती`, `बिजली कनेक्शन`, `केवाईसी ब्लॉक`.
* **Bengali**: Matches terms like `লটারি জিতেছেন`, `বিদ্যুৎ সংযোগ`, `কেওয়াইসি বন্ধ`.
* **Tamil**: Scans for patterns like `பணம் வென்றீர்கள்`, `மின் இணைப்பு`, `கேஒய்சி முடக்கம்`.
* **Telugu**: Identifies markers like `లాటరీ గెలుచుకున్నారు`, `విద్యుత్ కనెక్షన్`, `కేవైసీ బ్లాక్`.

These patterns feed directly into the weighted risk aggregator if matched, bypassing generic model evaluations to raise threat alerts.

---

## 🔍 Fuzzy Matcher & Typosquat Detection

Scammers register VPAs (Virtual Payment Addresses) that closely mimic reputable merchants or organizations to trick users (e.g. `electricity.bill@ybl` typosquatting the official merchant domain).

SuRaksha detects these mimicry attempts using two algorithms:

### 1. Sliding Window Edit-Distance Comparison
The system compares VPA handles against common UPI provider brands (such as Paytm, PhonePe, Google Pay, BHIM, SBI) using Gestalt Pattern Matching:
- **Matcher threshold**: A similarity ratio $\ge 0.85$ (SequenceMatcher edit-distance metric) flags potential typosquatting.
- **Example**: An input handle containing `paytml@ybl` is matched against the registered brand `paytm`. It yields a similarity ratio of `0.91` (above the `0.85` threshold), generating an immediate high-risk warning.

### 2. Jaccard Similarity name matcher
To verify invoice display names against VPA handles (e.g. confirming whether an invoice showing payee "Sharma Kirana Store" matches a VPA like `attacker@upi`), the engine computes a token-based Jaccard similarity index:
$$J(A, B) = \frac{|A \cap B|}{|A \cup B|}$$

- **Order-Invariant**: By splitting names into sets of tokens, the similarity match remains accurate even if word orders are swapped (e.g. "Kirana Store Sharma" matches "Sharma Kirana Store").
- **Substring overrides**: If the cleaned VPA username is a substring of the merchant display name, similarity is overridden to `1.0` to eliminate false positives for legitimately compressed names.
