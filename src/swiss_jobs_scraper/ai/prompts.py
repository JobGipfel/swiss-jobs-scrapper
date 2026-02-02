"""
LLM prompts for job processing.

Contains the system and user prompts for AI-powered job analysis.
"""

from swiss_jobs_scraper.ai.features import AIFeature

SYSTEM_PROMPT = """\
You are a professional job listing analyzer and translator \
specializing in the Swiss job market.

Your task is to analyze job listings and extract specific structured information \
based on the requested features.
"""

# Template parts for building the prompt dynamically
PROMPT_PARTS = {
    AIFeature.TRANSLATION: """
1. Translate the title and description to all 4 Swiss official languages \
(German, French, Italian) and English.
""",
    AIFeature.LANGUAGES: """
2. Extract any language requirements mentioned in the job description. \
Use ISO 639-1 code (de, fr, it, en, etc.).
""",
    AIFeature.EXPERIENCE: """
3. Determine the experience level based on the actual requirements, NOT the job title.

IMPORTANT for experience level:
- Ignore what the job is titled (e.g., "Junior Developer")
- Focus on the ACTUAL requirements mentioned (years of experience, skills expected)
- A job titled "Junior" requiring 5 years of experience is actually a SENIOR position
- Look for phrases like "X years of experience", "extensive experience", "entry-level welcome"

Experience levels:
- entry: 0 years, explicitly welcomes graduates/interns
- junior: 0-2 years experience required
- mid: 2-5 years experience required
- senior: 5-8 years experience required
- lead: 8+ years, often mentions team leadership
- principal: 10+ years, architect or principal level
""",
    AIFeature.EDUCATION: """
4. Extract the required education level. Provide a concise summary \
(e.g., "University degree", "ETH/EPFL", "Apprenticeship", "No degree required").
""",
    AIFeature.KEYWORDS: """
5. Extract semantic search keywords. Include:
- Technical skills/Technologies (e.g., Python, Docker, AWS)
- Concepts/Methodologies (e.g., Agile, CI/CD)
- Soft skills (if important)
- Domain knowledge (e.g., Banking, Pharma)
""",
}

USER_PROMPT_TEMPLATE = """Analyze this job listing and provide the requested information.

Requested Analysis:
{analysis_instructions}

Job Title: {title}

Job Description:
{description}

Original Language: {language}

Respond in this exact JSON format (only include fields relevant to requested features):
{{
{json_structure}
}}

Rules:
{rules}
"""


def get_processing_prompt(
    title: str,
    description: str,
    features: set[AIFeature],
    language: str = "en",
) -> str:
    """
    Generate the user prompt for job processing based on enabled features.

    Args:
        title: Job title
        description: Job description text
        features: Set of enabled AI features
        language: Original language of the job listing

    Returns:
        Formatted prompt string
    """
    # Build dynamic parts
    instructions = []
    json_fields = []
    rules = []

    if AIFeature.TRANSLATION in features:
        instructions.append(PROMPT_PARTS[AIFeature.TRANSLATION])
        json_fields.extend(
            [
                '    "title_de": "German title",',
                '    "title_fr": "French title",',
                '    "title_it": "Italian title",',
                '    "title_en": "English title",',
                '    "description_de": "German description",',
                '    "description_fr": "French description",',
                '    "description_it": "Italian description",',
                '    "description_en": "English description",',
            ]
        )
        rules.append("- If a language is the original, still include it")

    if AIFeature.LANGUAGES in features:
        instructions.append(PROMPT_PARTS[AIFeature.LANGUAGES])
        json_fields.append('    "required_languages": ["de", "en"],')
        rules.append("- For required_languages, use ISO 639-1 codes")

    if AIFeature.EXPERIENCE in features:
        instructions.append(PROMPT_PARTS[AIFeature.EXPERIENCE])
        json_fields.extend(
            [
                '    "experience_level": "mid",',
                '    "years_experience_min": 2,',
                '    "years_experience_max": 5,',
            ]
        )
        rules.extend(
            [
                "- experience_level must be one of: entry, junior, mid, senior, lead, principal",
                "- If no specific years mentioned, estimate from context",
                "- years_experience_min/max can be null if truly impossible to determine",
            ]
        )

    if AIFeature.EDUCATION in features:
        instructions.append(PROMPT_PARTS[AIFeature.EDUCATION])
        json_fields.append('    "education": "University degree in CS or similar",')
        rules.append("- education level should be short and normalized if possible")

    if AIFeature.KEYWORDS in features:
        instructions.append(PROMPT_PARTS[AIFeature.KEYWORDS])
        json_fields.append(
            '    "semantic_keywords": ["Python", "API", "Scraping", "Data"]'
        )
        rules.append("- semantic_keywords should be single words or short phrases")

    return USER_PROMPT_TEMPLATE.format(
        analysis_instructions="\n".join(instructions),
        title=title,
        description=description[:4000],
        language=language,
        json_structure="\n".join(json_fields),
        rules="\n".join(rules),
    )
