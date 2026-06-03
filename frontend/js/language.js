// frontend/js/language.js

const hiMap = {
    // Dynamic Hotspot Cities & Fraud Categories
    "Delhi NCR": "दिल्ली एनसीआर",
    "Mumbai": "मुंबई",
    "Bengaluru": "बेंगलुरु",
    "Hyderabad": "हैदराबाद",
    "Kolkata": "कोलकाता",
    "Bangalore": "बेंगलुरु",
    "Delhi": "दिल्ली",
    "Typosquat Hijack": "टाइपोस्क्वाट अपहरण",
    "Collect Request Scam": "कलेक्ट अनुरोध घोटाला",
    "Lottery PIN-Trap": "लॉटरी पिन-ट्रैप",
    "Fake Fastag Portal": "नकली फास्टैग पोर्टल",
    "Urgent Utility Fraud": "तत्काल उपयोगिता धोखाधड़ी",
    "Government Refund Spoof": "सरकारी रिफंड स्पूफ़",
    "Cashback Trap": "कैशबैक जाल",
    "Electricity Collect Scam": "बिजली संग्रह घोटाला",
    "Impersonation Scam": "प्रतिरूपण घोटाला",
    "UPI Fraud Link": "यूपीआई धोखाधड़ी लिंक",
    "User Report": "उपयोगकर्ता रिपोर्ट",
    "Scanning... AI is checking fraud": "स्कैनिंग... एआई धोखाधड़ी की जांच कर रहा है",
    "Zero-Trust Inspect Active": "जीरो-ट्रस्ट निरीक्षण सक्रिय",
    "Online Threat Analyzer": "ऑनलाइन खतरा विश्लेषक",
    "SuRaksha AI Scanner": "SuRaksha एआई स्कैनर",
    "AI Command Center": "एआई कमांड सेंटर",
    "Suraj Sawant": "सूरज सावंत",
    "Lead Developer & AI Architect": "मुख्य डेवलपर और एआई आर्किटेक्ट",
    "Team Lead & Lead AI Architect": "टीम लीड और मुख्य एआई आर्किटेक्ट",
    "PROJECT LEAD": "परियोजना प्रमुख",
    "Antigravity": "एंटीग्रेविटी",
    "Autonomous Coding Agent": "स्वायत्त कोडिंग एजेंट",
    "AI Pair Programmer": "एआई जोड़ी प्रोग्रामर",
    "CORE AI SYSTEM": "मुख्य एआई सिस्टम",
    "Stitch": "स्टिच",
    "AI Collaboration Assistant": "एआई सहयोग सहायक",
    "AI Collaboration Specialist": "एआई सहयोग विशेषज्ञ",
    "SUPPORT AI": "सहायक एआई",
    "👑 Project Owner": "👑 परियोजना मालिक",
    "🤖 Core AI Agent": "🤖 मुख्य एआई एजेंट",
    "🤖 AI Assistant": "🤖 एआई सहायक",
    "Designed and developed for Hackathon 2024 by a dedicated lead developer empowered by advanced AI agents.": "उन्नत एआई एजेंटों द्वारा सशक्त एक समर्पित मुख्य डेवलपर द्वारा हैकाथॉन 2024 के लिए डिज़ाइन और विकसित किया गया।",

    // Top App Bar / Navigation
    "Home": "होम",
    "Features": "सुविधाएँ",
    "How It Works": "यह कैसे काम करता है",
    "About": "हमारे बारे में",
    "Open Scanner": "स्कैनर खोलें",
    "Scan & Analyze": "स्कैन और विश्लेषण",
    "SuRaksha": "सुरक्षा (SuRaksha)",
    // Footer & Common Links
    "Quick Links": "त्वरित लिंक",
    "About Us": "हमारे बारे में",
    "Core Features": "मुख्य विशेषताएं",
    "Security Protocol": "सुरक्षा प्रोटोकॉल",
    "Privacy Policy": "गोपनीयता नीति",
    "Building a safer digital economy for every UPI user in India.": "भारत में प्रत्येक यूपीआई उपयोगकर्ता के लिए एक सुरक्षित डिजिटल अर्थव्यवस्था का निर्माण।",
    "Go Back": "वापस जाएँ",
    "Contact Support": "सहायता से संपर्क करें",
    "SuRaksha Financial Security. All rights reserved.": "SuRaksha वित्तीय सुरक्षा। सर्वाधिकार सुरक्षित।",
    "Trusted by 50k+ Users": "50,000+ उपयोगकर्ताओं द्वारा विश्वसनीय",
    "Detect UPI Fraud Instantly — Before You Lose Money": "यूपीआई धोखाधड़ी का तुरंत पता लगाएं — पैसे खोने से पहले",
    "Scan QR codes, screenshots, and suspicious messages instantly. Our AI-driven security engine prevents unauthorized transactions before they happen.": "क्यूआर कोड, स्क्रीनशॉट और संदिग्ध संदेशों को तुरंत स्कैन करें। हमारा एआई-संचालित सुरक्षा इंजन अनधिकृत लेनदेन को होने से पहले ही रोकता है।",
    "Scan & Verify Payment": "स्कैन करें और भुगतान सत्यापित करें",
    "Learn More": "और जानें",
    "Total Scans": "कुल स्कैन",
    "Threats Blocked": "रोके गए खतरे",
    "Fraudsters Flagged": "चिह्नित धोखेबाज",
    "Community Reports": "सामुदायिक रिपोर्ट",

    // index.html How It Works
    "How SuRaksha Protects You": "SuRaksha आपकी सुरक्षा कैसे करता है",
    "Three simple steps to secure your digital payments": "आपके डिजिटल भुगतान को सुरक्षित करने के लिए तीन सरल चरण",
    "Upload Screenshot": "स्क्रीनशॉट अपलोड करें",
    "Take a screenshot of any suspicious payment request or chat and upload it for instant analysis.": "किसी भी संदिग्ध भुगतान अनुरोध या चैट का स्क्रीनशॉट लें और तत्काल विश्लेषण के लिए इसे अपलोड करें।",
    "Scan QR/Message": "क्यूआर/संदेश स्कैन करें",
    "Scan physical QR codes at shops or paste SMS alerts to identify malicious links hidden behind payment icons.": "दुकानों पर भौतिक क्यूआर कोड स्कैन करें या भुगतान आइकन के पीछे छिपे दुर्भावनापूर्ण लिंक की पहचान करने के लिए एसएमएस अलर्ट पेस्ट करें।",
    "Get Risk Alert": "जोखिम चेतावनी प्राप्त करें",
    "Our AI evaluates the risk level and gives you a clear Go/No-Go signal with detailed reasoning.": "हमारा एआई जोखिम स्तर का मूल्यांकन करता है और आपको विस्तृत तर्क के साथ एक स्पष्ट गो/नो-गो (आगे बढ़ें/न बढ़ें) संकेत देता है।",

    // index.html Features
    "Advanced Detection Suite": "उन्नत सुरक्षा सूट",
    " on next-gen security protocols": " अगले जनरेशन के सुरक्षा प्रोटोकॉल पर",
    "⚡ Real-time Analysis": "⚡ वास्तविक समय विश्लेषण",
    "🤖 AI-Powered": "🤖 एआई-संचालित",
    "Visual Intelligence": "दृश्य बुद्धिमत्ता",
    "Screenshot Fraud Detection": "स्क्रीनशॉट धोखाधड़ी का पता लगाना",
    "Identifies deceptive UI patterns in spoofed banking apps that trick you into entering your UPI PIN.": "स्पूफ़ किए गए बैंकिंग ऐप्स में भ्रामक यूआई पैटर्न की पहचान करता है जो आपको अपना यूपीआई पिन दर्ज करने के लिए धोखा देते हैं।",
    "Text Analysis": "पाठ विश्लेषण",
    "Suspicious Message Analyzer": "संदिग्ध संदेश विश्लेषक",
    "Detects urgency-based phishing messages and 'Lucky Draw' scams common on WhatsApp and SMS.": "व्हाट्सएप और एसएमएस पर आम तात्कालिकता-आधारित फ़िशिंग संदेशों और 'लकी ड्रा' घोटालों का पता लगाता है।",
    "Warning: Message contains high-pressure language typical of financial scams.": "चेतावनी: संदेश में वित्तीय घोटालों की विशिष्ट उच्च-दबाव वाली भाषा शामिल है।",
    "Safe QR Scanner": "सुरक्षित क्यूआर स्कैनर",
    "Prevents 'Collect Request' frauds by verifying QR destination before you tap pay.": "आपके द्वारा भुगतान टैप करने से पहले क्यूआर गंतव्य का सत्यापन करके 'कलेक्ट अनुरोध' धोखाधड़ी को रोकता है।",
    "Real-time Risk Score": "वास्तविक समय जोखिम स्कोर",
    "Instant 0-100 score based on global fraud databases and behavioral patterns.": "वैश्विक धोखाधड़ी डेटाबेस और व्यवहार पैटर्न के आधार पर तत्काल 0-100 स्कोर।",
    "AI Recommendation": "एआई सिफारिश",
    "Context-aware advice on whether to proceed, block, or report the transaction.": "लेनदेन को आगे बढ़ाने, ब्लॉक करने या रिपोर्ट करने के बारे में संदर्भ-जागरूक सलाह।",

    // index.html Live Demo
    "See It in Action": "इसे एक्शन में देखें",
    "Our scanning engine works in milliseconds. Whether it's a fake reward or a masked payment link, we catch it before your money leaves your account.": "हमारा स्कैनिंग इंजन मिलीसेकंड में काम करता है। चाहे वह नकली इनाम हो या छुपा हुआ भुगतान लिंक, हम आपके खाते से पैसे निकलने से पहले ही उसे पकड़ लेते हैं।",
    "High Risk: Spoofed Payment Gateway": "उच्च जोखिम: स्पूफ़ किया गया भुगतान गेटवे",
    "Medium Risk: Unverified Merchant Account": "मध्यम जोखिम: असत्यापित व्यापारी खाता",
    "Low Risk: Verified Institutional Vendor": "कम जोखिम: सत्यापित संस्थागत विक्रेता",
    "⚠️ Suspicious UPI Request": "⚠️ संदिग्ध यूपीआई अनुरोध",
    "This payment link points to a blacklisted account reported for 'Lottery Scam' multiple times.": "यह भुगतान लिंक एक ब्लैकलिस्ट किए गए खाते की ओर इशारा करता है जिसे कई बार 'लॉटरी घोटाले' के लिए रिपोर्ट किया गया है।",
    "Recommendation:": "सिफारिश:",
    "Do not enter your PIN. Report this number immediately.": "अपना पिन दर्ज न करें। इस नंबर की तुरंत रिपोर्ट करें।",
    "Report Fraud": "धोखाधड़ी की रिपोर्ट करें",
    "Close Scanner": "स्कैनर बंद करें",
    "AI Confidence (Demo)": "एआई आत्मविश्वास (डेमो)",
    "Database Match Found": "डेटाबेस मिलान मिला",

    // index.html Multi-Input
    "Start Your Safety Scan": "अपनी सुरक्षा स्कैन शुरू करें",
    "Choose your input method to verify a request": "अनुरोध को सत्यापित करने के लिए अपनी इनपुट विधि चुनें",
    "Gallery images or chat screenshots": "गैलरी चित्र या चैट स्क्रीनशॉट",
    "Paste Message": "संदेश पेस्ट करें",
    "SMS alerts or suspicious WhatsApp text": "एसएमएस अलर्ट या संदिग्ध व्हाट्सएप संदेश",
    "Scan QR Code": "क्यूआर कोड स्कैन करें",
    "Real-time scan with your camera": "अपने कैमरे के साथ वास्तविक समय में स्कैन",

    // index.html Comparison
    "Why Choose SuRaksha?": "SuRaksha क्यों चुनें?",
    "Feature": "सुविधा",
    "SuRaksha AI": "SuRaksha एआई",
    "Standard Apps": "मानक ऐप्स",
    "Real-time Alerts": "वास्तविक समय अलर्ट",
    "AI Behavioral Analysis": "एआई व्यवहार विश्लेषण",
    "Global Fraud Database": "वैश्विक धोखाधड़ी डेटाबेस",

    // index.html Trust & Privacy
    "Your Privacy is Our Priority": "आपकी गोपनीयता हमारी प्राथमिकता है",
    "We believe security shouldn't come at the cost of privacy. SuRaksha uses on-device edge processing and volatile memory scanning.": "हमारा मानना ​​है कि गोपनीयता की कीमत पर सुरक्षा नहीं मिलनी चाहिए। SuRaksha ऑन-डिवाइस एज प्रोसेसिंग और वोलाटाइल मेमोरी स्कैनिंग का उपयोग करता है।",
    "Data Not Stored": "डेटा संग्रहीत नहीं किया जाता",
    "Scans are deleted after processing.": "स्कैन प्रोसेसिंग के बाद हटा दिए जाते हैं।",
    "Secure Scanning": "सुरक्षित स्कैनिंग",
    "256-bit SSL for cloud analysis.": "क्लाउड विश्लेषण के लिए 256-बिट एसएसएल।",

    // index.html Testimonials
    "What Our Users Say": "हमारे उपयोगकर्ता क्या कहते हैं",
    "\"I almost clicked on a 'Free Rewards' link. SuRaksha caught it immediately. Saved me from a ₹5000 fraud!\"": "\"मैं लगभग एक 'फ्री रिवॉर्ड्स' लिंक पर क्लिक करने ही वाला था। SuRaksha ने इसे तुरंत पकड़ लिया। मुझे ₹5000 की धोखाधड़ी से बचा लिया!\"",
    "Rahul M.": "राहुल एम.",
    "Bangalore": "बेंगलुरु",
    "\"The screenshot scanning is a game changer. Now I check every QR before paying at new shops.\"": "\"स्क्रीनशॉट स्कैनिंग एक गेम चेंजर है। अब मैं नई दुकानों पर भुगतान करने से पहले हर क्यूआर की जांच करती हूं।\"",
    "Priya S.": "प्रिया एस.",
    "Mumbai": "मुंबई",
    "\"Simple, fast, and reliable. A must-have app for anyone using UPI regularly in India.\"": "\"सरल, तेज और विश्वसनीय। भारत में नियमित रूप से यूपीआई का उपयोग करने वाले किसी भी व्यक्ति के लिए एक अनिवार्य ऐप।\"",
    "Amit K.": "अमित के.",
    "Delhi": "दिल्ली",

    // index.html Final CTA
    "Start detecting fraud before it happens": "धोखाधड़ी होने से पहले ही उसका पता लगाना शुरू करें",
    "Join thousands of users who trust SuRaksha for their daily UPI safety. Get instant peace of mind today.": "उन हजारों उपयोगकर्ताओं से जुड़ें जो अपनी दैनिक यूपीआई सुरक्षा के लिए SuRaksha पर भरोसा करते हैं। आज ही त्वरित मानसिक शांति प्राप्त करें।",
    "Scan Now": "अभी स्कैन करें",
    "View Documentation": "दस्तावेज़ देखें",

    // scan.html & test.html General Layout
    "Choose Scan Method": "स्कैन विधि चुनें",
    "Select how you want to verify the transaction": "चुनें कि आप लेनदेन को कैसे सत्यापित करना चाहते हैं",
    "QR Scanner": "क्यूआर स्कैनर",
    "UPI ID Check": "यूपीआई आईडी जांच",
    "Screenshot AI": "स्क्रीनशॉट एआई",
    "Message Scanner": "संदेश स्कैनर",
    "🔒 Secure QR Gen": "🔒 सुरक्षित क्यूआर जनरेटर",
    "🗺️ Live SOC Map": "🗺️ लाइव एसओसी मैप",
    "Unique Fraudsters": "अद्वितीय धोखेबाज",

    // scan.html & test.html Section A: Pay/Receive Card
    "Send Money (Pay)": "पैसे भेजें (भुगतान)",
    "You are paying someone. Use this to verify the destination UPI ID and ensure the QR code hasn't been tampered with.": "आप किसी को भुगतान कर रहे हैं। गंतव्य यूपीआई आईडी को सत्यापित करने और यह सुनिश्चित करने के लिए इसका उपयोग करें कि क्यूआर कोड के साथ छेड़छाड़ नहीं की गई है।",
    "Receive Money": "पैसे प्राप्त करें",
    "Someone is sending you money. View your secure QR code or verify a payment proof screenshot sent by a sender.": "कोई आपको पैसे भेज रहा। अपना सुरक्षित क्यूआर कोड देखें या प्रेषक द्वारा भेजे गए भुगतान प्रमाण स्क्रीनशॉट को सत्यापित करें।",

    // scan.html & test.html Section B: Forms & Inputs
    "Verify Destination VPA": "गंतव्य वीपीए सत्यापित करें",
    "Verify standard UPI ID handles against our intelligence registries instantly.": "बुद्धिमत्ता रजिस्ट्रियों के खिलाफ मानक यूपीआई आईडी हैंडल को तुरंत सत्यापित करें।",
    "Enter UPI VPA": "यूपीआई वीपीए दर्ज करें",
    "Verify VPA": "वीपीए सत्यापित करें",
    "Upload Transaction Screenshot": "लेनदेन स्क्रीनशॉट अपलोड करें",
    "Upload transaction receipts to run optical heuristics and metadata checks.": "ऑप्टिकल हेरिस्टिक्स और मेटाडेटा जांच चलाने के लिए लेनदेन रसीदें अपलोड करें।",
    "Upload Screenshot": "स्क्रीनशॉट अपलोड करें",
    "Phishing Chat Scanner": "फ़िशिंग चैट स्कैनर",
    "Paste SMS or WhatsApp notifications to check linguistic urgency alerts.": "भाषाई तात्कालिकता अलर्ट की जांच करने के लिए एसएमएस या व्हाट्सएप सूचनाएं पेस्ट करें।",
    "Scan Message": "संदेश स्कैन करें",
    "Type or paste suspicious message...": "संदेहास्पद संदेश टाइप करें या पेस्ट करें...",

    // scan.html Section C: Secure QR Gen
    "Cryptographic Secure QR Generator": "क्रिप्टोग्राफिक सुरक्षित क्यूआर जनरेटर",
    "Create Secure Store QR": "सुरक्षित स्टोर क्यूआर बनाएं",
    "Generate Secure QR Code": "सुरक्षित क्यूआर कोड बनाएं",
    "Download Store Trust Certificate": "स्टोर ट्रस्ट प्रमाणपत्र डाउनलोड करें",
    "Merchant/Store Name": "व्यापारी/स्टोर का नाम",
    "Merchant UPI VPA": "व्यापारी यूपीआई वीपीए",
    "Cryptographic Secret Key": "क्रिप्टोग्राफिक गुप्त कुंजी",
    "Awaiting Generation": "पीढ़ी की प्रतीक्षा में",
    "Enter your merchant details and secret key on the left to output a cryptographically secured QR code.": "क्रिप्टोग्राफ़िक रूप से सुरक्षित क्यूआर कोड आउटपुट करने के लिए बाईं ओर अपने व्यापारी विवरण और गुप्त कुंजी दर्ज करें।",

    // scan.html Section D: SOC threat map
    "Cyber Security Operations Center (SOC)": "साइबर सुरक्षा संचालन केंद्र (SOC)",
    "Live Geolocation Threat Ticker (India)": "लाइव जियोलोकेशन थ्रेट टिकर (भारत)",
    "Live Incident Feed": "लाइव घटना फ़ीड",
    "Telemetry Stream: Incoming Alerts": "टेलीमेट्री स्ट्रीम: आने वाले अलर्ट",
    "System startup. Telemetry synchronized.": "सिस्टम स्टार्टअप। टेलीमेट्री सिंक्रनाइज़।",

    // scan.html Section E: Sandbox Simulator
    "Zero-Trust Threat Simulator": "जीरो-ट्रस्ट थ्रेट सिम्युलेटर",
    "Select Live Attack Vector": "लाइव आक्रमण वेक्टर चुनें",
    "Click a real-world scenario to launch a step-by-step simulated interactive attack within the sandbox.": "सैंडबॉक्स के भीतर चरण-दर-चरण सिम्युलेटेड इंटरैक्टिव हमले को शुरू करने के लिए एक वास्तविक दुनिया परिदृश्य पर क्लिक करें।",
    "1. Utility Collect Bill Fraud": "1. उपयोगिता बिल संग्रह धोखाधड़ी",
    "High urgency collect request mimicking electricity board": "बिजली बोर्ड की नकल करते हुए उच्च तात्कालिकता संग्रह अनुरोध",
    "2. Typosquatted VPA Spoof": "2. टाइपोस्क्वाट वीपीए स्पूप",
    "Misspelled shop VPA handle hijack in printed QR code": "मुद्रित क्यूआर कोड में गलत वर्तनी वाले दुकान वीपीए हैंडल का अपहरण",
    "3. Cashback PIN-Trap Trap": "3. कैशबैक PIN-ट्रैप जाल",
    "Scam notification requesting UPI PIN to 'receive' money": "पैसे 'प्राप्त' करने के लिए यूपीआई पिन का अनुरोध करने वाली घोटाला सूचना",
    "Sandbox Ticker Logging": "सैंडबॉक्स टिकर लॉगिंग",
    "Reset": "रीसेट",
    "Inspect Payload": "पेलोड का निरीक्षण करें",

    // scan.html & test.html Section F: Stay Safe Cards
    "Learn & Stay Safe": "सीखें और सुरक्षित रहें",
    "Learn &amp; Stay Safe": "सीखें और सुरक्षित रहें",
    "Never share OTP": "ओटीपी कभी साझा न करें",
    "SuRaksha or any bank will never ask for your OTP. Sharing it gives scammers full access to your funds.": "SuRaksha या कोई भी बैंक कभी भी आपसे ओटीपी नहीं मांगेगा। इसे साझा करने से घोटालेबाजों को आपके फंड तक पूरी पहुंच मिल जाती है।",
    "Collect Request Scams": "कलेक्ट रिक्वेस्ट घोटाले",
    "Entering your PIN always means money is LEAVING your account. No PIN is needed to receive money.": "अपना पिन दर्ज करने का हमेशा मतलब होता है कि आपके खाते से पैसे निकल रहे हैं। पैसे प्राप्त करने के लिए किसी पिन की आवश्यकता नहीं है।",
    "Fake reward scams": "फर्जी इनाम घोटाले",
    "Be wary of 'You Won' messages. These often lead to phishing sites designed to steal your credentials.": "जीत गए' संदेशों से सावधान रहें। ये अक्सर आपकी साख चुराने के लिए डिज़ाइन की गई फ़िशिंग साइटों की ओर ले जाते हैं।",

    // Buttons and actions inside popups
    "Proceed to Pay": "भुगतान करने के लिए आगे बढ़ें",
    "Report Fraud": "धोखाधड़ी की रिपोर्ट करें",
    "Acknowledge & Close": "स्वीकार करें और बंद करें",
    "Acknowledge &amp; Close": "स्वीकार करें और बंद करें",
    "Dismiss": "खारिज करें",
    "Print Certificate": "प्रमाणपत्र प्रिंट करें",
    "AI ML Classification Distribution": "एआई एमएल वर्गीकरण वितरण",
    "Threat Indicators & Signals": "खतरे के संकेतक और संकेत",
    "Fraud Type:": "धोखाधड़ी का प्रकार:",
    "Recommendation:": "सिफारिश:",

    // Dynamic placeholders
    "e.g. Sharma Kirana Store": "जैसे: शर्मा किराना स्टोर",
    "e.g. sharmakirana@upi": "जैसे: sharmakirana@upi",
    "e.g. user@upi": "जैसे: user@upi",

    // result.html Specific
    "FRAUD ALERT": "धोखाधड़ी की चेतावनी",
    "High Risk": "उच्च जोखिम",
    "Low Risk": "कम जोखिम",
    "Moderate Risk": "मध्यम जोखिम",
    "Threat probability analyzed in real-time.": "वास्तविक समय में खतरे की संभावना का विश्लेषण किया गया।",
    "Fraud Type": "धोखाधड़ी का प्रकार",
    "Confidence": "विश्वास",
    "Detected Action": "डिटेक्ट की गई क्रिया",
    "Why this is risky": "यह जोखिम भरा क्यों है",
    "Suspicious keywords detected": "संदिग्ध कीवर्ड पाए गए",
    "Intent mismatch": "इरादा बेमेल (Intent mismatch)",
    "Unknown UPI pattern": "अज्ञात यूपीआई पैटर्न",
    "Safe to Pay: NO": "भुगतान करना सुरक्षित: नहीं",
    "Safe to Pay: YES": "भुगतान करना सुरक्षित: हाँ",
    "Do NOT proceed with this payment. Report this number immediately.": "इस भुगतान के साथ आगे न बढ़ें। इस नंबर की तुरंत रिपोर्ट करें।",
    "Scan Again": "फिर से स्कैन करें",

    // test.html Specific
    "Advanced cybersecurity protection for your financial transactions. Verify QR codes, payment proofs, and suspicious messages instantly.": "आपके वित्तीय लेनदेन के लिए उन्नत साइबर सुरक्षा सुरक्षा। क्यूआर कोड, भुगतान प्रमाण और संदिग्ध संदेशों को तुरंत सत्यापित करें।",

    // about.html Specific
    "About SuRaksha": "SuRaksha के बारे में",
    "Building a safer digital payment ecosystem by preventing UPI fraud in real-time.": "वास्तविक समय में यूपीआई धोखाधड़ी को रोककर एक सुरक्षित डिजिटल भुगतान पारिस्थितिकी तंत्र का निर्माण करना।",
    "Try SuRaksha AI Instantly": "SuRaksha AI का तुरंत परीक्षण करें",
    "Paste a suspicious payment message and test our AI fraud detector.": "एक संदिग्ध भुगतान संदेश पेस्ट करें और हमारे AI धोखाधड़ी डिटेक्टर का परीक्षण करें।",
    "Our Solution": "हमारा समाधान",
    "AI-Powered Analysis": "एआई-संचालित विश्लेषण",
    "Powerful Protection Features": "शक्तिशाली सुरक्षा विशेषताएं",
    "Why SuRaksha Matters": "SuRaksha क्यों महत्वपूर्ण है",
    "Preventing Financial Loss": "वित्तीय नुकसान को रोकना",
    "Building Digital Trust": "डिजिटल विश्वास का निर्माण",
    "The Team": "हमारी टीम",
    "Screenshot Detection": "स्क्रीनशॉट डिटेक्शन",
    "Message Analysis": "संदेश विश्लेषण",
    "Risk Score": "जोखिम स्कोर",

    // features.html Specific
    "Advanced Protection Suite": "उन्नत सुरक्षा सूट",
    "Powerful Fraud Detection Features": "शक्तिशाली धोखाधड़ी जांच सुविधाएं",
    "Advanced AI tools to protect your UPI transactions in real time with the industry's most sophisticated security layer.": "उद्योग की सबसे परिष्कृत सुरक्षा परत के साथ वास्तविक समय में आपके यूपीआई लेनदेन की सुरक्षा के लिए उन्नत एआई उपकरण।",
    "Screenshot Fraud Detection": "स्क्रीनशॉट धोखाधड़ी का पता लगाना",
    "QR Code Scanner": "क्यूआर कोड स्कैनर",
    "Message Analyzer": "संदेश विश्लेषक",
    "Real-Time Risk Score": "वास्तविक समय जोखिम स्कोर",
    "Smart Suggestions": "स्मार्ट सुझाव",
    "Multi-Input Support": "बहु-इनपुट समर्थन",
    "AI-Powered Detection Engine": "एआई-संचालित पहचान इंजन",
    "AI Screenshot Verification": "एआई स्क्रीनशॉट सत्यापन"
};

