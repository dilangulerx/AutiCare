import json
import os
import re
import yaml
from crewai import Agent, Task, Crew, Process

def load_yaml(filename: str):
    config_path = os.path.join(os.path.dirname(__file__), f"../crew_config/{filename}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def build_agents() -> dict:
    agents_config = load_yaml("agents.yaml")
    agents = {}
    for a in agents_config:
        name = a.pop("agent_name")
        agents[name] = Agent(
            llm=f"openai/gpt-4o-mini",
            **a
        )
    return agents

def build_tasks(agents: dict, descriptions: dict) -> list:
    tasks_config = load_yaml("tasks.yaml")
    tasks = []
    for t in tasks_config:
        name = t.pop("task_name")
        agent_name = t.pop("agent")
        # Dinamik description varsa üzerine yaz
        if name in descriptions:
            t["description"] = descriptions[name]
        tasks.append(Task(
            agent=agents[agent_name],
            **t
        ))
    return tasks

def generate_crew_report(child_name: str, logs: list) -> dict:
    logs_text = ""
    for log in logs:
        logs_text += f"""
Tarih: {log.get('date')}
- Göz Teması: {log.get('eye_contact')}/5
- İletişim: {log.get('communication_score')}/5
- Agresyon: {log.get('aggression_level')}/5
- Uyku: {log.get('sleep_hours')} saat
- Notlar: {log.get('notes', '-')}
"""

    agents = build_agents()

    descriptions = {
        "analyze_logs_task": f"""
{child_name} adlı çocuğun bu haftaki verilerini analiz et:
{logs_text}
Trendleri, güçlü yönleri ve dikkat gerektiren alanları belirle.
""",
        "detect_anomalies_task": f"""
{child_name} adlı çocuğun verilerinde anormal sapmalar var mı?
{logs_text}
Normal gelişim beklentilerine göre değerlendir.
""",
        "generate_recommendations_task": f"""
{child_name} için analiz ve anomali sonuçlarına dayanarak
ebeveyne 3 somut ve uygulanabilir öneri sun. Türkçe yaz.
""",
        "compile_weekly_report_task": f"""
{child_name} için haftalık gelişim raporunu Türkçe, sıcak ve 
destekleyici bir dille yaz. Şunları içermeli:
- Genel değerlendirme (2-3 paragraf)
- Bu haftanın öne çıkan gelişimi
- Dikkat edilmesi gereken alan
- Ebeveyne 3 pratik öneri
Tıbbi teşhis koyma, sadece gözlem ve öneri sun.
"""
    }

    # Sadece rapor için 4 task kullan (chat task hariç)
    all_tasks = build_tasks(agents, descriptions)
    report_tasks = all_tasks[:4]  # ilk 4 task

    crew = Crew(
        agents=[
            agents["BehavioralAnalystAgent"],
            agents["AnomalyDetectorAgent"],
            agents["TherapyAdvisorAgent"],
            agents["ReportGeneratorAgent"],
        ],
        tasks=report_tasks,
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()

    return {
        "report_text": str(result),
        "generated_by": "CrewAI YAML (4 Agent)"
    }


def _rule_based_anomaly(logs: list) -> dict | None:
    """Sayısal uç değerler — modele güvenmeden gerçek anomali sayılır."""
    rows = []
    for log in logs:
        try:
            rows.append({
                "date": str(log.get("date", "")),
                "eye": int(log.get("eye_contact") or 0),
                "comm": int(log.get("communication_score") or 0),
                "agg": int(log.get("aggression_level") or 0),
                "sleep": float(log.get("sleep_hours") or 0),
            })
        except (TypeError, ValueError):
            continue
    if not rows:
        return None

    reasons: list[str] = []
    for r in rows:
        if r["agg"] >= 4:
            reasons.append("Agresyon skoru yüksek (4–5).")
        if r["sleep"] > 0 and r["sleep"] <= 4:
            reasons.append("Uyku süresi belirgin düşük.")
        if r["sleep"] >= 14:
            reasons.append("Uyku süresi olağan üstü yüksek.")
        if r["eye"] <= 1:
            reasons.append("Göz teması çok düşük.")
        if r["comm"] <= 1:
            reasons.append("İletişim skoru çok düşük.")

    by_date = sorted(rows, key=lambda x: x["date"], reverse=True)
    if len(by_date) >= 2:
        a, b = by_date[0], by_date[1]
        if a["eye"] >= 3 and b["eye"] >= 3 and (a["eye"] - b["eye"]) >= 2:
            reasons.append("Göz temasında kısa sürede belirgin düşüş.")
        if a["comm"] >= 3 and b["comm"] >= 3 and (a["comm"] - b["comm"]) >= 2:
            reasons.append("İletişim skorunda belirgin düşüş.")

    if not reasons:
        return None
    uniq = list(dict.fromkeys(reasons))
    return {"has_anomaly": True, "message": " ".join(uniq[:4])}


def _parse_anomaly_response(raw: str) -> dict:
    """Crew çıktısından JSON veya metin ile has_anomaly + message üret."""
    raw = raw.strip()
    try:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            obj = json.loads(raw[start : end + 1])
            if isinstance(obj, dict) and "has_anomaly" in obj:
                return {
                    "has_anomaly": bool(obj["has_anomaly"]),
                    "message": str(obj.get("message", "")).strip() or "Değerlendirme tamamlandı.",
                }
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    m_true = re.search(r'"has_anomaly"\s*:\s*true\b', raw, re.I)
    m_false = re.search(r'"has_anomaly"\s*:\s*false\b', raw, re.I)
    if m_true and not m_false:
        return {"has_anomaly": True, "message": raw[:500].strip() or "Dikkat gerektiren bir patern görüldü."}
    if m_false and not m_true:
        msg_m = re.search(r'"message"\s*:\s*"([^"]*)"', raw)
        msg = msg_m.group(1) if msg_m else raw[:500]
        return {"has_anomaly": False, "message": msg or "Belirgin sapma yok."}

    lower = raw.lower()
    negative = any(
        p in lower
        for p in ("anomali yok", "anomaly yok", "önemli sapma yok", "belirgin sapma yok", 'has_anomaly": false')
    )
    if negative:
        return {"has_anomaly": False, "message": raw[:500] if raw else "Belirgin bir sapma tespit edilmedi."}

    return {
        "has_anomaly": False,
        "message": raw[:500] if raw else "Model net JSON üretmedi; sayısal uç değer yoksa uyarı gösterilmedi.",
    }


def detect_anomalies(child_name: str, logs: list) -> dict:
    """Dashboard anomali kartı: önce sayısal uç değerler, yoksa LLM (AnomalyDetectorAgent)."""
    heuristic = _rule_based_anomaly(logs)
    if heuristic:
        return heuristic

    logs_text = ""
    for log in logs:
        logs_text += f"Tarih: {log.get('date')} Göz: {log.get('eye_contact')}/5 İletişim: {log.get('communication_score')}/5 Agresyon: {log.get('aggression_level')}/5 Uyku: {log.get('sleep_hours')}h\n"

    agents = build_agents()
    descriptions = {
        "detect_anomalies_task": f"""
{child_name} adlı çocuğun son günlük kayıtları:
{logs_text}

Kurallar:
- 1–2 günlük küçük farklar (ör. göz temasında 1 puan) NORMAL kabul edilir; bunlar için has_anomaly false olmalı.
- has_anomaly true SADECE belirgin sapma varsa: örn. bir metrikte ani çöküş (birden fazla gün veya uç değer), uyku veya agresyonda ciddi bozulma.
- Şüphede kalırsan has_anomaly false seç.

Yanıtının SON satırında yalnızca şu JSON'u ver, başka metin ekleme:
{{"has_anomaly": true veya false, "message": "Türkçe, kısa özet"}}
Tıbbi teşhis koyma.
"""
    }
    all_tasks = build_tasks(agents, descriptions)
    anomaly_task = all_tasks[1]

    crew = Crew(
        agents=[agents["AnomalyDetectorAgent"]],
        tasks=[anomaly_task],
        process=Process.sequential,
        verbose=False,
    )
    raw = str(crew.kickoff())
    return _parse_anomaly_response(raw)


def generate_chat_response(child_name: str, query: str, logs: list) -> str:
    logs_text = ""
    for log in logs[-7:]:
        logs_text += (
            f"Tarih: {log.get('date')} | Göz teması: {log.get('eye_contact')}/5 | "
            f"İletişim: {log.get('communication_score')}/5 | Agresyon: {log.get('aggression_level')}/5 | "
            f"Uyku: {log.get('sleep_hours')} saat\n"
        )

    agents = build_agents()

    descriptions = {
        "handle_chat_query_task": f"""
Ebeveyn sorusu: {query}

Çocuğun tam adı (yalnızca bunu kullan, başka isim uydurma): "{child_name}"

Son günlük kayıtları (yalnızca bu satırlardaki sayıları kullan; tarih veya skor ekleme/çarpıtma):
{logs_text if logs_text.strip() else "(Henüz kayıt yok)"}

Kurallar:
- Yanıtta çocuğu mutlaka "{child_name}" diye an.
- Skorları yukarıdaki tabloyla birebir uyumlu anlat; olmayan gün veya değer uydurma.
- Türkçe, empatik ve destekleyici ol; tıbbi teşhis koyma.
"""
    }

    all_tasks = build_tasks(agents, descriptions)
    chat_task = all_tasks[4]  # 5. task

    crew = Crew(
        agents=[agents["ConversationalAgent"]],
        tasks=[chat_task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()
    return str(result)