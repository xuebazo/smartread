"""
难度评级 Agent — 综合词汇复杂度 + AI 分类判断文章难度等级
"""
import re
from config import get_api_key
from services.ai_service import AIService

# 四六级词汇复杂度基准（参考 COCA 词频）
CET4_WORDS = {
    "analysis", "approach", "benefit", "challenge", "community",
    "consequence", "contribute", "decade", "demonstrate", "economic",
    "environment", "establish", "evidence", "factor", "function",
    "global", "identify", "impact", "indicate", "individual",
    "involve", "issue", "method", "obtain", "occur",
    "percent", "policy", "principle", "process", "require",
    "research", "resource", "response", "role", "section",
    "significant", "similar", "source", "specific", "strategy",
    "structure", "theory", "tradition", "various",
}

CET6_WORDS = {
    "abandon", "abstract", "academy", "accommodate", "accompany",
    "accomplish", "acknowledge", "acquire", "adequate", "advocate",
    "aggressive", "alternative", "ambiguous", "ambitious", "anticipate",
    "appreciate", "approach", "appropriate", "approximate", "arbitrary",
    "aspect", "assemble", "assess", "assign", "associate",
    "assume", "atmosphere", "attribute", "authority", "available",
    "aware", "behalf", "benefit", "bias", "bond",
    "brief", "capable", "capacity", "category", "cease",
    "challenge", "channel", "chapter", "chart", "circumstance",
    "cite", "civil", "clarify", "classic", "clause",
    "code", "cognitive", "coherent", "coincide", "collapse",
    "colleague", "commence", "comment", "commission", "commit",
    "communicate", "community", "compatible", "compensate", "compile",
    "complement", "complex", "component", "compound", "comprehensive",
    "comprise", "conceive", "concentrate", "concept", "conclusion",
    "concurrent", "conduct", "conference", "confirm", "conflict",
    "conform", "consent", "consequence", "considerable", "consistent",
    "constant", "constitute", "constrain", "construct", "consume",
    "contact", "contemporary", "context", "contract", "contradict",
    "contrary", "contrast", "contribute", "controversy", "convene",
    "converse", "convert", "convince", "cooperate", "coordinate",
    "core", "corporate", "correspond", "crucial", "culture",
    "currency", "cycle", "debate", "decline", "dedicate",
    "definite", "demonstrate", "denote", "deny", "depress",
    "derive", "design", "despite", "detect", "deviate",
    "device", "devote", "dimension", "diminish", "discipline",
    "discriminate", "displace", "display", "dispose", "distinct",
    "distort", "distribute", "diverse", "document", "domain",
    "domestic", "dominate", "draft", "drama", "duration",
    "dynamic", "edit", "element", "eliminate", "emerge",
    "emphasis", "empirical", "enable", "encounter", "energy",
    "enforce", "enhance", "enormous", "ensure", "entity",
    "environment", "equip", "equivalent", "erode", "error",
    "establish", "estate", "estimate", "ethnic", "evaluate",
    "eventual", "evident", "evolve", "exceed", "exclude",
    "exclusive", "exhibit", "expand", "expert", "explicit",
    "exploit", "export", "expose", "external", "extract",
    "facilitate", "factor", "federal", "finance", "finite",
    "flexible", "fluctuate", "focus", "format", "formula",
    "forthcoming", "foundation", "framework", "function", "fund",
    "furthermore", "gender", "generate", "global", "grade",
    "guarantee", "guideline", "hence", "hierarchy", "highlight",
    "hypothesis", "identical", "identify", "ideology", "ignorance",
    "illustrate", "image", "immigrate", "impact", "implement",
    "implicit", "imply", "impose", "incentive", "incidence",
    "incline", "income", "incorporate", "index", "indicate",
    "individual", "induce", "inevitable", "infer", "infrastructure",
    "inherent", "inhibit", "initial", "initiate", "injure",
    "innovate", "input", "insert", "insight", "inspect",
    "instance", "institute", "instruct", "intelligence", "intense",
    "interact", "intermediate", "internal", "interpret", "interval",
    "intervene", "intrinsic", "invest", "investigate", "invoke",
    "involve", "isolate", "issue", "item", "journal",
    "justify", "label", "labour", "layer", "lecture",
    "legal", "legislate", "levy", "liberal", "license",
    "likewise", "link", "locate", "logic", "maintain",
    "major", "manipulate", "manual", "margin", "mature",
    "maximise", "mechanism", "media", "mediate", "mental",
    "method", "migrate", "military", "minimal", "minimise",
    "minimum", "ministry", "minor", "mode", "modify",
    "monitor", "motivate", "mutual", "negate", "network",
    "neutral", "nevertheless", "nonetheless", "norm", "normal",
    "notion", "notwithstanding", "nuclear", "objective", "obtain",
    "obvious", "occupy", "occur", "odd", "offset",
    "ongoing", "option", "orient", "outcome", "output",
    "overall", "overlap", "overseas", "panel", "paradigm",
    "paragraph", "parallel", "parameter", "participate", "partner",
    "passive", "perceive", "percent", "period", "persist",
    "perspective", "phase", "phenomenon", "philosophy", "physical",
    "plus", "policy", "portion", "pose", "positive",
    "potential", "practitioner", "precede", "precise", "predict",
    "predominant", "preliminary", "presume", "previous", "primary",
    "prime", "principal", "principle", "prior", "priority",
    "proceed", "process", "professional", "prohibit", "project",
    "promote", "proportion", "prospect", "protocol", "psychology",
    "publication", "publish", "purchase", "pursue", "qualitative",
    "quote", "radical", "random", "range", "ratio",
    "rational", "react", "recover", "refine", "regime",
    "region", "register", "regulate", "reinforce", "reject",
    "relax", "release", "relevant", "reluctance", "rely",
    "remove", "require", "research", "reside", "resolve",
    "resource", "respond", "restore", "restrain", "restrict",
    "retain", "reveal", "revenue", "reverse", "revolution",
    "rigid", "role", "route", "scenario", "schedule",
    "scheme", "scope", "section", "sector", "secure",
    "seek", "select", "sequence", "series", "shift",
    "significant", "similar", "simulate", "site", "so-called",
    "sole", "somewhat", "source", "specific", "sphere",
    "stable", "statistic", "status", "straightforward", "strategy",
    "stress", "structure", "submit", "subordinate", "subsequent",
    "subsidy", "substitute", "successor", "sufficient", "sum",
    "summary", "supplement", "survey", "survive", "suspend",
    "sustain", "symbol", "target", "task", "team",
    "technical", "technique", "technology", "temporary", "tense",
    "terminal", "terminate", "text", "theme", "theory",
    "thereby", "thesis", "topic", "trace", "tradition",
    "transfer", "transform", "transit", "transmit", "transport",
    "trend", "trigger", "ultimate", "undergo", "underlie",
    "undertake", "uniform", "unify", "unique", "utilise",
    "valid", "vary", "vehicle", "version", "via",
    "violate", "virtual", "visible", "vision", "visual",
    "volume", "voluntary", "welfare", "whereas", "widespread",
}


