from ticketroute.taxonomy import SLA_HOURS, URGENCY_LABEL

TEMPLATES = {
    "en": {
        "Billing & Payments": "We received your billing request. Our payments team will review the charge and update you within {sla} hour(s). Please keep the transaction id handy.",
        "Account / KYC / Login": "Sorry you cannot access your account. We have flagged this for the identity team. Do not share OTP with anyone. Expect an update within {sla} hour(s).",
        "Technical / App crash": "Thanks for reporting the app issue. Please try force-close and update the app. Engineering will inspect crash logs. SLA {sla} hour(s).",
        "Product / Order / Delivery": "We are checking your order status with logistics. You will get a tracking update within {sla} hour(s).",
        "Abuse / Safety / Fraud": "We treat safety reports as critical. Do not make off-app payments. A specialist will contact you within {sla} hour(s).",
        "Feedback / General": "Thank you for the feedback. We logged it for the product team. No action needed from you.",
        "Other / Unknown": "We could not auto-route this with high confidence. An agent will read it within {sla} hour(s).",
    },
    "hi": {
        "Billing & Payments": "आपकी बिलिंग शिकायत दर्ज हो गई है। पेमेंट टीम {sla} घंटे में अपडेट देगी। ट्रांजैक्शन आईडी संभाल कर रखें।",
        "Account / KYC / Login": "लॉगिन समस्या के लिए खेद है। OTP किसी से साझा न करें। पहचान टीम {sla} घंटे में जवाब देगी।",
        "Technical / App crash": "ऐप समस्या दर्ज है। ऐप अपडेट करके फिर चलाएँ। इंजीनियरिंग {sla} घंटे में जाँच करेगी।",
        "Product / Order / Delivery": "आपका ऑर्डर लॉजिस्टिक्स से जाँचा जा रहा है। {sla} घंटे में ट्रैकिंग अपडेट मिलेगा।",
        "Abuse / Safety / Fraud": "सुरक्षा रिपोर्ट को प्राथमिकता दी गई है। ऐप के बाहर भुगतान न करें। {sla} घंटे में विशेषज्ञ संपर्क करेगा।",
        "Feedback / General": "आपके सुझाव के लिए धन्यवाद। उत्पाद टीम को भेज दिया गया है।",
        "Other / Unknown": "यह टिकट अपने आप रूट नहीं हो सका। एजेंट {sla} घंटे में पढ़ेगा।",
    },
    "hinglish": {
        "Billing & Payments": "Aapka billing issue register ho gaya hai. Payments team {sla} hour me update degi. Transaction id save rakhna.",
        "Account / KYC / Login": "Login problem ke liye sorry. OTP kisi ko mat dena. Identity team {sla} hour me reply karegi.",
        "Technical / App crash": "App crash report mil gayi. App update karke dubara try karo. Engineering {sla} hour me check karegi.",
        "Product / Order / Delivery": "Order status logistics se check ho raha hai. {sla} hour me tracking update milega.",
        "Abuse / Safety / Fraud": "Yeh safety report critical hai. Off-app payment mat karo. Specialist {sla} hour me contact karega.",
        "Feedback / General": "Feedback ke liye shukriya. Product team ko bhej diya hai.",
        "Other / Unknown": "Yeh ticket auto-route nahi hua. Agent {sla} hour me padhega.",
    },
}

PREFIX = {
    "en": "{urg} ({label}). Routed to {dept}.",
    "hi": "{urg} ({label})। विभाग: {dept}।",
    "hinglish": "{urg} ({label}). Department: {dept}.",
}


def draft_reply(department: str, urgency: str, language: str, ticket: str = "") -> str:
    lang = language if language in TEMPLATES else "en"
    sla = SLA_HOURS.get(urgency, 24)
    body = TEMPLATES[lang].get(department) or TEMPLATES["en"]["Feedback / General"]
    head = PREFIX[lang].format(
        urg=urgency, label=URGENCY_LABEL.get(urgency, urgency), dept=department
    )
    snippet = " ".join(str(ticket).split())[:140]
    if lang == "hi":
        extra = f" आपकी बात: “{snippet}”।" if snippet else ""
    elif lang == "hinglish":
        extra = f" Aapne likha: “{snippet}”." if snippet else ""
    else:
        extra = f" You wrote: “{snippet}”." if snippet else ""
    return f"{head} {body.format(sla=sla)}{extra}"
