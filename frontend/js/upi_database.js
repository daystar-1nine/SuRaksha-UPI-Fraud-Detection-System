// Local Demonstration Database of UPI IDs
// This file is used to demonstrate the functionality to college faculty.
// You can edit the UPI IDs here with 10-15 Real UPI IDs.

const UPIDatabase = {
    "safe": {
        "personal": [
            "demo.personal1@okaxis",
            "friend.test@ybl"
            // Add your real personal UPI IDs here
        ],
        "business": [
            "merchant@okicici",
            "shop.test@paytm",
            "business.demo@sbi"
            // Add your real business UPI IDs here
        ]
    },
    "unsafe": {
        "fraud": [
            "fraudster1@ybl",
            "fake.reward@paytm"
            // Add known fraud/scam UPI IDs here
        ],
        "criminal": [
            "blacklisted.user@okicici",
            "scam.network@sbi"
            // Add known criminal activity UPI IDs here
        ]
    }
};

// Function to classify a UPI ID based on the local database
function classifyUPI(upiId) {
    if (!upiId) return { risk: "unknown", type: "unknown", category: "unknown" };
    upiId = upiId.toLowerCase().trim();

    if (UPIDatabase.safe.personal.includes(upiId)) return { risk: "low", type: "safe", category: "personal" };
    if (UPIDatabase.safe.business.includes(upiId)) return { risk: "low", type: "safe", category: "business" };
    
    if (UPIDatabase.unsafe.fraud.includes(upiId)) return { risk: "high", type: "unsafe", category: "fraud" };
    if (UPIDatabase.unsafe.criminal.includes(upiId)) return { risk: "critical", type: "unsafe", category: "criminal" };

    return null; // Not found in local database
}
