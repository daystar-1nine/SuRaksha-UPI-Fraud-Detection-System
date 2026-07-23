// Local Demonstration Database of UPI IDs
// This file is used to demonstrate the functionality to college faculty.

const UPIDatabase = {
    "safe": {
        "personal": [
            "demo.personal1@okaxis",
            "friend.test@ybl",
            "9168772121@yespop",
            "9168772121@mbkns",
            "9168772121@mbk",
            "piyushkanekar@oksbi",
            "deepalisoyane@okicici"
        ],
        "business": [
            "merchant@okicici",
            "shop.test@paytm",
            "business.demo@sbi"
        ]
    },
    "medium": {
        "suspect": [
            "cashback.offers@ybl",
            "support.helpdesk@okaxis",
            "online.deals24@paytm"
        ]
    },
    "unsafe": {
        "fraud": [
            "support@paytm",
            "rewards@ybl",
            "fraudster1@ybl",
            "fake.reward@paytm",
            "8169834706@fam",
            "bumikagowda36@oksbi",
            "darshjadhav361@okicici"
        ],
        "criminal": [
            "electricitysupport@paytm",
            "fakebillpay@sbi",
            "blacklisted.user@okicici",
            "scam.network@sbi"
        ]
    }
};

// Function to classify a UPI ID based on the local database
function classifyUPI(upiId) {
    if (!upiId) return { risk: "unknown", type: "unknown", category: "unknown" };
    upiId = upiId.toLowerCase().trim();

    if (UPIDatabase.safe.personal.includes(upiId)) return { risk: "low", type: "safe", category: "personal" };
    if (UPIDatabase.safe.business.includes(upiId)) return { risk: "low", type: "safe", category: "business" };
    
    if (UPIDatabase.medium && UPIDatabase.medium.suspect.includes(upiId)) return { risk: "medium", type: "medium", category: "suspect" };

    if (UPIDatabase.unsafe.fraud.includes(upiId)) return { risk: "high", type: "unsafe", category: "fraud" };
    if (UPIDatabase.unsafe.criminal.includes(upiId)) return { risk: "critical", type: "unsafe", category: "criminal" };

    return null; // Not found in local database
}

window.UPIDatabase = UPIDatabase;
window.classifyUPI = classifyUPI;
