"""Motor de evaluación y auditoría de diseño UX/UI para MyWorld Harness.

Combina análisis estático determinista (a11y WCAG, contraste, jerarquía, mobile)
con el juicio semántico de TypeSafe Jev (System 1 RLCD / Fallback local rápido).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jev_design_judge import JevDesignJudge, DesignEvaluationDecision

UI_EXTENSIONS = {".astro", ".html", ".tsx", ".jsx", ".vue", ".svelte"}
STYLE_EXTENSIONS = {".css", ".scss", ".sass", ".less"}
LOW_CONTRAST_PATTERNS = [
    re.compile(r"text-(slate|gray|zinc|neutral)-(300|200|100)\s+bg-white", re.IGNORECASE),
    re.compile(r"text-(slate|gray|zinc|neutral)-(600|700|800)\s+bg-black", re.IGNORECASE),
    re.compile(r"color:\s*#(?:ccc|ddd|eee|999|aaa|bbb)\s*;.*?background:\s*#(?:fff|fafafa)", re.IGNORECASE | re.DOTALL),
]

CLICHE_GRADIENT_PATTERNS = [
    re.compile(r"\bfrom-(?:purple|violet|fuchsia|pink)-(?:400|500|600|700)\b", re.IGNORECASE),
    re.compile(r"\bto-(?:pink|fuchsia|violet)-(?:400|500|600|700)\b", re.IGNORECASE),
    re.compile(r"\blinear-gradient\([^)]*(?:#8b5cf6|#a855f7|#d946ef|#ec4899|#6366f1)", re.IGNORECASE),
]

HOLLOW_COPY_PATTERNS = [
    re.compile(r"\b(?:potenciado\s+por\s+ia|impulsado\s+por\s+ia|powered\s+by\s+ai)\b", re.IGNORECASE),
    re.compile(r"\b(?:revoluciona(?:r)?(?:\s+tu|\s+el|\s+la)?|revolutionize)\b", re.IGNORECASE),
    re.compile(r"\b(?:seamless(?:ly)?(?:\s+experience|\s+integration)?|integraci[oó]n\s+sin\s+fisuras)\b", re.IGNORECASE),
    re.compile(r"\b(?:next-gen(?:\s+platform)?|de\s+[uú]ltima\s+generaci[oó]n)\b", re.IGNORECASE),
    re.compile(r"\b(?:unleash\s+the\s+power|desata\s+el\s+poder|empodera\s+tu)\b", re.IGNORECASE),
    re.compile(r"\b(?:10x(?:\s+tu)?\s+productividad)\b", re.IGNORECASE),
    re.compile(r"\b99\.9%\s+(?:satisfacci[oó]n|satisfaction)\b", re.IGNORECASE),
]

EXCESSIVE_RADII_PATTERNS = [
    re.compile(r"\brounded-(?:2xl|3xl)\b", re.IGNORECASE),
]



class MyWorldDesignEngine:
    def __init__(self, repo_path: Path) -> None:
        self.repo = repo_path
        self.judge = JevDesignJudge()

    def discover_ui_files(self) -> List[Path]:
        """Encuentra todos los archivos de interfaz dentro del repositorio excluyendo dependencias."""
        ignored = {".git", ".next", ".astro", "node_modules", "dist", "build", ".venv", "venv", ".myworld-harness"}
        ui_files: List[Path] = []
        for path in self.repo.rglob("*"):
            if any(part in ignored for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in UI_EXTENSIONS:
                ui_files.append(path)
        return sorted(ui_files)

    def audit_static_a11y(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Audita estáticamente accesibilidad, etiquetas y atributos WCAG en interfaces."""
        checks = []
        missing_alts = 0
        missing_btn_labels = 0
        contrast_warnings = 0
        missing_inputs_label = 0

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            # 1. Imágenes sin alt
            for img_match in re.finditer(r"<img\b([^>]*)/?>", content, re.IGNORECASE):
                attrs = img_match.group(1)
                if not re.search(r'\balt\s*=', attrs, re.IGNORECASE):
                    missing_alts += 1

            # 2. Botones sin texto ni aria-label
            for btn_match in re.finditer(r"<button\b([^>]*)>(.*?)</button>", content, re.IGNORECASE | re.DOTALL):
                attrs = btn_match.group(1)
                inner = btn_match.group(2).strip()
                has_aria = re.search(r'\baria-label\s*=', attrs, re.IGNORECASE)
                if not inner and not has_aria:
                    missing_btn_labels += 1

            # 3. Inputs sin label o aria-label
            # Buscar inputs que NO estén dentro de un <label>...</label>
            label_blocks = [m.group(0) for m in re.finditer(r"<label\b[^>]*>.*?</label>", content, re.IGNORECASE | re.DOTALL)]

            for input_match in re.finditer(r"<input\b([^>]*)/?>", content, re.IGNORECASE):
                attrs = input_match.group(1)
                input_str = input_match.group(0)
                input_type = re.search(r'\btype\s*=\s*["\']?([^"\'\s>]+)', attrs, re.IGNORECASE)
                t_val = input_type.group(1).lower() if input_type else "text"
                if t_val in {"hidden", "submit", "button"}:
                    continue
                if "aria-hidden=\"true\"" in attrs or "hidden" in attrs:
                    continue
                # Si está anidado dentro de un <label>...</label>, tiene label implícito accesible
                is_wrapped_in_label = any(input_str in block for block in label_blocks)
                has_label = re.search(r'\b(aria-label|aria-labelledby|placeholder|id)\s*=', attrs, re.IGNORECASE) or is_wrapped_in_label
                if not has_label:
                    missing_inputs_label += 1

            # 4. Patrones de contraste peligroso
            for pattern in LOW_CONTRAST_PATTERNS:
                if pattern.search(content):
                    contrast_warnings += 1

        # Generar resultados
        checks.append({
            "check": "design.a11y.image_alt",
            "status": "pass" if missing_alts == 0 else "fail",
            "detail": "Todas las imágenes cuentan con atributo alt" if missing_alts == 0 else f"{missing_alts} imagen(es) sin atributo alt detectable"
        })
        checks.append({
            "check": "design.a11y.interactive_labels",
            "status": "pass" if (missing_btn_labels == 0 and missing_inputs_label == 0) else "fail",
            "detail": "Botones e inputs cuentan con etiquetas accesibles" if (missing_btn_labels == 0 and missing_inputs_label == 0) else f"{missing_btn_labels} botón(es) y {missing_inputs_label} input(s) sin etiqueta o aria-label"
        })
        checks.append({
            "check": "design.contrast.safe_ratios",
            "status": "pass" if contrast_warnings == 0 else "fail",
            "detail": "Sin combinaciones de bajo contraste detectadas" if contrast_warnings == 0 else f"{contrast_warnings} alerta(s) de contraste deficiente"
        })

        return checks

    def audit_mobile_responsiveness(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Verifica la presencia de viewport meta y clases adaptativas responsivas."""
        checks = []
        has_viewport = False
        has_responsive_classes = False

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            content_lower = content.lower()
            if "viewport" in content_lower and ("width=device-width" in content_lower or 'width: "device-width"' in content_lower or "width: 'device-width'" in content_lower):
                has_viewport = True
            if any(term in content for term in ["@media", "sm:", "md:", "lg:", "xl:", "grid-cols-", "flex-col"]):
                has_responsive_classes = True

        checks.append({
            "check": "design.responsive.viewport",
            "status": "pass" if has_viewport or len(files) == 0 else "pending",
            "detail": "Etiqueta viewport configurada para dispositivos móviles" if has_viewport else "Revisar configuración viewport en layout maestro"
        })
        checks.append({
            "check": "design.responsive.breakpoints",
            "status": "pass" if has_responsive_classes or len(files) == 0 else "pending",
            "detail": "Patrones adaptativos (flex/grid/media queries) detectados" if has_responsive_classes else "No se detectaron breakpoints responsivos explícitos"
        })

        return checks

    def audit_semantic_hierarchy(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Verifica la coherencia de la jerarquía de encabezados."""
        checks = []
        h1_counts = 0

        for file_path in files:
            # Layouts, páginas principales, dashboards y buscadores suelen definir H1
            is_main = any(term in file_path.name.lower() for term in ["index", "page", "layout", "home", "hero", "buscador", "dashboard", "checkout"]) or len(files) <= 3
            if is_main:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    h1_counts += len(re.findall(r"<h1\b", content, re.IGNORECASE))
                except Exception:
                    continue

        detail = f"{h1_counts} encabezado(s) H1 en páginas principales"
        checks.append({
            "check": "design.hierarchy.headings",
            "status": "pass" if h1_counts >= 1 else "pending",
            "detail": detail if h1_counts >= 1 else "No se detectó un encabezado H1 explícito en las páginas principales"
        })
        return checks

    def evaluate_with_jev(self, files: List[Path]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Ejecuta el juicio semántico de TypeSafe Jev sobre la muestra más representativa."""
        sample_content = ""
        target_name = self.repo.name

        def extract_ui_sample(raw_text: str) -> str:
            # Eliminar bloques masivos de <style> para que Jev evalúe el markup visual real
            cleaned = re.sub(r"<style\b[^>]*>.*?</style>", "", raw_text, flags=re.DOTALL | re.IGNORECASE)
            return cleaned.strip()[:4000]

        # Priorizar archivo de interfaz principal (hero, landing, index, app/page.tsx, etc.)
        def score_ui_file(p: Path) -> int:
            str_path = p.as_posix().lower()
            name = p.name.lower()
            if "hero" in name:
                return 105
            if str_path.endswith("src/app/page.tsx") or name in ["index.astro", "index.html", "index.tsx"]:
                return 100
            if "index" in name or "home" in name or "landing" in name:
                return 90
            if "hero" in name:
                return 80
            if "dashboard" in name or "buscador" in name:
                return 70
            if "page" in name:
                return 50
            return 10

        sorted_files = sorted(files, key=score_ui_file, reverse=True)

        # Buscar el archivo representativo más relevante
        for file_path in sorted_files:
            try:
                raw = file_path.read_text(encoding="utf-8", errors="replace")
                sample_content = extract_ui_sample(raw)
                target_name = file_path.name
                if len(sample_content) > 100:
                    break
            except Exception:
                pass

        if not sample_content and files:
            try:
                raw = files[0].read_text(encoding="utf-8", errors="replace")
                sample_content = extract_ui_sample(raw)
                target_name = files[0].name
            except Exception:
                sample_content = "<div>No UI content</div>"

        decision: DesignEvaluationDecision = self.judge.evaluate_ui(sample_content, target_name)

        checks = [
            {
                "check": "design.jev.hierarchy_clarity",
                "status": "pass" if decision.hierarchy_clarity in {"clara", "optima"} else ("pending" if decision.hierarchy_clarity == "aceptable" else "fail"),
                "detail": f"Nivel: {decision.hierarchy_clarity} (score={decision.hierarchy_score})"
            },
            {
                "check": "design.jev.information_density",
                "status": "pass" if decision.information_density == "equilibrada" else "pending",
                "detail": f"Densidad: {decision.information_density}"
            },
            {
                "check": "design.jev.accessibility_risk",
                "status": "pass" if decision.accessibility_risk == "bajo" else ("pending" if decision.accessibility_risk == "moderado" else "fail"),
                "detail": f"Riesgo: {decision.accessibility_risk} (score={decision.accessibility_risk_score})"
            },
            {
                "check": "design.jev.client_friction",
                "status": "pass" if decision.client_friction_prob < 0.40 else ("pending" if decision.client_friction_prob <= 0.65 else "fail"),
                "detail": f"Probabilidad de fricción usuario: {decision.client_friction_prob:.3f}"
            }
        ]

        summary = {
            "target": decision.target,
            "status": decision.status,
            "verdict_reason": decision.verdict_reason,
            "latency_ms": decision.latency_ms
        }
        return checks, summary

    def audit_anti_slop(self, files: List[Path]) -> List[Dict[str, Any]]:
        """Audita el cumplimiento del protocolo Anti-AI-Slop: gradientes cliché, geometría, copy inflado y rigor de datos."""
        checks = []
        cliche_gradients_count = 0
        hollow_copy_count = 0
        excessive_radii_count = 0
        tables_or_kpis_count = 0
        tabular_mono_count = 0
        missing_states_count = 0
        interactive_files_count = 0

        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            content_lower = content.lower()

            # 1. Gradientes cliché de IA (púrpura, violeta, fucsia, rosa neón)
            for pattern in CLICHE_GRADIENT_PATTERNS:
                matches = pattern.findall(content)
                cliche_gradients_count += len(matches)

            # 2. Copy inflado o buzzwords de IA
            for pattern in HOLLOW_COPY_PATTERNS:
                matches = pattern.findall(content)
                hollow_copy_count += len(matches)

            # 3. Geometría hiper-redondeada (burbujas en tarjetas, tablas o contenedores)
            for pattern in EXCESSIVE_RADII_PATTERNS:
                matches = pattern.findall(content)
                excessive_radii_count += len(matches)

            # 4. Rigor de datos y tipografía tabular
            has_data_surface = bool(re.search(r"<(?:table|thead|tbody)\b|class=[\"'][^\"']*(?:data-table|forensic-table|metric-card|kpi-card|stat-box)", content, re.IGNORECASE))
            if has_data_surface:
                tables_or_kpis_count += 1
                has_mono = bool(re.search(r"\b(?:font-mono|tabular-nums|jetbrains|font-family:\s*monospace)\b", content, re.IGNORECASE))
                if has_mono:
                    tabular_mono_count += 1

            # 5. Estados reales de software en vistas interactivas (formularios o listados con fetch)
            is_interactive_view = bool(re.search(r"<(?:form|table)\b|useQuery|useEffect|fetch\(|\$fetch|useState", content, re.IGNORECASE))
            if is_interactive_view:
                interactive_files_count += 1
                has_any_state = any(term in content_lower for term in ["skeleton", "animate-pulse", "loading", "spinner", "cargando", "empty", "sin datos", "no hay", "error", "alert"])
                if not has_any_state:
                    missing_states_count += 1

        # Check 1: Gradientes cliché
        checks.append({
            "check": "design.anti_slop.cliche_gradients",
            "status": "pass" if cliche_gradients_count == 0 else "fail",
            "detail": "Paleta sobria y libre de gradientes neón cliché de IA" if cliche_gradients_count == 0 else f"{cliche_gradients_count} gradiente(s) púrpura/neón detectado(s). Usar tokens UDS (Midnight Void / Active Signal)"
        })

        # Check 2: Copy de marketing hueco de IA
        checks.append({
            "check": "design.anti_slop.hollow_copy",
            "status": "pass" if hollow_copy_count == 0 else "fail",
            "detail": "Redacción técnica y sobria sin buzzwords infladas de IA" if hollow_copy_count == 0 else f"{hollow_copy_count} frase(s) cliché o buzzwords de IA detectadas ('revoluciona', 'potenciado con ia', etc.)"
        })

        # Check 3: Geometría afilada institucional
        checks.append({
            "check": "design.anti_slop.geometry",
            "status": "pass" if excessive_radii_count == 0 else "fail",
            "detail": "Geometría Techno-Structuralist afilada respetada (rounded-none / rounded-sm)" if excessive_radii_count == 0 else f"{excessive_radii_count} uso(s) de esquinas hiper-redondeadas (rounded-2xl/3xl) detectadas"
        })

        # Check 4: Tipografía monoespaciada en datos
        if tables_or_kpis_count > 0:
            mono_ok = tabular_mono_count >= tables_or_kpis_count
            checks.append({
                "check": "design.anti_slop.tabular_data",
                "status": "pass" if mono_ok else "pending",
                "detail": f"{tabular_mono_count}/{tables_or_kpis_count} superficie(s) de datos usan tipografía mono/tabular-nums estricta" if mono_ok else f"{tables_or_kpis_count - tabular_mono_count} tabla(s) o métrica(s) no declaran font-mono ni tabular-nums"
            })

        # Check 5: Estados reales de software
        if interactive_files_count > 0:
            states_ok = missing_states_count == 0
            checks.append({
                "check": "design.anti_slop.software_states",
                "status": "pass" if states_ok else "pending",
                "detail": "Vistas interactivas implementan estados reales (loading/empty/error)" if states_ok else f"{missing_states_count} vista(s) interactiva(s) carecen de patrones para loading, empty o error states"
            })

        return checks

    def run_full_design_gate(self, semantic_authorized: bool = False) -> Dict[str, Any]:
        """Ejecuta el gate completo de diseño y entrega el reporte estructurado."""
        ui_files = self.discover_ui_files()

        if not ui_files:
            return {
                "applicable": False,
                "file_count": 0,
                "checks": [
                    {
                        "check": "design.applicability",
                        "status": "not_applicable",
                        "detail": "No se encontraron archivos de interfaz (Astro, HTML, TSX, React, Vue, Svelte)"
                    }
                ],
                "summary": None
            }

        checks = []
        checks.append({
            "check": "design.surface.discovered",
            "status": "pass",
            "detail": f"{len(ui_files)} archivo(s) de interfaz descubiertos"
        })
        checks.extend(self.audit_static_a11y(ui_files))
        checks.extend(self.audit_mobile_responsiveness(ui_files))
        checks.extend(self.audit_semantic_hierarchy(ui_files))
        checks.extend(self.audit_anti_slop(ui_files))
        jev_summary = None
        if semantic_authorized:
            jev_checks, jev_summary = self.evaluate_with_jev(ui_files)
            checks.extend(jev_checks)
        else:
            checks.append({"check": "design.jev.authorization", "status": "pending", "detail": "Evaluación externa no ejecutada; requiere autorización para enviar contenido UI", "blocking": False})

        return {
            "applicable": True,
            "file_count": len(ui_files),
            "checks": checks,
            "jev_summary": jev_summary
        }
