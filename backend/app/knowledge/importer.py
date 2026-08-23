from __future__ import annotations

import hashlib
import io
import re
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as ET
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ids import uuid7

from .models import ContentReview, EvidenceClaim, EvidenceClaimSource, EvidenceClaimVersion, EvidenceSource, Method, MethodAlias, MethodEffect, MethodRelation, MethodVersion, PhysicalQuality, SourceDisposition, SourceImport, SourceImportRow


MAX_WORKBOOK_BYTES = 20 * 1024 * 1024
MAX_XML_ENTRY_BYTES = 15 * 1024 * 1024
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


class WorkbookImportError(ValueError):
    pass


DOCUMENT_FIELDS = {
    "exercise name": "canonical_name", "name": "canonical_name", "code": "code",
    "type": "method_type", "movement pattern": "movement_pattern", "aliases": "aliases",
    "equipment": "equipment_codes", "environment": "environments", "environments": "environments",
    "surface": "surfaces", "surfaces": "surfaces", "dose units": "accepted_dose_units",
    "force direction": "force_directions", "force directions": "force_directions",
    "contraction type": "contractions", "contractions": "contractions", "movement speed": "speed_intent",
    "minimum level": "level_minimum", "technical cost": "technical_cost", "impact cost": "impact_cost",
    "fatigue cost": "fatigue_cost", "requires supervision": "supervision_required",
    "instructions": "instructions", "coaching cues": "cues", "cues": "cues",
    "common mistakes": "common_errors", "safety": "safety_boundaries",
    "safety and stop conditions": "safety_boundaries",
}
LIST_DOCUMENT_FIELDS = {"aliases", "equipment_codes", "environments", "surfaces", "accepted_dose_units", "force_directions", "contractions", "instructions", "cues", "common_errors", "safety_boundaries"}


def _document_text(filename: str, content: bytes) -> str:
    if not content or len(content) > MAX_DOCUMENT_BYTES:
        raise WorkbookImportError("document is empty or exceeds the 10 MB limit")
    suffix = filename.lower().rsplit(".", 1)[-1]
    if suffix == "md":
        try: return content.decode("utf-8")
        except UnicodeDecodeError as exc: raise WorkbookImportError("Markdown must be UTF-8 encoded") from exc
    if suffix != "docx":
        raise WorkbookImportError("choose a .md or .docx file")
    try:
        with ZipFile(io.BytesIO(content)) as archive:
            root = _safe_xml(archive, "word/document.xml")
    except BadZipFile as exc:
        raise WorkbookImportError("file is not a valid DOCX document") from exc
    paragraphs = []
    for paragraph in root.iter(f"{{{WORD_NS}}}p"):
        value = "".join(node.text or "" for node in paragraph.iter(f"{{{WORD_NS}}}t")).strip()
        if value: paragraphs.append(value)
    return "\n".join(paragraphs)


