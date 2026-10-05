"""Local OKF-style Markdown + YAML. Atomic writes and explicit human review, no auto approval."""

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import yaml
from .models import KnowledgeItem, ImprovementPlan

FOLDERS = {
    "entity": "entities",
    "decision": "decisions",
    "lesson": "lessons",
    "pattern": "patterns",
}


class KnowledgeStore:
    def __init__(self, root=None):
        self.root = Path(
            root or os.environ.get("KNOWLEDGE_ROOT", "knowledge")
        ).resolve()

    @contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _path(self, relative):
        path = self.root / relative
        if not path.resolve().is_relative_to(self.root) or path.is_symlink():
            raise ValueError("Caminho de conhecimento inválido")
        return path

    def _write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name("." + uuid4().hex + ".tmp")
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)

    def _save(self, item):
        data = item.model_dump(mode="json")
        content = data.pop("content")
        path = self._path(f"wiki/{FOLDERS[item.type]}/{item.id}.md")
        self._write(
            path,
            "---\n"
            + yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
            + "---\n\n"
            + content
            + "\n",
        )

    def list(self, query="", status=None, source=None):
        items = []
        for folder in FOLDERS.values():
            for path in sorted((self.root / "wiki" / folder).glob("*.md")):
                self._path(path.relative_to(self.root))
                text = path.read_text(encoding="utf-8")
                if not text.startswith("---\n"):
                    raise ValueError("Documento de conhecimento inválido")
                header, separator, content = text[4:].partition("\n---\n")
                if not separator:
                    raise ValueError("Documento de conhecimento inválido")
                item = KnowledgeItem.model_validate(
                    yaml.safe_load(header) | {"content": content.strip()}
                )
                if (status and item.validation_status != status) or (
                    source and item.source != source
                ):
                    continue
                if (
                    query
                    and query.casefold()
                    not in (
                        item.title + " " + item.content + " " + " ".join(item.tags)
                    ).casefold()
                ):
                    continue
                items.append(item)
        return sorted(items, key=lambda i: (i.updated_at, i.id), reverse=True)

    def get(self, key):
        for item in self.list():
            if item.id == key:
                return item
        raise LookupError("Conhecimento não encontrado")

    def create_candidate(self, item, raw):
        if item.validation_status != "pending_review":
            raise ValueError("Candidato deve aguardar revisão")
        with self.lock():
            if any(i.id == item.id for i in self.list()):
                raise ValueError("Candidato já existe")
            self._write(
                self._path(f"raw/executions/{item.id}.json"),
                json.dumps(raw, ensure_ascii=False, indent=2),
            )
            self._save(item)
        return item

    def review(self, key, status, request):
        if status not in ("approved", "rejected"):
            raise ValueError("Revisão inválida")
        with self.lock():
            item = self.get(key)
            if item.validation_status != "pending_review":
                raise ValueError("Somente candidatos pendentes podem ser revisados")
            if not request.confirmed:
                raise ValueError("Confirmação humana obrigatória")
            item = KnowledgeItem.model_validate(
                item.model_dump()
                | {
                    "validation_status": status,
                    "reviewer": request.reviewer,
                    "review_note": request.note,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._save(item)
        return item

    def save_plan(self, plan):
        with self.lock():
            self._write(
                self._path(f"plans/{plan.plan_id}.json"), plan.model_dump_json(indent=2)
            )
        return plan

    def plans(self, source=None):
        result = []
        for p in sorted((self.root / "plans").glob("*.json")):
            self._path(p.relative_to(self.root))
            plan = ImprovementPlan.model_validate_json(p.read_text())
            if source is None or plan.source == source:
                result.append(plan)
        return sorted(result, key=lambda x: x.created_at, reverse=True)

    def overview(self, source):
        items = self.list(source=source)
        return {
            "items": items,
            "counts": {
                s: sum(i.validation_status == s for i in items)
                for s in ("approved", "pending_review", "rejected", "superseded")
            },
            "types": {s: sum(i.type == s for i in items) for s in FOLDERS},
            "links": [
                {"from": i.id, "to": r, "label": "relacionado a"}
                for i in items
                for r in i.related
                if any(t.id == r for t in items)
            ],
        }
