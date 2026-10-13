from typing import Dict

from services.scraping.src.base_model.job_offer import JobURL


def get_scrapers_config() -> Dict[str, dict]:
    """Return scrapers configuration."""
    return {
        "1": {
            "name": "Business France (VIE)",
            "url": JobURL.BUSINESS_FRANCE,
            "description": "VIE offers from Business France portal",
            "enabled": True,
            "category": "VIE",
        },
        "2": {
            "name": "Air France",
            "url": JobURL.AIR_FRANCE,
            "description": "Job offers from Air France careers page",
            "enabled": True,
            "category": "CDI",
            "keyword": "data",
            "contract_type": "CDI",
        },
        "3": {
            "name": "Apple",
            "url": JobURL.APPLE,
            "description": "Job offers from Apple careers (France focus)",
            "enabled": True,
            "category": "CDI",
        },
        "4": {
            "name": "Welcome to the Jungle (Data Engineer)",
            "url": JobURL.WELCOME_TO_THE_JUNGLE,
            "description": "Data Engineer positions from WTTJ",
            "enabled": True,
            "keyword": "data engineer",
            "location": "Paris",
            "category": "CDI",
        },
        "5": {
            "name": "Welcome to the Jungle (AI)",
            "url": JobURL.WELCOME_TO_THE_JUNGLE,
            "description": "AI positions from WTTJ",
            "enabled": True,
            "keyword": "artificial intelligence",
            "location": "Paris",
            "category": "CDI",
        },
        "6": {
            "name": "LinkedIn (Data Engineer)",
            "url": JobURL.LINKEDIN,
            "description": "Data Engineer positions from LinkedIn (Paris et périphérie)",
            "enabled": True,
            "keyword": "data engineer",
            "location": "Paris et périphérie",
            "category": "CDI",
        },
        "7": {
            "name": "LinkedIn (Data science)",
            "url": JobURL.LINKEDIN,
            "description": "Data science positions from LinkedIn (Paris et périphérie)",
            "enabled": True,
            "keyword": "data science",
            "location": "Paris et périphérie",
            "category": "CDI",
        },
    }


def get_default_filters() -> tuple:
    """Get default include and exclude filters."""
    default_include = [
        "data engineer",
        "data analyst",
        "data scientist",
        "data science",
        "machine learning",
        "artificial intelligence",
        "big data",
        "science",
        "GCP",
        "Data platform",
        "Cloud Database",
        "deep learning",
        "software",
        "developer",
        "neural networks",
        "computer vision",
        "vision",
        "data mining",
        "predictive modeling",
        "language processing",
        "mlops",
        "llm",
        "generative",
        "nlp",
        "reinforcement learning",
        "forward deployed",
        "forward-deployed",
        "operational research",
        "operations research",
        "recherche opérationnelle",
        "optimization",
        "optimisation",
    ]

    default_exclude = [
        "stage",
        "stages",
        "stagiaire",
        "stagiaires",
        "intern",
        "interns",
        "internship",
        "internships",
        "apprenti",
        "apprentissage",
        "apprentice",
        "apprenticeship",
        "alternance",
        "alternant",
        "alternants",
        "business developer",
        "développeur commercial",
    ]

    return default_include, default_exclude