def parse_exercise_document(filename: str, content: bytes) -> tuple[str, list[WorkbookCandidate]]:
    """Parse repeated `## Exercise` sections containing `Field: value` lines."""
    text = _document_text(filename, content).replace("\r\n", "\n")
    sections = re.split(r"(?m)^\s*#{1,3}\s+(?:Exercise\s*:\s*)?", text)
    if len(sections) == 1:
        sections = re.split(r"(?mi)^\s*Exercise\s*:\s*", text)
    candidates: list[WorkbookCandidate] = []
    seen_names: set[str] = set()
    for index, section in enumerate(sections[1:], 1):
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines: continue
        payload: dict[str, Any] = {"canonical_name": lines[0].strip("# ")}
        current_field: str | None = None
        for line in lines[1:]:
            matched = re.match(r"^(?:[-*]\s*)?([^:]{2,40}):\s*(.*)$", line)
            if matched and matched.group(1).strip().lower() in DOCUMENT_FIELDS:
                current_field = DOCUMENT_FIELDS[matched.group(1).strip().lower()]
                value = matched.group(2).strip()
                payload[current_field] = _split(value) if current_field in LIST_DOCUMENT_FIELDS else value
            elif current_field in LIST_DOCUMENT_FIELDS:
                value = re.sub(r"^[-*\d.)\s]+", "", line).strip()
                if value: payload.setdefault(current_field, []).append(value)
        name = str(payload.get("canonical_name", "")).strip()
        errors: list[str] = []
        normalized_name = name.casefold()
        if not name: errors.append("missing exercise name")
        if normalized_name in seen_names: errors.append("duplicate exercise name in document")
        seen_names.add(normalized_name)
        for field in ("movement_pattern", "instructions", "cues", "common_errors", "safety_boundaries"):
            if not payload.get(field): errors.append(f"missing {field}")
        def number(field: str, default: int) -> int:
            try: return max(1, min(5, int(payload.get(field, default))))
            except (TypeError, ValueError): errors.append(f"invalid {field}"); return default
        normalized = {
            "code": _slug(str(payload.get("code") or name)), "canonical_name": name,
            "method_type": str(payload.get("method_type") or "exercise").lower().replace(" ", "_"),
            "movement_pattern": _slug(str(payload.get("movement_pattern") or "general"))[:50],
            "aliases": payload.get("aliases", []), "equipment_codes": [_slug(x) for x in payload.get("equipment_codes", [])],
            "environments": [_slug(x) for x in payload.get("environments", ["gym"])],
            "surfaces": [_slug(x) for x in payload.get("surfaces", [])],
            "accepted_dose_units": [_slug(x) for x in payload.get("accepted_dose_units", ["sets", "repetitions"])],
            "force_directions": [_slug(x) for x in payload.get("force_directions", [])],
            "contractions": [_slug(x) for x in payload.get("contractions", [])],
            "speed_intent": _slug(str(payload.get("speed_intent") or "controlled"))[:24],
            "joint_positions": {}, "level_minimum": _slug(str(payload.get("level_minimum") or "beginner")),
            "technical_cost": number("technical_cost", 2), "impact_cost": number("impact_cost", 2),
            "fatigue_cost": number("fatigue_cost", 2),
            "supervision_required": str(payload.get("supervision_required", "no")).lower() in {"yes", "true", "required"},
            "instructions": payload.get("instructions", []), "cues": payload.get("cues", []),
            "common_errors": payload.get("common_errors", []), "safety_boundaries": payload.get("safety_boundaries", []),
        }
        candidates.append(WorkbookCandidate(f"document-{index:04d}", payload, normalized, "retain", tuple(errors)))
    if not candidates:
        raise WorkbookImportError("no exercise sections found; use headings such as `## Exercise: Goblet Squat`")
    return hashlib.sha256(content).hexdigest(), candidates


