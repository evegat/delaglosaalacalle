from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

KEY_FILE = Path(r"c:\Users\evega\OneDrive\Documents\Obsidian\MyWorld\2 - Project\P129 - Typesafe ai Jev Acess First meeting\claves.txt")


def get_typesafe_key() -> str | None:
    env_key = os.getenv("TYPESAFE_API_KEY")
    if env_key:
        return env_key.strip()
    if KEY_FILE.exists():
        try:
            return KEY_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


@dataclass
class DesignEvaluationDecision:
    target: str
    hierarchy_clarity: str        # "confusa" | "aceptable" | "clara" | "optima"
    hierarchy_score: float        # 0.0 a 3.0
    information_density: str      # "hacinada" | "equilibrada" | "excesivamente_vacia"
    accessibility_risk: str       # "bajo" | "moderado" | "alto" | "critico"
    accessibility_risk_score: float
    client_friction_prob: float   # 0.0 a 1.0 (Noul)
    slop_risk: str = "bajo"       # "bajo" | "moderado" | "alto"
    slop_risk_score: float = 0.0  # 0.0 a 2.0
    status: str = "pass"          # "pass" | "needs_review" | "reject"
    verdict_reason: str = ""
    latency_ms: float = 0.0


class JevDesignJudge:
    """Juez semántico de diseño y UI/UX impulsado por TypeSafe Jev (System 1 RLCD)."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or get_typesafe_key()

    def evaluate_ui(self, ui_description_or_html: str, target_name: str = "component") -> DesignEvaluationDecision:
        """Evalúa jerarquía, densidad, accesibilidad y riesgo de fricción de la interfaz."""
        start_time = time.time()
        desc = ui_description_or_html.strip()

        if self.api_key:
            try:
                from typesafe_sdk import TypeSafeClient, Choice, Score, Noul  # type: ignore
                client = TypeSafeClient(api_key=self.api_key)
                res = client.system_one(
                    state={"ui_content": desc[:4000], "target": target_name},
                    questions={
                        "hierarchy_clarity": Score(
                            levels=["confusa", "aceptable", "clara", "optima"]
                        ),
                        "information_density": Choice(
                            options=["hacinada", "equilibrada", "excesivamente_vacia"]
                        ),
                        "accessibility_risk": Score(
                            levels=["bajo", "moderado", "alto", "critico"]
                        ),
                        "client_friction_risk": Noul()
                    }
                )
                latency = (time.time() - start_time) * 1000
                h_level = res["hierarchy_clarity"].level
                h_score = round(float(res["hierarchy_clarity"].score), 2)
                density = res["information_density"].choice
                a_level = res["accessibility_risk"].level
                a_score = round(float(res["accessibility_risk"].score), 2)
                f_prob = round(float(res["client_friction_risk"].prob), 3)

                status = "pass"
                if a_level in ["alto", "critico"] or f_prob > 0.65 or h_level == "confusa":
                    status = "reject"
                elif a_level == "moderado" or f_prob > 0.40 or density != "equilibrada":
                    status = "needs_review"

                return DesignEvaluationDecision(
                    target=target_name,
                    hierarchy_clarity=h_level,
                    hierarchy_score=h_score,
                    information_density=density,
                    accessibility_risk=a_level,
                    accessibility_risk_score=a_score,
                    client_friction_prob=f_prob,
                    status=status,
                    verdict_reason=f"Decidido por Jev RLCD: jerarquía {h_level}, densidad {density}, fricción p={f_prob}",
                    latency_ms=round(latency, 1)
                )
            except Exception:
                pass

        # Calibrador determinista System 1 (fallback local rápido < 5ms)
        desc_lower = desc.lower()
        latency = (time.time() - start_time) * 1000

        # Señales de accesibilidad y estructura
        has_aria = "aria-" in desc_lower or "role=" in desc_lower or "alt=" in desc_lower
        has_contrast_issues = any(w in desc_lower for w in ["#ccc", "#999", "lightgray", "opacity-30", "text-slate-300 on white"])
        has_clear_hierarchy = any(tag in desc_lower for tag in ["<h1", "<h2", "text-2xl", "text-xl", "font-bold", "heading"])
        is_crowded = len(desc) > 2500 and desc.count("<button") > 8 and desc.count("<input") > 6

        # Señales de AI Slop (plantilla genérica de IA, gradientes cliché, buzzwords de marketing)
        has_cliche_gradient = any(w in desc_lower for w in ["from-purple-", "from-violet-", "from-indigo-", "to-pink-", "from-fuchsia-"])
        has_hollow_copy = any(w in desc_lower for w in [
            "potenciado por ia", "impulsado por ia", "powered by ai",
            "revoluciona tu", "revoluciona el", "seamlessly", "next-gen",
            "unleash the power", "10x tu productividad", "99.9% satisfacción"
        ])
        has_inflated_radii = any(w in desc_lower for w in ["rounded-2xl", "rounded-3xl", "rounded-full"]) and ("<table" in desc_lower or "<div" in desc_lower)

        slop_risk = "bajo"
        slop_risk_score = 0.0
        if has_cliche_gradient and has_hollow_copy:
            slop_risk = "alto"
            slop_risk_score = 2.0
        elif has_cliche_gradient or has_hollow_copy or has_inflated_radii:
            slop_risk = "moderado"
            slop_risk_score = 1.0

        if is_crowded:
            density = "hacinada"
        elif len(desc) < 200:
            density = "excesivamente_vacia"
        else:
            density = "equilibrada"

        if has_clear_hierarchy:
            h_level = "clara"
            h_score = 2.0
        else:
            h_level = "aceptable"
            h_score = 1.0

        if has_contrast_issues:
            a_level = "alto"
            a_score = 2.2
            f_prob = 0.55
        elif not has_aria and ("<input" in desc_lower or "<button" in desc_lower):
            a_level = "moderado"
            a_score = 1.2
            f_prob = 0.35
        else:
            a_level = "bajo"
            a_score = 0.3
            f_prob = 0.15

        # Penalización por riesgo de IA Slop en la fricción percibida
        if slop_risk == "alto":
            f_prob = max(f_prob, 0.70)
        elif slop_risk == "moderado":
            f_prob = max(f_prob, 0.45)

        status = "pass"
        if a_level in ["alto", "critico"] or f_prob > 0.65 or slop_risk == "alto":
            status = "reject"
        elif a_level == "moderado" or density != "equilibrada" or slop_risk == "moderado":
            status = "needs_review"

        verdict_reason = f"Calibrador System 1: jerarquía {h_level}, densidad {density}, riesgo a11y {a_level}, slop {slop_risk}"
        if slop_risk == "alto":
            verdict_reason += " (bloqueado por patrones detectados de AI Slop)"

        return DesignEvaluationDecision(
            target=target_name,
            hierarchy_clarity=h_level,
            hierarchy_score=h_score,
            information_density=density,
            accessibility_risk=a_level,
            accessibility_risk_score=a_score,
            client_friction_prob=f_prob,
            slop_risk=slop_risk,
            slop_risk_score=slop_risk_score,
            status=status,
            verdict_reason=verdict_reason,
            latency_ms=round(latency, 1)
        )


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "Demo UI"
    sample_content = sys.argv[2] if len(sys.argv) > 2 else "<h1>Panel de Control</h1><button class='bg-blue-600 text-white px-4 py-2 rounded' aria-label='Guardar cambios'>Guardar</button>"

    judge = JevDesignJudge()
    decision = judge.evaluate_ui(sample_content, target)
    print(json.dumps(asdict(decision), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
