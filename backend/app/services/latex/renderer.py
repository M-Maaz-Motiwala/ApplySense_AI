import re
import subprocess
from pathlib import Path
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from app.core.config import get_settings

LATEX_ESCAPE = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
}


class LatexRenderer:
    def __init__(self) -> None:
        self.settings = get_settings()
        template_path = Path(self.settings.latex_template_path)
        self.env = Environment(loader=FileSystemLoader(str(template_path.parent)))
        self.template_name = template_path.name

    def _escape_text(self, value: str) -> str:
        if not value:
            return ""
        # 1. Basic LaTeX character escaping
        escaped = re.sub(r"[&%$_#]", lambda m: LATEX_ESCAPE[m.group(0)], value)
        # 2. Problematic Unicode characters
        # U+202F is Narrow No-Break Space, often used by LLMs before units
        escaped = escaped.replace("\u202f", " ")
        # U+2011 is Non-Breaking Hyphen
        escaped = escaped.replace("\u2011", "-")
        # Smart quotes and dashes
        escaped = escaped.replace("\u201c", "``").replace("\u201d", "''")
        escaped = escaped.replace("\u2018", "`").replace("\u2019", "'")
        escaped = escaped.replace("\u2013", "--").replace("\u2014", "---")
        return escaped

    def _escape_payload(self, payload: dict) -> dict:
        escaped = {}
        for key, value in payload.items():
            if isinstance(value, str):
                escaped[key] = self._escape_text(value)
            elif isinstance(value, list):
                escaped[key] = [self._escape_payload(item) if isinstance(item, dict) else self._escape_text(item) for item in value]
            elif isinstance(value, dict):
                escaped[key] = self._escape_payload(value)
            else:
                escaped[key] = value
        return escaped

    def render_and_compile(self, optimized_json: dict, user_id: str = None, job_id: str = None) -> dict:
        base_dir = Path(self.settings.latex_output_dir)
        if user_id and job_id:
            output_dir = base_dir / str(user_id) / str(job_id)
        else:
            output_dir = base_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)

        escaped_payload = self._escape_payload(optimized_json)
        template = self.env.get_template(self.template_name)
        latex_source = template.render(**escaped_payload)

        stem = "resume"
        tex_file = output_dir / f"{stem}.tex"
        pdf_file = output_dir / f"{stem}.pdf"

        tex_file.write_text(latex_source, encoding="utf-8")

        compile_cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory",
            str(output_dir),
            str(tex_file),
        ]
        result = subprocess.run(compile_cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not pdf_file.exists():
            raise RuntimeError(f"LaTeX compilation failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")

        return {
            "latex_source": latex_source,
            "pdf_path": str(pdf_file),
            "output_dir": str(output_dir),
            "metadata": {"tex_path": str(tex_file), "compiler": "pdflatex"},
        }


latex_renderer = LatexRenderer()