def parse_exercise_csv(content: bytes) -> tuple[str, list[WorkbookCandidate]]:
    if not content or len(content) > MAX_DOCUMENT_BYTES:
        raise WorkbookImportError("CSV is empty or exceeds the 10 MB limit")
    try: text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc: raise WorkbookImportError("CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text))
    required = {"source_id", "exercise_name", "code", "type", "movement_pattern", "instructions", "coaching_cues", "common_mistakes", "safety_stop_conditions"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise WorkbookImportError(f"exercise CSV is missing required columns: {sorted(required - set(reader.fieldnames or []))}")
    candidates=[]; seen=set()
    for index, source in enumerate(reader,1):
        name=(source.get("exercise_name") or "").strip(); code=_slug(source.get("code") or name); errors=[]
        if not name: errors.append("missing exercise name")
        if code in seen: errors.append("duplicate code in CSV")
        seen.add(code)
        def items(key): return _split(source.get(key, ""))
        def number(key, default):
            try: return max(1,min(5,int(source.get(key) or default)))
            except ValueError: errors.append(f"invalid {key}"); return default
        normalized={"code":code,"canonical_name":name,"method_type":source.get("type") or "exercise","movement_pattern":_slug(source.get("movement_pattern") or "general")[:50],"aliases":items("aliases"),"primary_quality":_slug(source.get("primary_quality") or "maximum_strength"),"secondary_qualities":[_slug(x) for x in items("secondary_qualities")][:3],"training_role":source.get("training_role") or "accessory","equipment_codes":[_slug(x) for x in items("equipment")],"environments":[_slug(x) for x in items("environments")] or ["gym"],"surfaces":[],"accepted_dose_units":[_slug(x) for x in items("dose_units")] or ["sets","repetitions"],"force_directions":[],"contractions":[],"speed_intent":"controlled","joint_positions":{},"level_minimum":source.get("minimum_level") or "beginner","technical_cost":number("technical_cost",2),"impact_cost":number("impact_cost",2),"fatigue_cost":number("fatigue_cost",2),"supervision_required":str(source.get("supervision_required","")).lower() in {"yes","true","required"},"instructions":items("instructions"),"cues":items("coaching_cues"),"common_errors":items("common_mistakes"),"safety_boundaries":items("safety_stop_conditions"),"progression_codes":[_slug(x) for x in items("progressions")],"regression_codes":[_slug(x) for x in items("regressions")],"substitution_codes":[_slug(x) for x in items("substitutions")]}
        for field in ("instructions","cues","common_errors","safety_boundaries"):
            if not normalized[field]: errors.append(f"missing {field}")
        disposition="specialist" if source.get("catalogue_scope")=="specialist_only" else "retain"
        candidates.append(WorkbookCandidate(source.get("source_id") or f"csv-{index:04d}",source,normalized,disposition,tuple(errors)))
    if not candidates: raise WorkbookImportError("exercise CSV contains no rows")
    return hashlib.sha256(content).hexdigest(),candidates


@dataclass(frozen=True)
class WorkbookCandidate:
    source_reference: str
    source_payload: dict[str, Any]
    normalized_payload: dict[str, Any]
    disposition: str
    validation_errors: tuple[str, ...]


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if not letters:
        raise WorkbookImportError("invalid cell reference")
    result = 0
    for character in letters.group(0):
        result = result * 26 + ord(character) - 64
    return result - 1


def _safe_xml(archive: ZipFile, name: str):
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise WorkbookImportError(f"workbook is missing {name}") from exc
    if info.file_size > MAX_XML_ENTRY_BYTES:
        raise WorkbookImportError(f"workbook entry is too large: {name}")
    return ET.fromstring(archive.read(name))


def _split(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"\s*(?:;|\||,)\s*", value or "") if item.strip()]


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return result[:100] or "unnamed_method"


def _cost(value: str, *, default: int) -> int:
    return {"low": 1, "moderate": 3, "high": 5}.get((value or "").strip().lower(), default)


def _method_type(section: str, qualities: str) -> str:
    combined = f"{section} {qualities}".lower()
    if "conditioning" in combined:
        return "conditioning_modality"
    if "preparation" in combined or "mobility" in combined:
        return "preparation_drill"
    if "plyometric" in combined or "speed" in combined:
        return "athletic_drill"
    return "exercise"


def _movement_pattern(section: str, patterns: str) -> str:
    first = _split(patterns)
    if first:
        return _slug(first[0])[:50]
    return {
        "Lower Body Strength": "lower_body_strength",
        "Upper Body Strength": "upper_body_strength",
        "Trunk and Carries": "trunk_carry",
        "Power and Plyometrics": "plyometric",
        "Movement Preparation": "preparation",
        "Athletic Accessories": "capacity",
        "Conditioning Movements": "conditioning",
    }.get(section, "general")


def _dose_units(name: str, section: str, qualities: str) -> list[str]:
    combined = f"{name} {section} {qualities}".lower()
    if any(token in combined for token in ("isometric", "hold", "squeeze")):
        return ["sets", "duration_seconds", "effort_rpe", "recovery_seconds"]
    if any(token in combined for token in ("carry", "crawl", "sled", "run", "sprint")):
        return ["sets", "distance_m", "recovery_seconds"]
    if any(token in combined for token in ("jump", "hop", "bound", "throw", "plyometric")):
        return ["sets", "repetitions", "recovery_seconds"]
    return ["sets", "repetitions", "effort_rpe", "recovery_seconds"]


def _disposition(decision: str) -> str:
    normalized = (decision or "").strip().lower()
    if "duplicate" in normalized:
        return "merge_duplicate"
    if "specialist" in normalized:
        return "specialist"
    if normalized == "approved":
        return "retain"
    return "quarantine"


def parse_exercise_workbook(content: bytes) -> tuple[str, list[WorkbookCandidate]]:
    if not content or len(content) > MAX_WORKBOOK_BYTES:
        raise WorkbookImportError("workbook is empty or exceeds the 20 MB limit")
    digest = hashlib.sha256(content).hexdigest()
    try:
        archive = ZipFile(io.BytesIO(content))
    except BadZipFile as exc:
        raise WorkbookImportError("file is not a valid XLSX workbook") from exc
    with archive:
        shared_root = _safe_xml(archive, "xl/sharedStrings.xml")
        shared = ["".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t")) for item in shared_root.findall(f"{{{MAIN_NS}}}si")]
        workbook = _safe_xml(archive, "xl/workbook.xml")
        relationships = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in _safe_xml(archive, "xl/_rels/workbook.xml.rels")
        }
        target = None
        for sheet in workbook.find(f"{{{MAIN_NS}}}sheets") or []:
            if sheet.attrib.get("name") == "Curated Exercises":
                target = relationships.get(sheet.attrib.get(f"{{{REL_NS}}}id", ""))
                break
        if not target:
            raise WorkbookImportError("Curated Exercises sheet was not found")
        sheet_path = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
        worksheet = _safe_xml(archive, sheet_path)
        raw_rows: list[dict[int, str]] = []
        for row in worksheet.findall(f".//{{{MAIN_NS}}}sheetData/{{{MAIN_NS}}}row"):
            values: dict[int, str] = {}
            for cell in row.findall(f"{{{MAIN_NS}}}c"):
                value_node = cell.find(f"{{{MAIN_NS}}}v")
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
                values[_column_index(cell.attrib["r"])] = value.strip()
            raw_rows.append(values)
    if len(raw_rows) < 5:
        raise WorkbookImportError("Curated Exercises contains no data rows")
    header_row = raw_rows[3]
    headers = [header_row.get(index, "") for index in range(max(header_row) + 1)]
    required = {"Review ID", "Exercise Name", "S&C Review Decision", "Section"}
    if not required.issubset(headers):
        raise WorkbookImportError("Curated Exercises is missing required columns")

    candidates: list[WorkbookCandidate] = []
    seen_references: set[str] = set()
    seen_names: set[str] = set()
    for row in raw_rows[4:]:
        source = {headers[index]: row.get(index, "") for index in range(len(headers))}
        reference = source["Review ID"]
        name = source["Exercise Name"]
        if not reference and not name:
            continue
        errors: list[str] = []
        if not reference:
            errors.append("missing Review ID")
        elif reference in seen_references:
            errors.append("duplicate Review ID")
        if not name:
            errors.append("missing exercise name")
        normalized_name = name.casefold()
        if normalized_name in seen_names:
            errors.append("duplicate normalized exercise name")
        seen_references.add(reference)
        seen_names.add(normalized_name)
        disposition = _disposition(source.get("S&C Review Decision", ""))
        normalized = {
            "code": _slug(name),
            "canonical_name": name,
            "method_type": _method_type(source.get("Section", ""), source.get("Training Qualities", "")),
            "movement_pattern": _movement_pattern(source.get("Section", ""), source.get("Movement Patterns", "")),
            "equipment_codes": [_slug(value) for value in _split(source.get("Equipment", "")) if value.lower() not in {"none", "bodyweight"}],
            "environments": [_slug(value) for value in _split(source.get("Environments", ""))],
            "surfaces": [],
            "accepted_dose_units": _dose_units(name, source.get("Section", ""), source.get("Training Qualities", "")),
            "force_directions": [],
            "contractions": ["isometric"] if any(token in f"{name} {source.get('Training Qualities', '')}".lower() for token in ("isometric", "hold", "squeeze")) else ["concentric", "eccentric"],
            "speed_intent": "explosive" if source.get("Section") == "Power and Plyometrics" else "controlled",
            "joint_positions": {},
            "level_minimum": source.get("Difficulty", "Beginner").lower(),
            "technical_cost": _cost(source.get("Technical Complexity", ""), default=2),
            "impact_cost": _cost(source.get("Impact", ""), default=1),
            "fatigue_cost": 3 if source.get("Proposed Role") == "Core" else 2,
            "supervision_required": source.get("Supervision", "").lower() == "required",
            "instructions": _split(source.get("Coaching Cues — Research Notes", "")),
            "cues": _split(source.get("Coaching Cues — Research Notes", "")),
            "common_errors": _split(source.get("Common Mistakes — Research Notes", "")),
            "safety_boundaries": _split(source.get("Safety / Avoid — Research Notes", "")),
            "source_training_qualities": _split(source.get("Training Qualities", "")),
            "source_progressions": _split(source.get("Progressions", "")),
            "source_regressions": _split(source.get("Regressions", "")),
            "source_substitutions": _split(source.get("Substitutions", "")),
        }
        for field in ("instructions", "cues", "common_errors", "safety_boundaries"):
            if not normalized[field]:
                errors.append(f"missing {field}")
        candidates.append(WorkbookCandidate(reference, source, normalized, disposition, tuple(errors)))
    if len(candidates) != 175:
        raise WorkbookImportError(f"expected 175 curated rows, found {len(candidates)}")
    counts = {value: sum(candidate.disposition == value for candidate in candidates) for value in {candidate.disposition for candidate in candidates}}
    if counts.get("retain") != 172 or counts.get("merge_duplicate") != 2 or counts.get("specialist") != 1:
        raise WorkbookImportError(f"workbook decisions do not reconcile: {counts}")
    return digest, candidates


async def preview_import(session: AsyncSession, *, filename: str, content: bytes) -> SourceImport:
    suffix=filename.lower().rsplit(".",1)[-1]
    document=suffix in {"md","docx"}
    digest,candidates = parse_exercise_document(filename,content) if document else parse_exercise_csv(content) if suffix=="csv" else parse_exercise_workbook(content)
    # Version the parser contract so a file previously committed by the
    # prototype importer can be safely previewed again after upsert fixes.
    source_type = "exercise_document_v2" if document else "exercise_csv_v2" if suffix=="csv" else "exercise_workbook_v2"
    existing = await session.scalar(select(SourceImport).where(SourceImport.source_type == source_type, SourceImport.content_hash == digest))
    if existing:
        return existing
    current = (await session.execute(select(Method.code, MethodVersion.canonical_name).join(
        MethodVersion,
        (MethodVersion.method_id == Method.id) & (MethodVersion.content_version == Method.latest_version),
    ))).all()
    code_by_name = {name.casefold(): code for code, name in current}
    existing_codes = {code for code, _ in current}
    normalized_candidates = []
    create_count = update_count = 0
    for item in candidates:
        code = item.normalized_payload["code"]
        name_code = code_by_name.get(item.normalized_payload["canonical_name"].casefold())
        errors = item.validation_errors
        if name_code is not None and name_code != code:
            errors += (f"exercise name already belongs to code {name_code}",)
        if code in existing_codes:
            update_count += 1
        else:
            create_count += 1
        normalized_candidates.append(WorkbookCandidate(item.source_reference, item.source_payload, item.normalized_payload, item.disposition, errors))
    candidates = normalized_candidates
    row = SourceImport(
        source_type=source_type,
        source_name=filename,
        content_hash=digest,
        status="previewed",
        row_count=len(candidates),
        summary_json={
            "retain": sum(item.disposition == "retain" for item in candidates),
            "merge_duplicate": sum(item.disposition == "merge_duplicate" for item in candidates),
            "specialist": sum(item.disposition == "specialist" for item in candidates),
            "rows_with_errors": sum(bool(item.validation_errors) for item in candidates),
            "creates": create_count,
            "updates": update_count,
        },
    )
    session.add(row)
    await session.flush()
    session.add_all(
        SourceImportRow(
            source_import_id=row.id,
            source_reference=item.source_reference,
            source_payload=item.source_payload,
            normalized_payload=item.normalized_payload,
            disposition=item.disposition,
            validation_errors=list(item.validation_errors),
        )
        for item in candidates
    )
    await session.commit()
    return row


async def commit_import(session: AsyncSession, source_import: SourceImport, actor_user_id: UUID) -> dict[str, int]:
    if source_import.status == "committed":
        return dict(source_import.summary_json)
    if source_import.status != "previewed":
        raise WorkbookImportError("only a previewed import can be committed")
    rows = (await session.scalars(select(SourceImportRow).where(SourceImportRow.source_import_id == source_import.id).order_by(SourceImportRow.source_reference).with_for_update())).all()
    now = datetime.now(timezone.utc)
    evidence_source = await session.scalar(select(EvidenceSource).where(EvidenceSource.canonical_locator == f"runlete://source-import/{source_import.content_hash}"))
    if evidence_source is None:
        evidence_source = EvidenceSource(title=f"Runlete curated exercise catalogue: {source_import.source_name}", canonical_locator=f"runlete://source-import/{source_import.content_hash}", source_tier=5, population="Athletes aged 16+", context="Internal catalogue classification", limitations="Not expert or medical approval; sport-package evidence review remains separate.")
        session.add(evidence_source); await session.flush()
    claim_code=f"catalogue_import_{source_import.content_hash[:20]}"
    claim=await session.scalar(select(EvidenceClaim).where(EvidenceClaim.code==claim_code))
    if claim is None:
        claim=EvidenceClaim(code=claim_code,latest_version=1);session.add(claim);await session.flush()
        session.add(EvidenceClaimVersion(claim_id=claim.id,claim_version=1,statement="The imported Runlete catalogue assigns these physical-quality effects to the listed exercises.",claim_type="catalogue_classification",implication_type="practitioner_inference",population="Athletes aged 16+",context="Internal method classification",confidence=0.5,limitations="Not a substitute for claim-level scientific or expert review.",status="draft",created_at=now,updated_at=now,record_version=1))
        # The source link has a composite FK to the claim version. Flush the
        # parent explicitly because these models intentionally have no ORM
        # relationship from which SQLAlchemy could infer insert ordering.
        await session.flush()
        session.add(EvidenceClaimSource(claim_id=claim.id,claim_version=1,source_id=evidence_source.id,support_type="provenance",locator=source_import.source_name))
    existing_by_code = {row.code: row for row in (await session.scalars(select(Method).with_for_update())).all()}
    required_quality_codes: set[str] = set()
    for item in rows:
        payload=item.normalized_payload or {}
        if item.validation_errors or item.disposition=="merge_duplicate": continue
        required_quality_codes.update([payload.get("primary_quality") or "general_strength", *payload.get("secondary_qualities", [])])
    quality_by_code={item.code:item for item in (await session.scalars(select(PhysicalQuality).where(PhysicalQuality.code.in_(required_quality_codes)))).all()}
    for quality_code in required_quality_codes-quality_by_code.keys():
        quality=PhysicalQuality(code=quality_code,name=quality_code.replace("_"," ").title(),category="imported_catalogue",description="Physical quality imported from the curated Runlete exercise catalogue.",status="draft")
        session.add(quality);quality_by_code[quality_code]=quality
    if required_quality_codes: await session.flush()
    alias_rows=(await session.execute(select(MethodAlias.method_id,MethodAlias.normalized_alias))).all()
    aliases_by_method: dict[UUID,set[str]] = {}
    for method_id,normalized_alias in alias_rows: aliases_by_method.setdefault(method_id,set()).add(normalized_alias)
    disposition_by_reference={item.source_reference:item for item in (await session.scalars(select(SourceDisposition).where(SourceDisposition.source_system==source_import.source_type).with_for_update())).all()}
    def record_disposition(source_row: SourceImportRow, disposition: str, reason: str, method: Method | None = None) -> None:
        item=disposition_by_reference.get(source_row.source_reference)
        source_name=(source_row.normalized_payload or {}).get("canonical_name") or source_row.source_payload.get("Exercise Name")
        if item is None:
            item=SourceDisposition(source_system=source_import.source_type,source_reference=source_row.source_reference,source_name=source_name,disposition=disposition,canonical_method_id=method.id if method else None,reason=reason)
            session.add(item);disposition_by_reference[source_row.source_reference]=item
        else:
            item.source_name=source_name;item.disposition=disposition;item.canonical_method_id=method.id if method else None;item.reason=reason;item.version+=1
    imported_methods: dict[str, Method] = {}
    imported_payloads: dict[str, dict[str, Any]] = {}
    # MethodEffect has a composite foreign key to MethodVersion, but these
    # models intentionally do not expose ORM relationships. SQLAlchemy cannot
    # therefore infer the required insert order when both are pending. Stage
    # effect values while building methods, flush every identity/version once,
    # and only then add the dependent effect rows.
    pending_effects: list[dict[str, Any]] = []
    for row in rows:
        payload = row.normalized_payload or {}
        if row.validation_errors:
            continue
        if row.disposition == "merge_duplicate":
            record_disposition(row,"merge_duplicate","Catalogue review rejected this row as a duplicate.")
            continue
        code = payload["code"]
        method = existing_by_code.get(code)
        if method is None:
            method = Method(id=uuid7(), code=code, latest_version=1, archived=False)
            session.add(method)
            content_version = 1
            existing_by_code[code] = method
        else:
            content_version = method.latest_version + 1
            method.latest_version = content_version
            method.archived = False
            method.version += 1
        version = MethodVersion(
            method_id=method.id,
            content_version=content_version,
            canonical_name=payload["canonical_name"],
            method_type=payload["method_type"],
            movement_pattern=payload["movement_pattern"],
            equipment_codes=payload["equipment_codes"],
            environments=payload["environments"],
            surfaces=payload["surfaces"],
            accepted_dose_units=payload["accepted_dose_units"],
            force_directions=payload["force_directions"],
            contractions=payload["contractions"],
            speed_intent=payload["speed_intent"],
            joint_positions=payload["joint_positions"],
            level_minimum=payload["level_minimum"],
            technical_cost=payload["technical_cost"],
            impact_cost=payload["impact_cost"],
            fatigue_cost=payload["fatigue_cost"],
            supervision_required=payload["supervision_required"] or row.disposition == "specialist",
            instructions=payload["instructions"],
            cues=payload["cues"],
            common_errors=payload["common_errors"],
            safety_boundaries=payload["safety_boundaries"],
            wording_original=True,
            status="catalogue_validated",
            generator_eligible=row.disposition != "specialist",
            created_at=now,
            updated_at=now,
            record_version=1,
        )
        session.add(version)
        session.add(ContentReview(entity_type="method",entity_id=method.id,entity_version=content_version,review_type="content",reviewer_user_id=actor_user_id,decision="approved",rationale="Catalogue content reviewed and approved by the Runlete founder for exercise-library use.",scope="Exercise identity, classification, instructions, cues, common mistakes, safety text and catalogue effects. This does not constitute scientific, medical or specialist approval.",decided_at=now))
        qualities=[payload.get("primary_quality") or "general_strength",*payload.get("secondary_qualities",[])][:4]
        for index,quality_code in enumerate(dict.fromkeys(qualities)):
            requested_role = payload.get("training_role") or "accessory"
            training_role = requested_role if requested_role in {"preparation", "primary", "accessory", "capacity", "recovery"} else "accessory"
            pending_effects.append({
                "method_id": method.id,
                "method_version": content_version,
                "quality_code": quality_code,
                "is_primary": index == 0,
                "training_role": training_role if index == 0 else "accessory",
                "magnitude": 0.8 if index == 0 else 0.5,
                "confidence": 0.5,
                "evidence_claim_id": claim.id,
                "evidence_claim_version": 1,
            })
        existing_aliases = aliases_by_method.setdefault(method.id,set())
        session.add_all(MethodAlias(method_id=method.id, alias=alias, normalized_alias=alias.strip().casefold()) for alias in payload.get("aliases", []) if alias.strip().casefold() not in existing_aliases)
        existing_aliases.update(alias.strip().casefold() for alias in payload.get("aliases", []))
        row.canonical_method_id = method.id
        record_disposition(row,row.disposition,"Imported as a catalogue-validated method; sport release eligibility remains a separate gate.",method)
        imported_methods[payload["code"]] = method
        imported_payloads[payload["code"]] = payload
    await session.flush()
    session.add_all(MethodEffect(**values) for values in pending_effects)
    # CSV relations use stable method codes. Persist progression direction as
    # lower -> higher; regressions therefore reverse their stored direction.
    all_methods = {row.code: row for row in (await session.scalars(select(Method))).all()}
    created_relations: set[tuple[UUID, UUID, str, str]] = {tuple(item) for item in (await session.execute(select(MethodRelation.from_method_id, MethodRelation.to_method_id, MethodRelation.relation_type, MethodRelation.objective_code))).all()}
    for source_code, payload in imported_payloads.items():
        source_method = imported_methods[source_code]
        objective = payload.get("primary_quality") or "maximum_strength"
        relations: set[tuple[str, str, str]] = set()
        relations.update((source_code, target, "progression") for target in payload.get("progression_codes", []))
        relations.update((target, source_code, "progression") for target in payload.get("regression_codes", []))
        relations.update((source_code, target, "substitution") for target in payload.get("substitution_codes", []))
        for from_code, to_code, relation_type in relations:
            from_method = all_methods.get(from_code)
            to_method = all_methods.get(to_code)
            if from_method is None or to_method is None or from_method.id == to_method.id:
                continue
            relation_key = (from_method.id, to_method.id, relation_type, objective)
            if relation_key in created_relations:
                continue
            created_relations.add(relation_key)
            session.add(MethodRelation(
                from_method_id=from_method.id,
                to_method_id=to_method.id,
                relation_type=relation_type,
                objective_code=objective,
                prerequisites_json={},
                rationale="Canonical relation imported from the normalized Runlete exercise catalogue.",
                status="catalogue_validated",
            ))
    source_import.status = "committed"
    source_import.committed_at = now
    source_import.committed_by = actor_user_id
    source_import.version += 1
    await session.commit()
    return dict(source_import.summary_json)