def analyze_difficulty(text: str) -> dict:
    """
    综合判断文章难度等级
    返回 {"level": "CET4/CET6/考研/IELTS", "score": 1-5, "reason": "..."}
    优先使用 AI 分类，降级使用规则判断
    """
    # 先用规则快速估算
    rule_result = _rule_based_difficulty(text)

    # 尝试 AI 分类
    try:
        ai_result = _ai_difficulty(text)
        if ai_result:
            return ai_result
    except Exception:
        pass

    return rule_result


def _rule_based_difficulty(text: str) -> dict:
    """基于词汇复杂度和句长判断难度"""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    if not words:
        return {"level": "CET4", "score": 1, "reason": "无法分析"}

    total_words = len(words)

    # 统计 CET6 词汇数量
    cet6_count = sum(1 for w in words if w in CET6_WORDS)
    cet4_count = sum(1 for w in words if w in CET4_WORDS)

    # 平均句长估算
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    avg_sentence_len = total_words / max(len(sentences), 1)

    cet6_ratio = cet6_count / max(total_words, 1)

    # 判定逻辑
    if cet6_ratio > 0.06 and avg_sentence_len > 22:
        level = "IELTS"
        score = 5
    elif cet6_ratio > 0.04 and avg_sentence_len > 18:
        level = "考研"
        score = 4
    elif cet6_ratio > 0.02:
        level = "CET6"
        score = 3
    else:
        level = "CET4"
        score = 2 if avg_sentence_len > 14 else 1

    stars = "★" * score + "☆" * (5 - score)
    return {
        "level": level,
        "score": score,
        "stars": stars,
        "reason": f"词汇量约{total_words}词，CET6词汇占比{cet6_ratio:.1%}，平均句长{avg_sentence_len:.0f}词",
    }


def _ai_difficulty(text: str) -> dict | None:
    """使用 AI 判断难度"""
    system_prompt = (
        "你是一名英语教学专家。请根据以下英文文章的词汇难度、句子复杂度和内容深度，"
        "判断其适合的英语学习者等级。"
        "等级选项：CET4（大学英语四级）、CET6（大学英语六级）、考研、IELTS（雅思）。"
    )

    user_message = (
        f"请判断以下英语文章适合的学习者等级。\n\n"
        f"请严格按照以下 JSON 格式返回，不要添加任何其他文字：\n"
        f'{{"level": "CET6", "score": 3, "stars": "★★★☆☆", "reason": "简要说明判断依据"}}\n\n'
        f"{text[:3000]}"  # 截断以节省 token
    )

    ai = AIService(api_key=get_api_key(), temperature=0.1, max_tokens=200)

    try:
        result = ai.chat_json(system_prompt, user_message)
        if isinstance(result, dict) and "level" in result:
            # 确保 stars 与 score 一致
            score = result.get("score", 3)
            result["stars"] = "★" * score + "☆" * (5 - score)
            return result
    except Exception:
        pass
    return None
