import json
import re


SKILLS = [
    "React",
    "TypeScript",
    "JavaScript",
    "Next.js",
    "Vue",
    "Angular",
    "Node.js",
    "Python",
    "Django",
    "FastAPI",
    "Java",
    "C#",
    "C++",
    "PHP",
    "Laravel",
    "Ruby",
    "Ruby on Rails",
    "Go",
    "Rust",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Git",
    "GitHub",
    "Tailwind CSS",
    "Bootstrap",
    "HTML",
    "CSS",
    "Figma",
]


def extract_required_skills(text: str) -> list[str]:
    """
    Extract known technical skills from job text.
    """

    if not text:
        return []

    text_lower = text.lower()
    found_skills = []

    for skill in SKILLS:
        pattern = re.escape(skill.lower())

        if re.search(rf"(?<!\w){pattern}(?!\w)", text_lower):
            found_skills.append(skill)

    return found_skills


def extract_required_experience(text: str) -> int | None:
    """
    Extract the minimum years of experience mentioned in a job description.

    Examples:
        "2+ years of experience" -> 2
        "3 years experience" -> 3
        "minimum of 5 years" -> 5
        "at least 4 years of experience" -> 4
        "2-4 years of experience" -> 2
        "3 to 5 years of experience" -> 3
        "experience: 2 years" -> 2
    """

    if not text:
        return None

    patterns = [
        # 2+ years of experience
        r"\b(\d+)\s*\+?\s*years?\s+of\s+experience\b",

        # 2+ years experience
        r"\b(\d+)\s*\+?\s*years?\s+experience\b",

        # minimum of 5 years
        r"\bminimum\s+of\s+(\d+)\s+years?\b",

        # at least 4 years
        r"\bat\s+least\s+(\d+)\s+years?\b",

        # 2-4 years of experience -> minimum is 2
        r"\b(\d+)\s*[-–]\s*\d+\s+years?\s+of\s+experience\b",

        # 3 to 5 years of experience -> minimum is 3
        r"\b(\d+)\s+to\s+\d+\s+years?\s+of\s+experience\b",

        # experience: 2 years
        r"\bexperience\s*[:\-]\s*(\d+)\s+years?\b",

        # 2 years experience required
        r"\b(\d+)\s+years?\s+experience\s+(?:required|preferred)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_requirements(
    title: str | None,
    description: str | None,
) -> dict:
    """
    Extract structured requirements from a job.
    """

    combined_text = " ".join(
        part for part in [title, description] if part
    )

    skills = extract_required_skills(combined_text)
    experience = extract_required_experience(combined_text)

    return {
        "required_skills": json.dumps(skills),
        "required_experience": experience,
    }