class NaiveLanguageTranslator {
    constructor() {
        this.currentLang = localStorage.getItem("suraksha_lang") || "en";
        this.observer = null;
    }

    init() {
        this.setupToggleButton();
        this.applyLanguage(this.currentLang);
        this.setupMutationObserver();
    }

    setupToggleButton() {
        const langBtn = document.getElementById("language-toggle");
        if (!langBtn) return;

        // Synchronize initial text label
        const label = document.getElementById("lang-label");
        if (label) label.innerText = this.currentLang.toUpperCase();

        if (langBtn._hasListener) return;
        langBtn._hasListener = true;

        langBtn.addEventListener("click", () => {
            // Apply micro-animation: rotate the globe icon on click
            const icon = langBtn.querySelector(".material-symbols-outlined");
            if (icon) {
                icon.style.transform = "rotate(360deg)";
                icon.style.transition = "transform 0.6s ease";
                setTimeout(() => {
                    icon.style.transform = "none";
                    icon.style.transition = "none";
                }, 600);
            }

            this.toggleLanguage();
        });
    }

    toggleLanguage() {
        this.currentLang = this.currentLang === "en" ? "hi" : "en";
        localStorage.setItem("suraksha_lang", this.currentLang);
        
        const label = document.getElementById("lang-label");
        if (label) label.innerText = this.currentLang.toUpperCase();

        // Disconnect observer briefly to prevent infinite loops during full-page translate
        if (this.observer) this.observer.disconnect();

        this.applyLanguage(this.currentLang);

        // Reconnect observer
        this.setupMutationObserver();
        
        if (typeof showToast === "function") {
            const msg = this.currentLang === "en" ? "Language switched to English 🇬🇧" : "भाषा बदलकर हिंदी की गई 🇮🇳";
            showToast(msg, "success", 2000);
        }
    }

