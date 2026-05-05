"""
Story content — Hindi narrations, subtitles, and scene metadata.
"""

STORY_TITLE_HINDI = "रामलाल की कहानी"
STORY_TITLE_ENGLISH = "Ramlal's Story"
STORY_TAGLINE = "मेहनत · ईमानदारी · हिम्मत"

# Ordered list of scenes
SCENES = [
    {
        "id": "title",
        "narration_hindi": "",
        "narration_english": "",
        "subtitle_hindi": "रामलाल की कहानी",
        "subtitle_english": "The Story of Ramlal",
    },
    {
        "id": "village_intro",
        "narration_hindi": (
            "एक छोटे से गाँव में रामलाल नाम का एक किसान रहता था।"
        ),
        "narration_english": (
            "In a small village, there lived a farmer named Ramlal."
        ),
        "subtitle_hindi": "एक छोटे से गाँव में रामलाल नाम का एक किसान रहता था।",
        "subtitle_english": "In a small village lived a farmer named Ramlal.",
    },
    {
        "id": "ramlal_working",
        "narration_hindi": (
            "उसके पास ज़्यादा जमीन नहीं थी, लेकिन वह बहुत मेहनती और ईमानदार था। "
            "हर दिन वह सुबह जल्दी उठकर अपने खेत में काम करने जाता।"
        ),
        "narration_english": (
            "He didn't have much land, but he was very hardworking and honest. "
            "Every day he rose early and went to work in his fields."
        ),
        "subtitle_hindi": "मेहनती और ईमानदार — हर दिन सुबह खेत में",
        "subtitle_english": "Hardworking and honest — in the fields every dawn",
    },
    {
        "id": "drought",
        "narration_hindi": (
            "एक साल बारिश बहुत कम हुई। "
            "गाँव के कई किसान परेशान हो गए और कुछ ने तो खेती करना ही छोड़ दिया।"
        ),
        "narration_english": (
            "One year, there was very little rain. "
            "Many farmers grew worried and some even abandoned their fields."
        ),
        "subtitle_hindi": "एक साल बारिश बहुत कम हुई …",
        "subtitle_english": "One year, very little rain fell …",
    },
    {
        "id": "ramlal_determined",
        "narration_hindi": "लेकिन रामलाल ने हार नहीं मानी।",
        "narration_english": "But Ramlal did not give up.",
        "subtitle_hindi": "लेकिन रामलाल ने हार नहीं मानी।",
        "subtitle_english": "But Ramlal did not give up.",
    },
    {
        "id": "new_techniques",
        "narration_hindi": (
            "उसने अपने खेत में पानी बचाने के नए तरीके अपनाए, "
            "जैसे छोटे-छोटे गड्ढे बनाना और कम पानी वाली फसल उगाना।"
        ),
        "narration_english": (
            "He adopted new water-saving techniques — "
            "digging small ponds and growing drought-resistant crops."
        ),
        "subtitle_hindi": "पानी बचाने के नए तरीके अपनाए",
        "subtitle_english": "He adopted new water-saving techniques",
    },
    {
        "id": "green_contrast",
        "narration_hindi": (
            "धीरे-धीरे उसकी मेहनत रंग लाई। "
            "जहाँ बाकी खेत सूख रहे थे, वहीं रामलाल के खेत में हरियाली थी।"
        ),
        "narration_english": (
            "Gradually his hard work bore fruit. "
            "While other fields dried up, Ramlal's field stayed green."
        ),
        "subtitle_hindi": "उसके खेत में हरियाली — बाकी खेत सूखे",
        "subtitle_english": "His field stayed green while others dried up",
    },
    {
        "id": "harvest",
        "narration_hindi": (
            "उसकी फसल अच्छी हुई और उसे अच्छा मुनाफा भी मिला।"
        ),
        "narration_english": (
            "His crop was good and he earned a handsome profit."
        ),
        "subtitle_hindi": "फसल अच्छी हुई — मुनाफा भी मिला",
        "subtitle_english": "A bountiful harvest and a good profit",
    },
    {
        "id": "villagers_learning",
        "narration_hindi": "गाँव के लोग उससे सीखने लगे।",
        "narration_english": "The villagers began to learn from him.",
        "subtitle_hindi": "गाँव के लोग उससे सीखने लगे",
        "subtitle_english": "The village began to learn from Ramlal",
    },
    {
        "id": "moral",
        "narration_hindi": (
            "मुश्किल समय में हार नहीं माननी चाहिए, "
            "बल्कि समझदारी और मेहनत से काम लेना चाहिए।"
        ),
        "narration_english": (
            "In difficult times one should not give up — "
            "use wisdom and hard work instead."
        ),
        "subtitle_hindi": "मुश्किल में समझदारी और मेहनत से काम लो",
        "subtitle_english": "Meet hardship with wisdom and hard work",
    },
    {
        "id": "end_card",
        "narration_hindi": "",
        "narration_english": "",
        "subtitle_hindi": "समाप्त",
        "subtitle_english": "— The End —",
    },
]

# Full Hindi narration text (used for single-audio-track mode)
FULL_NARRATION_HINDI = (
    "एक छोटे से गाँव में रामलाल नाम का एक किसान रहता था। "
    "उसके पास ज़्यादा जमीन नहीं थी, लेकिन वह बहुत मेहनती और ईमानदार था। "
    "हर दिन वह सुबह जल्दी उठकर अपने खेत में काम करने जाता और पूरे मन से खेती करता। "
    "एक साल बारिश बहुत कम हुई। "
    "गाँव के कई किसान परेशान हो गए और कुछ ने तो खेती करना ही छोड़ दिया। "
    "लेकिन रामलाल ने हार नहीं मानी। "
    "उसने अपने खेत में पानी बचाने के नए तरीके अपनाए, "
    "जैसे छोटे-छोटे गड्ढे बनाना और कम पानी वाली फसल उगाना। "
    "धीरे-धीरे उसकी मेहनत रंग लाई। "
    "जहाँ बाकी खेत सूख रहे थे, वहीं रामलाल के खेत में हरियाली थी। "
    "उसकी फसल अच्छी हुई और उसे अच्छा मुनाफा भी मिला। "
    "गाँव के लोग उससे सीखने लगे कि मुश्किल समय में हार नहीं माननी चाहिए, "
    "बल्कि समझदारी और मेहनत से काम लेना चाहिए।"
)
