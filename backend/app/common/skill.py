from app.common.enums import SkillLevel
from app.config import get_settings


def default_score_for(level: SkillLevel) -> float:
    """Default skill_score for a given skill_level (business-requirements.md #10-11).

    Callers may still override the resulting score explicitly (Admin override,
    BR-09 unknown-skill fallback).
    """
    settings = get_settings()
    mapping = {
        SkillLevel.GIOI: settings.skill_score_gioi,
        SkillLevel.TRUNG_BINH: settings.skill_score_trung_binh,
        SkillLevel.YEU: settings.skill_score_yeu,
        SkillLevel.UNKNOWN: settings.skill_score_unknown,
    }
    return mapping[level]