    applyLanguage(lang) {
        // Recursive leaf translation
        this.translateElement(document.body, lang);
        
        // Translate placeholders
        this.translatePlaceholders(lang);
    }

    translateDynamicText(text, lang) {
        if (!text) return text;
        
        let result = text;
        if (lang === "hi") {
            // Exact key matching first
            if (hiMap[text]) return hiMap[text];
            
            // Regexes for telemetry logs
            const locRegex = /^Location:\s*(.*)$/i;
            if (locRegex.test(result)) {
                const city = result.match(locRegex)[1].trim();
                const translatedCity = hiMap[city] || city;
                return `स्थान: ${translatedCity}`;
            }
            
            const riskRegex = /^Risk:\s*(\d+%.*)$/i;
            if (riskRegex.test(result)) {
                const val = result.match(riskRegex)[1];
                return `जोखिम: ${val}`;
            }

            const vpaRegex = /^VPA:\s*(.*)$/i;
            if (vpaRegex.test(result)) {
                const addr = result.match(vpaRegex)[1];
                return `वीपीए: ${addr}`;
            }

            // Substring translations for composite messages
            for (let key in hiMap) {
                if (key.length > 3 && result.includes(key)) {
                    result = result.replace(new RegExp(key, 'g'), hiMap[key]);
                }
            }

            // Common word replacements
            result = result.replace(/Blocked/gi, "रोका गया");
            result = result.replace(/Verified/gi, "सत्यापित");
            result = result.replace(/Risk Score/gi, "जोखिम स्कोर");
            result = result.replace(/Confidence/gi, "विश्वास");
        }
        return result;
    }

