from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.ids import uuid7

from .importer import WorkbookImportError
from .models import (
    CategoryLevelAvailability,
    Method,
    ScenarioOverlay,
    SourceImport,
    SourceImportRow,
    SportModePolicy,
    SportTemplatePriority,
    SportTemplatePriorityItem,
    TrainingModeFallback,
    TrainingReferenceMethod,
    TrainingReferenceTemplate,
    TrainingReferenceTemplateVersion,
    TrainingReferenceWeek,
)

DATASET_KINDS = {"training_templates", "sport_priority_matrix", "training_policies"}
MAX_DATASET_BYTES = 30 * 1024 * 1024


def _digest(files: list[tuple[str, bytes]]) -> str:
    value = hashlib.sha256()
    for name, content in sorted(files):
        value.update(name.encode("utf-8")); value.update(b"\0"); value.update(content); value.update(b"\0")
    return value.hexdigest()


def _json(name: str, content: bytes) -> dict[str, Any]:
    try:
        value = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkbookImportError(f"{name} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise WorkbookImportError(f"{name} must contain a JSON object")
    return value


def _parse_templates(files: list[tuple[str, bytes]]) -> list[tuple[str, dict[str, Any], list[str]]]:
    rows: list[tuple[str, dict[str, Any], list[str]]] = []
    seen: set[str] = set()
    phases: set[int] = set()
    for name, content in files:
        document = _json(name, content)
        if "templates" not in document: raise WorkbookImportError(f"{name} is not a phase template file")
        try: phases.add(int(document.get("phase")))
        except (TypeError, ValueError): raise WorkbookImportError(f"{name} has no valid research phase")
        for template in document.get("templates", []):
            code = str(template.get("template_code", "")).strip()
            errors: list[str] = []
            if not code: errors.append("missing template_code")
            if code in seen: errors.append("duplicate template_code in upload")
            seen.add(code)
            if template.get("duration_weeks") != 4: errors.append("duration_weeks must be 4")
            weeks = template.get("weeks") or []
            if [item.get("week") for item in weeks] != [1, 2, 3, 4]: errors.append("weeks must be exactly 1, 2, 3 and 4")
            methods = template.get("method_options") or []
            if not methods: errors.append("at least one method option is required")
            if len({item.get("method_code") for item in methods}) != len(methods): errors.append("duplicate method option")
            required = ("phase", "category_code", "name", "athlete_level", "purpose", "selection_policy", "selection_rules", "exercise_progression_policy", "week_4_policy", "mandatory_stops", "ai_use", "prompt_reference_text")
            errors.extend(f"missing {field}" for field in required if not template.get(field))
            for index, item in enumerate(methods, 1):
                if not item.get("method_code"): errors.append(f"method option {index} is missing method_code")
                if not item.get("block_role"): errors.append(f"method option {index} is missing block_role")
                if not item.get("applicable_modes"): errors.append(f"method option {index} is missing applicable_modes")
            for item in weeks:
                for field in ("intent", "sessions_per_week", "prescription_per_primary_method", "progression_condition", "regression_condition"):
                    if item.get(field) in (None, "", {}): errors.append(f"week {item.get('week')} is missing {field}")
            rows.append((code or f"row-{len(rows)+1}", template, errors))
    if not rows: raise WorkbookImportError("No four-week templates were found. Select the phase_01 through phase_09 JSON files.")
    if phases != set(range(1, 10)): raise WorkbookImportError(f"Select all nine phase files together; received phases {sorted(phases)}")
    return rows


def _parse_matrix(name: str, content: bytes) -> list[tuple[str, dict[str, Any], list[str]]]:
    try: reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    except UnicodeDecodeError as exc: raise WorkbookImportError("Priority matrix must be UTF-8 CSV") from exc
    required = {"sport_code", "scope_type", "scope_code", "phase_code", "goal_code", "primary_template_category", "session_block_order", "priority_basis"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise WorkbookImportError(f"Priority matrix is missing columns: {sorted(required-set(reader.fieldnames or []))}")
    rows=[]; seen=set()
    for number, source in enumerate(reader, 2):
        key = "|".join((source.get(field) or "").strip() for field in ("sport_code", "scope_type", "scope_code", "phase_code", "goal_code"))
        errors=[]
        if not all((source.get(field) or "").strip() for field in required): errors.append("one or more required values are empty")
        if key in seen: errors.append("duplicate sport/scope/phase/goal row")
        seen.add(key)
        priorities=[]
        for rank in range(1, 9):
            category=(source.get(f"rank_{rank}_category") or "").strip(); raw=(source.get(f"rank_{rank}_weight") or "").strip()
            if not category and not raw: continue
            try: weight=float(raw)
            except ValueError: errors.append(f"rank {rank} weight is invalid"); continue
            if not 0 <= weight <= 1: errors.append(f"rank {rank} weight must be between 0 and 1")
            priorities.append({"rank":rank,"category_code":category,"weight":weight})
        if not priorities: errors.append("at least one ranked category is required")
        payload={**source,"session_block_order":[item.strip() for item in (source.get("session_block_order") or "").split(";") if item.strip()],"priorities":priorities}
        rows.append((f"matrix-row-{number}",payload,errors))
    if not rows: raise WorkbookImportError(f"{name} contains no matrix rows")
    return rows


def _parse_policies(files: list[tuple[str, bytes]]) -> list[tuple[str, dict[str, Any], list[str]]]:
    rows=[]; found=set()
    for name, content in files:
        data=_json(name,content)
        if "records" in data:
            found.add("availability")
            for item in data["records"]: rows.append((f"availability:{item.get('category_code')}:{item.get('athlete_level')}",{"record_type":"availability",**item},[]))
        if "policies" in data:
            found.add("mode_policy")
            for item in data["policies"]: rows.append((f"mode:{item.get('sport_code')}",{"record_type":"mode_policy",**item},[]))
            for item in data.get("missing_mode_fallbacks",[]): rows.append((f"fallback:{item.get('category_code')}:{item.get('athlete_level')}:{item.get('requested_mode')}",{"record_type":"mode_fallback",**item},[]))
        if "overlays" in data:
            found.add("overlay")
            for item in data["overlays"]: rows.append((f"overlay:{item.get('code')}",{"record_type":"overlay",**item},[]))
    missing={"availability","mode_policy","overlay"}-found
    if missing: raise WorkbookImportError(f"Policy upload is incomplete; missing: {', '.join(sorted(missing))}")
    seen=set(); result=[]
    for reference,payload,errors in rows:
        if reference in seen: errors.append("duplicate policy record")
        seen.add(reference)
        if any(value in (None, "") for key,value in payload.items() if key not in {"template_code","prerequisite_category","implementation_note"}): errors.append("required policy value is empty")
        result.append((reference,payload,errors))
    return result


async def preview_dataset(session: AsyncSession, *, dataset_kind: str, files: list[tuple[str, bytes]]) -> SourceImport:
    if dataset_kind not in DATASET_KINDS: raise WorkbookImportError("unsupported dataset kind")
    if not files or sum(len(content) for _,content in files) > MAX_DATASET_BYTES: raise WorkbookImportError("dataset is empty or exceeds 30 MB")
    digest=_digest(files)
    existing=await session.scalar(select(SourceImport).where(SourceImport.source_type==dataset_kind,SourceImport.content_hash==digest))
    if existing: return existing
    if dataset_kind=="training_templates": parsed=_parse_templates(files)
    elif dataset_kind=="sport_priority_matrix":
        if len(files)!=1: raise WorkbookImportError("select exactly one priority-matrix CSV")
        parsed=_parse_matrix(*files[0])
    else: parsed=_parse_policies(files)
    if dataset_kind=="training_templates":
        method_codes=set((await session.scalars(select(Method.code))).all())
        parsed=[(ref,payload,errors+[f"unknown method code: {code}" for code in {item.get('method_code') for item in payload.get('method_options',[])}-method_codes]) for ref,payload,errors in parsed]
    elif dataset_kind=="sport_priority_matrix":
        categories=set((await session.scalars(select(TrainingReferenceTemplateVersion.category_code).join(TrainingReferenceTemplate,TrainingReferenceTemplate.id==TrainingReferenceTemplateVersion.template_id).where(TrainingReferenceTemplate.latest_version==TrainingReferenceTemplateVersion.content_version))).all())
        parsed=[(ref,payload,errors+[f"unknown template category: {code}" for code in ({payload.get('primary_template_category')}|{item['category_code'] for item in payload.get('priorities',[])})-categories]) for ref,payload,errors in parsed]
    elif dataset_kind=="training_policies":
        template_codes=set((await session.scalars(select(TrainingReferenceTemplate.code))).all())
        parsed=[(ref,payload,errors+([f"unknown template code: {payload.get('template_code')}"] if payload.get("record_type")=="availability" and payload.get("available") and payload.get("template_code") not in template_codes else [])) for ref,payload,errors in parsed]
    summary={"rows":len(parsed),"valid":sum(not errors for _,_,errors in parsed),"errors":sum(bool(errors) for _,_,errors in parsed)}
    if dataset_kind=="training_templates": summary["templates"]=len(parsed)
    if dataset_kind=="sport_priority_matrix": summary["matrix_rows"]=len(parsed)
    source_name=", ".join(name for name,_ in files)
    if len(source_name)>230: source_name=f"{len(files)} files: {files[0][0]} … {files[-1][0]}"
    row=SourceImport(source_type=dataset_kind,source_name=source_name,content_hash=digest,status="previewed",row_count=len(parsed),summary_json=summary)
    session.add(row); await session.flush()
    session.add_all(SourceImportRow(source_import_id=row.id,source_reference=ref,source_payload=payload,normalized_payload=payload,disposition="retain" if not errors else "quarantine",validation_errors=errors) for ref,payload,errors in parsed)
    await session.commit(); return row


async def _commit_templates(session: AsyncSession, source: SourceImport, rows: list[SourceImportRow], now: datetime) -> dict[str,int]:
    by_code={item.code:item for item in (await session.scalars(select(Method))).all()}
    identities={item.code:item for item in (await session.scalars(select(TrainingReferenceTemplate).with_for_update())).all()}
    created=updated=0
    pending_methods: list[dict[str, Any]]=[]
    pending_weeks: list[dict[str, Any]]=[]
    for source_row in rows:
        payload=source_row.normalized_payload or {}; code=payload["template_code"]
        identity=identities.get(code)
        if identity is None:
            identity=TrainingReferenceTemplate(id=uuid7(),code=code,latest_version=1);session.add(identity);identities[code]=identity;version=1;created+=1
        else:
            version=identity.latest_version+1;identity.latest_version=version;identity.version+=1;updated+=1
        session.add(TrainingReferenceTemplateVersion(template_id=identity.id,content_version=version,research_phase=int(payload["phase"]),category_code=payload["category_code"],name=payload["name"],athlete_level=payload["athlete_level"],duration_weeks=int(payload["duration_weeks"]),purpose=payload["purpose"],source_template_ids=payload.get("source_template_ids",[]),applicable_scenarios=payload.get("applicable_scenarios",[]),selection_policy_json=payload["selection_policy"],selection_rules_json=payload["selection_rules"],exercise_progression_policy=payload["exercise_progression_policy"],week_4_policy=payload["week_4_policy"],mandatory_stops=payload.get("mandatory_stops",[]),ai_use=payload["ai_use"],prompt_reference_text=payload["prompt_reference_text"],status=payload.get("status","research_derived_candidate"),source_hash=source.content_hash,created_at=now,updated_at=now,record_version=1))
        for sequence,item in enumerate(payload["method_options"],1):
            method=by_code[item["method_code"]]
            pending_methods.append({"id":uuid7(),"template_id":identity.id,"template_version":version,"sequence":sequence,"method_id":method.id,"method_version":method.latest_version,"block_role":item["block_role"],"applicable_modes":item.get("applicable_modes",[]),"implementation_note":item.get("implementation_note", "")})
        for item in payload["weeks"]:
            pending_weeks.append({"id":uuid7(),"template_id":identity.id,"template_version":version,"week_number":int(item["week"]),"intent":item["intent"],"sessions_per_week":str(item["sessions_per_week"]),"prescription_json":item["prescription_per_primary_method"],"progression_condition":item["progression_condition"],"regression_condition":item["regression_condition"]})
    # The method/week rows reference a composite template-version key. Flush
    # all stable identities and immutable versions first, then add dependants
    # in one batch to preserve FK ordering without per-template round trips.
    await session.flush()
    session.add_all(TrainingReferenceMethod(**values) for values in pending_methods)
    session.add_all(TrainingReferenceWeek(**values) for values in pending_weeks)
    return {"created":created,"updated":updated}


async def _commit_matrix(session: AsyncSession, source: SourceImport, rows: list[SourceImportRow]) -> dict[str,int]:
    existing={(item.sport_code,item.scope_type,item.scope_code,item.phase_code,item.goal_code):item for item in (await session.scalars(select(SportTemplatePriority).with_for_update())).all()}
    retained=set();created=updated=0
    for source_row in rows:
        p=source_row.normalized_payload or {}
        key=(p["sport_code"],p["scope_type"],p["scope_code"],p["phase_code"],p["goal_code"]);retained.add(key)
        row=existing.get(key)
        if row is None:
            row=SportTemplatePriority(id=uuid7(),sport_code=p["sport_code"],scope_type=p["scope_type"],scope_code=p["scope_code"],phase_code=p["phase_code"],goal_code=p["goal_code"],primary_template_category=p["primary_template_category"],session_block_order=p["session_block_order"],priority_basis=p["priority_basis"],source_hash=source.content_hash);session.add(row);created+=1
        else:
            row.primary_template_category=p["primary_template_category"];row.session_block_order=p["session_block_order"];row.priority_basis=p["priority_basis"];row.source_hash=source.content_hash;row.version+=1;updated+=1
            await session.execute(delete(SportTemplatePriorityItem).where(SportTemplatePriorityItem.priority_id==row.id))
        session.add_all(SportTemplatePriorityItem(id=uuid7(),priority_id=row.id,rank=item["rank"],category_code=item["category_code"],weight=item["weight"]) for item in p["priorities"])
    stale=[item.id for key,item in existing.items() if key not in retained]
    if stale: await session.execute(delete(SportTemplatePriority).where(SportTemplatePriority.id.in_(stale)))
    return {"created":created,"updated":updated,"retired_missing":len(stale)}


async def _commit_policies(session: AsyncSession, source: SourceImport, rows: list[SourceImportRow]) -> dict[str,int]:
    counts={"availability":0,"mode_policy":0,"mode_fallback":0,"overlay":0}
    availability={(x.category_code,x.athlete_level):x for x in (await session.scalars(select(CategoryLevelAvailability).with_for_update())).all()}
    modes={x.sport_code:x for x in (await session.scalars(select(SportModePolicy).with_for_update())).all()}
    fallbacks={(x.category_code,x.athlete_level,x.requested_mode):x for x in (await session.scalars(select(TrainingModeFallback).with_for_update())).all()}
    overlays={x.code:x for x in (await session.scalars(select(ScenarioOverlay).with_for_update())).all()}
    retained={"availability":set(),"mode_policy":set(),"mode_fallback":set(),"overlay":set()}
    for source_row in rows:
        p=source_row.normalized_payload or {}; kind=p["record_type"]
        if kind=="availability":
            key=(p["category_code"],p["athlete_level"]);retained[kind].add(key);item=availability.get(key)
            values={"available":p["available"],"template_code":p.get("template_code"),"prerequisite_category":p.get("prerequisite_category"),"reason":p["reason"],"source_hash":source.content_hash}
            if item is None: session.add(CategoryLevelAvailability(category_code=key[0],athlete_level=key[1],**values))
            else:
                for field,value in values.items(): setattr(item,field,value)
                item.version+=1
        elif kind=="mode_policy":
            key=p["sport_code"];retained[kind].add(key);item=modes.get(key);values={"primary_mode":p["primary_mode"],"cross_training_requires_opt_in":p["cross_training_requires_opt_in"],"source_hash":source.content_hash}
            if item is None: session.add(SportModePolicy(sport_code=key,**values))
            else:
                for field,value in values.items(): setattr(item,field,value)
                item.version+=1
        elif kind=="mode_fallback":
            key=(p["category_code"],p["athlete_level"],p["requested_mode"]);retained[kind].add(key);item=fallbacks.get(key);values={"fallback_category":p["fallback_category"],"automatic":p["automatic"],"source_hash":source.content_hash}
            if item is None: session.add(TrainingModeFallback(category_code=key[0],athlete_level=key[1],requested_mode=key[2],**values))
            else:
                for field,value in values.items(): setattr(item,field,value)
                item.version+=1
        else:
            key=p["code"];retained[kind].add(key);item=overlays.get(key);values={"applies_to":p["applies_to"],"instruction":p["instruction"],"source_hash":source.content_hash}
            if item is None: session.add(ScenarioOverlay(code=key,**values))
            else:
                for field,value in values.items(): setattr(item,field,value)
                item.version+=1
        counts[kind]+=1
    for kind,model,items in (("availability",CategoryLevelAvailability,availability),("mode_policy",SportModePolicy,modes),("mode_fallback",TrainingModeFallback,fallbacks),("overlay",ScenarioOverlay,overlays)):
        stale=[item.id for key,item in items.items() if key not in retained[kind]]
        if stale: await session.execute(delete(model).where(model.id.in_(stale)))
    return counts


async def commit_dataset(session: AsyncSession, source: SourceImport, actor_user_id: UUID) -> dict[str,Any]:
    if source.status=="committed": return dict(source.summary_json)
    if source.status!="previewed": raise WorkbookImportError("only a previewed dataset can be committed")
    rows=(await session.scalars(select(SourceImportRow).where(SourceImportRow.source_import_id==source.id).order_by(SourceImportRow.source_reference).with_for_update())).all()
    invalid=sum(bool(row.validation_errors) for row in rows)
    if invalid: raise WorkbookImportError(f"commit blocked: {invalid} rows failed validation")
    now=datetime.now(timezone.utc)
    if source.source_type=="training_templates": result=await _commit_templates(session,source,rows,now)
    elif source.source_type=="sport_priority_matrix": result=await _commit_matrix(session,source,rows)
    elif source.source_type=="training_policies": result=await _commit_policies(session,source,rows)
    else: raise WorkbookImportError("this import is not a structured training dataset")
    source.status="committed";source.committed_at=now;source.committed_by=actor_user_id;source.version+=1;source.summary_json={**source.summary_json,**result}
    await session.commit();return dict(source.summary_json)
