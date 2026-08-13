"""
Agricultural Knowledge Base for RAG semantic search.

Seeds the InMemoryStore with farming knowledge documents that the agent
can retrieve via semantic search when farmers ask knowledge questions.
"""

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Knowledge documents organized by namespace
# ---------------------------------------------------------------------------
KNOWLEDGE_DOCUMENTS = [
    # ── Disease Management ──────────────────────────────────────────────
    (("knowledge", "disease"), "late_blight_mgmt", {
        "text": "Late Blight (Phytophthora infestans) in Tomato/Potato: "
                "Symptoms include water-soaked lesions on leaves turning brown-black, "
                "white fuzzy growth on leaf undersides in humid conditions. "
                "Chemical control: Apply Mancozeb 75% WP at 2.5g/L as preventive spray "
                "every 7-10 days during humid weather. Metalaxyl+Mancozeb for curative action. "
                "Organic alternative: Bordeaux mixture (1%), copper oxychloride. "
                "Cultural practices: Avoid overhead irrigation, ensure good air circulation, "
                "remove and destroy infected plant parts. Resistant varieties: Arka Rakshak, Kashi Amrit."
    }),
    (("knowledge", "disease"), "bacterial_wilt_mgmt", {
        "text": "Bacterial Wilt (Ralstonia solanacearum) in Tomato/Brinjal/Potato: "
                "Symptoms include sudden wilting of entire plant without yellowing. "
                "Cut stem placed in water shows milky bacterial ooze. "
                "No effective chemical control exists. "
                "Management: Use resistant varieties, practice crop rotation (3-4 years), "
                "raise seedlings in disease-free soil, apply Trichoderma viride (5g/L) as soil drench, "
                "use grafted seedlings on resistant rootstock. Avoid waterlogging."
    }),
    (("knowledge", "disease"), "rice_blast_mgmt", {
        "text": "Rice Blast (Magnaporthe oryzae): Most destructive rice disease. "
                "Leaf blast: Diamond/spindle shaped spots with grey center. "
                "Neck blast: Brown-black lesions at panicle base causing grain loss. "
                "Chemical control: Tricyclazole 75% WP (0.6g/L) preventive spray, "
                "Isoprothiolane 40% EC (1.5ml/L) for curative. "
                "Organic: Pseudomonas fluorescens spray. "
                "Management: Avoid excess nitrogen, maintain proper spacing, "
                "use resistant varieties (Pusa Basmati 1, IR 64)."
    }),
    (("knowledge", "disease"), "powdery_mildew_mgmt", {
        "text": "Powdery Mildew in vegetables and pulses: "
                "White powdery coating on leaves, stems, and pods. "
                "Favoured by dry days and cool nights (20-25°C). "
                "Chemical control: Sulphur 80% WP (3g/L), Hexaconazole 5% EC (2ml/L). "
                "Organic: Neem oil spray (5ml/L), milk spray (1:9 dilution). "
                "Cultural: Proper spacing for air circulation, remove infected debris."
    }),

    # ── Crop Guides ─────────────────────────────────────────────────────
    (("knowledge", "crops"), "rice_cultivation", {
        "text": "Rice Cultivation Guide (Kharif): "
                "Nursery sowing: June (21 days before transplanting). "
                "Transplanting: July, spacing 20x15cm, 2-3 seedlings/hill. "
                "Water management: Maintain 5cm standing water during tillering, "
                "drain 10 days before harvest. "
                "Fertilizer: Basal - NPK 60:30:30 kg/ha, top dress urea at 30 and 60 days. "
                "Major pests: Stem borer, BPH, leaf folder. "
                "Harvest: When 80% grains turn golden, moisture below 20%."
    }),
    (("knowledge", "crops"), "wheat_cultivation", {
        "text": "Wheat Cultivation Guide (Rabi): "
                "Sowing time: October-November (timely) or December (late). "
                "Seed rate: 100-125 kg/ha for timely, 125-150 kg/ha for late sowing. "
                "Spacing: Row to row 20-22.5cm. "
                "Irrigation: 5-6 irrigations — Crown root (21 days), Tillering (40-45 days), "
                "Late jointing (60-65 days), Flowering (80-85 days), Milk (100-105 days), Dough (115-120 days). "
                "Fertilizer: NPK 120:60:40 kg/ha. Half N + full P&K basal, rest N in 2 splits. "
                "Varieties: HD 3226, PBW 826, DBW 187."
    }),
    (("knowledge", "crops"), "cotton_cultivation", {
        "text": "Cotton Cultivation Guide (Kharif): "
                "Sowing: April-May (irrigated), June-July (rainfed). "
                "Spacing: 90x60cm (irrigated), 60x30cm (rainfed). "
                "Seed treatment: Imidacloprid 70% WS (5g/kg seed). "
                "Fertilizer: NPK 120:60:60 kg/ha for Bt cotton. "
                "Key pests: American bollworm, whitefly, pink bollworm. "
                "Picking: Start when 60% bolls open. 3-4 pickings at 15 day intervals. "
                "Yield potential: 15-20 quintal/ha (irrigated Bt cotton)."
    }),
    (("knowledge", "crops"), "tomato_cultivation", {
        "text": "Tomato Cultivation Guide: "
                "Seasons: Rabi (main) September-October transplanting, Kharif July-August. "
                "Spacing: 60x45cm. Staking recommended for indeterminate varieties. "
                "Fertilizer: NPK 120:80:80 kg/ha + FYM 20 tonnes/ha. "
                "Key diseases: Early blight, late blight, bacterial wilt, leaf curl virus. "
                "Key pests: Fruit borer (Helicoverpa), whitefly, nematodes. "
                "Harvest: 60-80 days after transplanting. Yield: 40-50 tonnes/ha."
    }),

    # ── Government Schemes ──────────────────────────────────────────────
    (("knowledge", "schemes"), "pm_kisan", {
        "text": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi): "
                "Income support of ₹6,000 per year in 3 equal installments of ₹2,000 each. "
                "Eligibility: All land-holding farmer families. "
                "Exclusions: Institutional land holders, government employees, taxpayers. "
                "Apply at pmkisan.gov.in or through Common Service Centers (CSC). "
                "Documents: Aadhaar card, land records, bank account details."
    }),
    (("knowledge", "schemes"), "pm_fasal_bima", {
        "text": "PM Fasal Bima Yojana (Crop Insurance): "
                "Premium: Kharif 2%, Rabi 1.5%, Horticulture/Commercial 5% of sum insured. "
                "Government pays remaining premium. Covers natural calamities, pests, diseases. "
                "Apply through bank, CSC, or insurance company portal. "
                "Claim: Report crop loss within 72 hours to insurance company or toll-free number. "
                "Uses satellite and drone technology for crop assessment."
    }),
    (("knowledge", "schemes"), "soil_health_card", {
        "text": "Soil Health Card Scheme: "
                "Free soil testing and nutrient status card for every farmer. "
                "Tests 12 parameters: pH, EC, OC, N, P, K, S, Zn, Fe, Cu, Mn, B. "
                "Issued every 2 years with crop-specific fertilizer recommendations. "
                "Apply at nearest Krishi Vigyan Kendra (KVK) or agriculture office. "
                "Helps reduce fertilizer costs by 10-15% through targeted application."
    }),
    (("knowledge", "schemes"), "kisan_credit_card", {
        "text": "Kisan Credit Card (KCC): "
                "Short-term credit for crop production at 4% interest (with 3% subvention). "
                "Effective interest: 4% per annum for prompt repayment. "
                "Covers: Crop production, post-harvest, farm maintenance, allied activities. "
                "Credit limit: Based on land holding, crop pattern, and scale of finance. "
                "Apply at any commercial, cooperative, or regional rural bank. "
                "Includes personal accident insurance cover of ₹50,000."
    }),

    # ── Organic Farming ─────────────────────────────────────────────────
    (("knowledge", "organic"), "vermicompost_guide", {
        "text": "Vermicompost Preparation Guide: "
                "Materials: Cow dung, agricultural waste, earthworms (Eisenia fetida). "
                "Bed preparation: Layer of dry leaves (6 inches) + cow dung (3 inches) + "
                "kitchen/farm waste (3 inches). Add earthworms (1000/bed). "
                "Maintenance: Keep moist (40-50%), cover with jute bags, turn every 15 days. "
                "Ready in 45-60 days. Signs: Dark brown, earthy smell, granular texture. "
                "Application: 2-5 tonnes/ha. Mix with soil 2 weeks before sowing. "
                "NABARD provides subsidy for vermicompost units under RKVY."
    }),
    (("knowledge", "organic"), "neem_pesticide", {
        "text": "Neem-based Organic Pest Control: "
                "Neem oil spray: 5ml/L water + 1ml liquid soap as emulsifier. "
                "Effective against: Aphids, whitefly, thrips, leaf miner, mealybug. "
                "Neem cake: Apply 250 kg/ha as soil amendment — acts as fertilizer + pest repellent. "
                "Neem seed kernel extract (NSKE) 5%: Soak 50g neem kernel in 1L water overnight, "
                "filter and spray. Effective against bollworm, fruit borer. "
                "Spray in evening, repeat every 10-15 days. Safe for bees and natural enemies."
    }),

    # ── Irrigation & Water Management ───────────────────────────────────
    (("knowledge", "irrigation"), "drip_irrigation", {
        "text": "Drip Irrigation Guide: "
                "Water saving: 30-50% compared to flood irrigation. "
                "Yield increase: 20-40% due to precise water delivery. "
                "Components: Pump, filter, main line, sub-main, laterals, drippers. "
                "Suitable crops: Vegetables, fruits, sugarcane, cotton. "
                "Government subsidy: 55% for small/marginal farmers, 45% for others under PMKSY. "
                "Fertigation: Dissolve water-soluble fertilizers in irrigation water for "
                "30% fertilizer savings. Maintenance: Clean filters weekly, flush laterals monthly."
    }),
]


async def seed_knowledge_base(store) -> int:
    """Load all farming knowledge documents into the memory store.

    Returns:
        Number of documents loaded.
    """
    count = 0
    for namespace, key, value in KNOWLEDGE_DOCUMENTS:
        try:
            store.put(namespace, key, value)
            count += 1
        except Exception as e:
            logger.warning(f"Failed to seed knowledge doc {key}", error=str(e))

    logger.info(f"Knowledge base seeded with {count} documents")
    return count