    translateElement(node, lang) {
        if (node.nodeType === Node.TEXT_NODE) {
            const rawText = node.nodeValue;
            const text = rawText.trim();
            if (!text) return;

            // If currently translating, skip to prevent infinite loops
            if (node._isTranslating) return;

            // Cache original English text in custom DOM node property
            if (node._originalText === undefined) {
                node._originalText = text;
            }

            const original = node._originalText;

            if (lang === "hi") {
                const translated = this.translateDynamicText(original, "hi");
                if (text !== translated) {
                    node._isTranslating = true;
                    node.nodeValue = rawText.replace(text, translated);
                    node._isTranslating = false;
                }
            } else {
                if (text !== original) {
                    node._isTranslating = true;
                    node.nodeValue = rawText.replace(text, original);
                    node._isTranslating = false;
                }
            }
        } else {
            // Do not translate scripting, style sheets, or icons
            if (["SCRIPT", "STYLE", "NOSCRIPT"].includes(node.tagName)) return;
            
            // Handle Google Font symbols explicitly so they do not get converted
            if (node.classList && node.classList.contains("material-symbols-outlined")) return;

            // Avoid translating language-toggle button contents directly
            if (node.id === "language-toggle" || node.id === "lang-label") return;

            for (let child of node.childNodes) {
                this.translateElement(child, lang);
            }
        }
    }

    translatePlaceholders(lang) {
        const inputs = document.querySelectorAll("input, textarea");
        inputs.forEach(input => {
            if (!input.placeholder) return;
            if (input._originalPlaceholder === undefined) {
                input._originalPlaceholder = input.placeholder;
            }
            const original = input._originalPlaceholder;
            if (lang === "hi") {
                if (hiMap[original] && input.placeholder !== hiMap[original]) {
                    input.placeholder = hiMap[original];
                }
            } else {
                if (input.placeholder !== original) {
                    input.placeholder = original;
                }
            }
        });
    }

    setupMutationObserver() {
        if (this.currentLang === "en") return; // No need to observe if active language is English

        this.observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === "childList") {
                    mutation.addedNodes.forEach(node => {
                        this.translateElement(node, this.currentLang);
                    });
                } else if (mutation.type === "characterData") {
                    this.translateElement(mutation.target, this.currentLang);
                }
            });
        });

        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }
}

// Instantiate and initialize on DOM load
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        const translator = new NaiveLanguageTranslator();
        translator.init();
    });
} else {
    const translator = new NaiveLanguageTranslator();
    translator.init();
}
