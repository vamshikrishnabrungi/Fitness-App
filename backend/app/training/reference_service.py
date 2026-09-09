"""Database adapter for released sport priorities, templates, and methods."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.athletes.models import (
    AthleteGoal,
    AthleteMethodFamiliarity,
    AthleteProfile,
    AthleteSport,
    AvailabilityWindow,
    EquipmentAccess,
    ExternalLoad,
)
from backend.app.health.models import DailyCheckIn, PainReport
from backend.app.knowledge.models import (
    ContentRelease,
    Method,
    MethodVersion,
    PhaseDosePolicy,
    SportModePolicy,
    SportTemplatePriority,
    SportTemplatePriorityItem,
    TrainingReferenceMethod,
    TrainingReferenceTemplate,
    TrainingReferenceTemplateVersion,
    TrainingReferenceWeek,
)
from backend.app.knowledge.training_contract import athlete_level, normalize_goal, normalize_phase, sport_scope_key
from backend.app.training.reference_compiler import (
    AvailabilitySlot,
    CompilerContext,
    PhasePolicy,
    PriorityContext,
    RankedCategory,
    ReferenceCompilationError,
    ReferenceMethod,
    ReferenceTemplate,
    ReferenceWeek,
)
from backend.app.training.reference_prescription import normalize_reference_prescription


def _hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


async def _verify_release_source_hashes(session: AsyncSession, release: ContentRelease) -> None:
    """Fail closed if live generator rows no longer match the published manifest.

    Import groups stamp every live row with their committed source hash. One
    query compares min/max hashes for all generator tables with the hashes
    captured by the active content release, preventing a plan from pinning an
    old release while a newer import is only partially applied.
    """
    expected = (release.validation_summary or {}).get("source_hashes", {})
    required = {
        "exercise_csv_v2", "training_templates", "sport_priority_matrix", "training_policies",
    }
    if not required <= set(expected):
        raise ReferenceCompilationError("released training-reference manifest lacks source hashes")

    method_scope = (
        MethodVersion.content_version == Method.latest_version,
        MethodVersion.status == "released",
    )
    template_scope = (
        TrainingReferenceTemplateVersion.content_version == TrainingReferenceTemplate.latest_version,
        TrainingReferenceTemplateVersion.status == "released",
    )
    expressions = {
        "method_min": select(func.min(MethodVersion.source_hash)).join(Method).where(*method_scope).scalar_subquery(),
        "method_max": select(func.max(MethodVersion.source_hash)).join(Method).where(*method_scope).scalar_subquery(),
        "template_min": select(func.min(TrainingReferenceTemplateVersion.source_hash)).join(TrainingReferenceTemplate).where(*template_scope).scalar_subquery(),
        "template_max": select(func.max(TrainingReferenceTemplateVersion.source_hash)).join(TrainingReferenceTemplate).where(*template_scope).scalar_subquery(),
        "priority_min": select(func.min(SportTemplatePriority.source_hash)).scalar_subquery(),
        "priority_max": select(func.max(SportTemplatePriority.source_hash)).scalar_subquery(),
    }
    for name, model in (
        ("mode", SportModePolicy),
        ("phase", PhaseDosePolicy),
    ):
        expressions[f"{name}_min"] = select(func.min(model.source_hash)).scalar_subquery()
        expressions[f"{name}_max"] = select(func.max(model.source_hash)).scalar_subquery()
    row = (await session.execute(select(*[value.label(key) for key, value in expressions.items()]))).mappings().one()
    groups = {
        "exercise_csv_v2": ("method",),
        "training_templates": ("template",),
        "sport_priority_matrix": ("priority",),
        "training_policies": ("mode", "phase"),
    }
    mismatches = [
        group
        for group, prefixes in groups.items()
        if any(row[f"{prefix}_min"] != expected[group] or row[f"{prefix}_max"] != expected[group] for prefix in prefixes)
    ]
    if mismatches:
        raise ReferenceCompilationError(
            "released training-reference manifest does not match live source groups: "
            + ", ".join(sorted(mismatches))
        )


async def _dataset_hash(session: AsyncSession) -> str:
    """Hash the semantic generator dataset without environment-local IDs.

    UUIDs and timestamps are intentionally excluded: importing the same
    versioned source into two clean databases must produce the same hash.
    Every field consumed by the AI candidate adapter is included so an in-place
    data change invalidates prior plan inputs.
    """
    template_rows = (await session.execute(
        select(
            TrainingReferenceTemplate.code,
            TrainingReferenceTemplateVersion.category_code,
            TrainingReferenceTemplateVersion.athlete_level,
            TrainingReferenceTemplateVersion.duration_weeks,
            TrainingReferenceTemplateVersion.purpose,
            TrainingReferenceTemplateVersion.selection_policy_json,
            TrainingReferenceTemplateVersion.selection_rules_json,
            TrainingReferenceTemplateVersion.exercise_progression_policy,
            TrainingReferenceTemplateVersion.week_4_policy,
            TrainingReferenceTemplateVersion.mandatory_stops,
            TrainingReferenceTemplateVersion.status,
            TrainingReferenceTemplateVersion.source_hash,
        )
        .join(TrainingReferenceTemplate, TrainingReferenceTemplate.id == TrainingReferenceTemplateVersion.template_id)
        .where(
            TrainingReferenceTemplateVersion.content_version == TrainingReferenceTemplate.latest_version,
            TrainingReferenceTemplateVersion.status == "released",
        )
        .order_by(TrainingReferenceTemplate.code)
    )).all()
    method_rows = (await session.execute(
        select(
            Method.code,
            MethodVersion.canonical_name,
            MethodVersion.method_type,
            MethodVersion.movement_pattern,
            MethodVersion.equipment_codes,
            MethodVersion.environments,
            MethodVersion.surfaces,
            MethodVersion.accepted_dose_units,
            MethodVersion.force_directions,
            MethodVersion.contractions,
            MethodVersion.speed_intent,
            MethodVersion.level_minimum,
            MethodVersion.technical_cost,
            MethodVersion.impact_cost,
            MethodVersion.fatigue_cost,
            MethodVersion.supervision_required,
            MethodVersion.instructions,
            MethodVersion.cues,
            MethodVersion.common_errors,
            MethodVersion.safety_boundaries,
            MethodVersion.source_hash,
            MethodVersion.status,
            MethodVersion.generator_eligible,
        )
        .join(MethodVersion, MethodVersion.method_id == Method.id)
        .join(TrainingReferenceMethod, and_(
            TrainingReferenceMethod.method_id == MethodVersion.method_id,
            TrainingReferenceMethod.method_version == MethodVersion.content_version,
        ))
        .join(TrainingReferenceTemplate, TrainingReferenceTemplate.id == TrainingReferenceMethod.template_id)
        .join(TrainingReferenceTemplateVersion, and_(
            TrainingReferenceTemplateVersion.template_id == TrainingReferenceMethod.template_id,
            TrainingReferenceTemplateVersion.content_version == TrainingReferenceMethod.template_version,
        ))
        .where(
            TrainingReferenceMethod.template_version == TrainingReferenceTemplate.latest_version,
            TrainingReferenceTemplateVersion.status == "released",
        )
        .where(MethodVersion.generator_eligible.is_(True), MethodVersion.status == "released")
        .distinct()
        .order_by(Method.code)
    )).all()
    method_links = (await session.execute(
        select(
            TrainingReferenceTemplate.code,
            TrainingReferenceMethod.sequence,
            Method.code,
            TrainingReferenceMethod.block_role,
            TrainingReferenceMethod.applicable_modes,
            TrainingReferenceMethod.sport_codes,
            TrainingReferenceMethod.scope_codes,
        )
        .join(TrainingReferenceTemplate, TrainingReferenceTemplate.id == TrainingReferenceMethod.template_id)
        .join(Method, Method.id == TrainingReferenceMethod.method_id)
        .join(TrainingReferenceTemplateVersion, and_(
            TrainingReferenceTemplateVersion.template_id == TrainingReferenceMethod.template_id,
            TrainingReferenceTemplateVersion.content_version == TrainingReferenceMethod.template_version,
        ))
        .where(
            TrainingReferenceMethod.template_version == TrainingReferenceTemplate.latest_version,
            TrainingReferenceTemplateVersion.status == "released",
        )
        .order_by(TrainingReferenceTemplate.code, TrainingReferenceMethod.sequence)
    )).all()
    week_rows = (await session.execute(
        select(
            TrainingReferenceTemplate.code,
            TrainingReferenceWeek.week_number,
            TrainingReferenceWeek.intent,
            TrainingReferenceWeek.sessions_per_week,
            TrainingReferenceWeek.prescription_json,
            TrainingReferenceWeek.progression_condition,
            TrainingReferenceWeek.regression_condition,
        )
        .join(TrainingReferenceTemplate, TrainingReferenceTemplate.id == TrainingReferenceWeek.template_id)
        .join(TrainingReferenceTemplateVersion, and_(
            TrainingReferenceTemplateVersion.template_id == TrainingReferenceWeek.template_id,
            TrainingReferenceTemplateVersion.content_version == TrainingReferenceWeek.template_version,
        ))
        .where(
            TrainingReferenceWeek.template_version == TrainingReferenceTemplate.latest_version,
            TrainingReferenceTemplateVersion.status == "released",
        )
        .order_by(TrainingReferenceTemplate.code, TrainingReferenceWeek.week_number)
    )).all()
    mode_rows = (await session.execute(select(
        SportModePolicy.sport_code,
        SportModePolicy.primary_mode,
        SportModePolicy.cross_training_requires_opt_in,
        SportModePolicy.source_hash,
    ).order_by(SportModePolicy.sport_code))).all()
    phase_policy_rows = (await session.execute(select(
        PhaseDosePolicy.phase_code,
        PhaseDosePolicy.policy_version,
        PhaseDosePolicy.progression_mode,
        PhaseDosePolicy.maximum_categories,
        PhaseDosePolicy.maximum_sessions_per_week,
        PhaseDosePolicy.weekly_volume_multipliers,
        PhaseDosePolicy.novelty_policy,
        PhaseDosePolicy.policy_basis,
        PhaseDosePolicy.source_hash,
    ).order_by(PhaseDosePolicy.phase_code))).all()
    priority_rows = (await session.execute(
        select(
            SportTemplatePriority.sport_code,
            SportTemplatePriority.scope_type,
            SportTemplatePriority.scope_code,
            SportTemplatePriority.phase_code,
            SportTemplatePriority.goal_code,
            SportTemplatePriority.primary_template_category,
            SportTemplatePriority.session_block_order,
            SportTemplatePriority.priority_basis,
            SportTemplatePriority.source_hash,
            SportTemplatePriorityItem.rank,
            SportTemplatePriorityItem.category_code,
            SportTemplatePriorityItem.weight,
        )
        .join(SportTemplatePriorityItem, SportTemplatePriorityItem.priority_id == SportTemplatePriority.id)
        .order_by(
            SportTemplatePriority.sport_code,
            SportTemplatePriority.scope_type,
            SportTemplatePriority.scope_code,
            SportTemplatePriority.phase_code,
            SportTemplatePriority.goal_code,
            SportTemplatePriorityItem.rank,
        )
    )).all()
    return _hash({
        "templates": [tuple(row) for row in template_rows],
        "methods": [tuple(row) for row in method_rows],
        "template_methods": [tuple(row) for row in method_links],
        "template_weeks": [tuple(row) for row in week_rows],
        "modes": [tuple(row) for row in mode_rows],
        "phase_policies": [tuple(row) for row in phase_policy_rows],
        "priorities": [tuple(row) for row in priority_rows],
    })


def _external_dates(
    rows: tuple[ExternalLoad, ...],
    *,
    starts_on: date,
    zone: ZoneInfo,
    hard_only: bool,
    horizon_weeks: int = 4,
) -> frozenset[date]:
    """Expand supported external-load recurrence over the plan horizon.

    One-time entries affect only their real local date. The only recurring
    contract is an explicit weekly rule with an optional positive
    ``interval_weeks`` and ISO ``until`` date. Unknown recurrence shapes fail
    closed instead of being silently interpreted as weekly forever.
    """
    horizon_start = starts_on - timedelta(days=1)
    horizon_end = starts_on + timedelta(weeks=horizon_weeks)
    matched_dates: set[date] = set()
    for row in rows:
        include = not hard_only or row.intensity in {"hard", "high", "maximal"}
        first = row.starts_at.astimezone(zone).date()
        recurrence = row.recurrence_json
        if recurrence is None:
            if include and horizon_start <= first <= horizon_end:
                matched_dates.add(first)
            continue
        if not isinstance(recurrence, dict) or set(recurrence) - {"frequency", "interval_weeks", "until"}:
            raise ReferenceCompilationError("external load recurrence contains unsupported fields")
        if recurrence.get("frequency") != "weekly":
            raise ReferenceCompilationError("external load recurrence must use frequency=weekly")
        interval = recurrence.get("interval_weeks", 1)
        if not isinstance(interval, int) or isinstance(interval, bool) or not 1 <= interval <= 12:
            raise ReferenceCompilationError("external load interval_weeks must be an integer from 1 to 12")
        until_value = recurrence.get("until")
        try:
            until = date.fromisoformat(until_value) if until_value else horizon_end
        except (TypeError, ValueError) as exc:
            raise ReferenceCompilationError("external load recurrence until must be an ISO date") from exc
        occurrence = first
        step = timedelta(weeks=interval)
        if occurrence < horizon_start:
            jumps = max(0, (horizon_start - occurrence).days // step.days)
            occurrence += step * jumps
            while occurrence < horizon_start:
                occurrence += step
        while occurrence <= min(horizon_end, until):
            if include:
                matched_dates.add(occurrence)
            occurrence += step
    return frozenset(matched_dates)


def _external_hard_dates(
    rows: tuple[ExternalLoad, ...],
    *,
    starts_on: date,
    zone: ZoneInfo,
) -> frozenset[date]:
    return _external_dates(rows, starts_on=starts_on, zone=zone, hard_only=True)


async def _load_reference_inputs(
    session: AsyncSession,
    *,
    athlete: AthleteProfile,
    primary: AthleteSport,
    goal: AthleteGoal,
    starts_on: date,
    athlete_level_override: str | None = None,
) -> tuple[CompilerContext, PriorityContext, dict[str, tuple[ReferenceTemplate, ...]], str, UUID]:
    base_level = athlete_level(athlete.competition_level)
    level = "beginner" if athlete.post_clearance_only else (athlete_level_override or base_level)
    scope_type, scope_code = sport_scope_key(
        primary.sport_code,
        event_code=primary.event_code,
        role_code=primary.role_code,
        discipline_code=primary.discipline_code,
        format_code=primary.format_code,
    )
    phase_code = normalize_phase(athlete.season_phase)
    goal_code = normalize_goal(goal.goal_type)
    reference_scope_code = {
        "800m": "400m",
        "1500m": "5k",
        "mile": "5k",
        "trail": "10k",
    }.get(scope_code, scope_code)
    priority_row = await session.scalar(select(SportTemplatePriority).where(
        SportTemplatePriority.sport_code == primary.sport_code,
        SportTemplatePriority.scope_type == scope_type,
        SportTemplatePriority.scope_code == reference_scope_code,
        SportTemplatePriority.phase_code == phase_code,
        SportTemplatePriority.goal_code == goal_code,
    ))
    if priority_row is None:
        raise ReferenceCompilationError("no exact sport, scope, phase and goal priority row exists")
    priority_items = tuple((await session.scalars(
        select(SportTemplatePriorityItem)
        .where(SportTemplatePriorityItem.priority_id == priority_row.id)
        .order_by(SportTemplatePriorityItem.rank)
    )).all())
    policy = await session.scalar(select(SportModePolicy).where(SportModePolicy.sport_code == primary.sport_code))
    if policy is None:
        raise ReferenceCompilationError("the sport has no training-mode policy")
    phase_policy_row = await session.scalar(
        select(PhaseDosePolicy).where(PhaseDosePolicy.phase_code == phase_code)
    )
    if phase_policy_row is None:
        raise ReferenceCompilationError("the season phase has no released dose policy")
    release = await session.scalar(
        select(ContentRelease)
        .where(
            ContentRelease.package_type == "training_reference",
            ContentRelease.state == "released",
        )
        .order_by(ContentRelease.published_at.desc())
    )
    if release is None or not release.content_hash:
        raise ReferenceCompilationError("no released training-reference dataset manifest exists")
    await _verify_release_source_hashes(session, release)

    availability = tuple((await session.scalars(
        select(AvailabilityWindow)
        .where(AvailabilityWindow.athlete_id == athlete.id)
        .order_by(AvailabilityWindow.weekday, AvailabilityWindow.start_minute)
    )).all())
    equipment_rows = tuple((await session.scalars(
        select(EquipmentAccess).where(EquipmentAccess.athlete_id == athlete.id)
    )).all())
    external = tuple((await session.scalars(
        select(ExternalLoad).where(ExternalLoad.athlete_id == athlete.id)
    )).all())
    try:
        zone = ZoneInfo(athlete.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ReferenceCompilationError("athlete timezone is not a valid IANA timezone") from exc
    external_hard_dates = _external_hard_dates(external, starts_on=starts_on, zone=zone)
    competition_rows = tuple(
        row
        for row in external
        if row.sport_code == primary.sport_code and row.load_type == "competition"
    )
    competition_dates = tuple(sorted(_external_dates(
        competition_rows,
        starts_on=starts_on,
        zone=zone,
        hard_only=False,
        horizon_weeks=12,
    )))
    future_competitions = tuple(value for value in competition_dates if value >= starts_on)
    days_to_competition = (
        (future_competitions[0] - starts_on).days
        if future_competitions
        else None
    )
    if phase_code == "competition" and days_to_competition is None:
        raise ReferenceCompilationError("competition phase requires an actual upcoming competition date")
    if days_to_competition is not None and days_to_competition <= 14 and phase_code != "competition":
        raise ReferenceCompilationError("an upcoming competition within 14 days requires competition phase")
    if phase_code == "transition" and days_to_competition is not None and days_to_competition <= 28:
        raise ReferenceCompilationError("transition phase conflicts with an upcoming competition within 28 days")
    if primary.sessions_per_week > 0 or primary.weekly_external_minutes > 0:
        primary_external = tuple(row for row in external if row.sport_code == primary.sport_code)
        exact_primary_dates = _external_dates(primary_external, starts_on=starts_on, zone=zone, hard_only=False)
        plan_end = starts_on + timedelta(weeks=4, days=-1)
        if not any(starts_on <= value <= plan_end for value in exact_primary_dates):
            raise ReferenceCompilationError(
                "exact external sport-session dates within the plan are required when weekly sport load is declared"
            )
    pain_unresolved = bool(await session.scalar(
        select(func.count()).select_from(PainReport).where(
            PainReport.athlete_id == athlete.id,
            PainReport.status == "open",
        )
    ))
    today_local = datetime.now(zone).date()
    latest_check_in = await session.scalar(
        select(DailyCheckIn)
        .where(
            DailyCheckIn.athlete_id == athlete.id,
            DailyCheckIn.local_date >= today_local - timedelta(days=2),
        )
        .order_by(DailyCheckIn.local_date.desc())
    )
    scenario_codes = set()
    if athlete.post_clearance_only:
        scenario_codes.add("re_entry_after_clearance")
    if latest_check_in and latest_check_in.readiness == 2:
        scenario_codes.add("high_fatigue_or_low_readiness")
    if pain_unresolved or (latest_check_in and latest_check_in.acute_illness):
        scenario_codes.add("pain_or_illness")
    if days_to_competition is not None and days_to_competition <= 14:
        scenario_codes.add("competition_taper")
    if len([value for value in future_competitions if value <= starts_on + timedelta(days=14)]) >= 2:
        scenario_codes.add("congested_competition")
    familiarity_rows = (await session.execute(
        select(AthleteMethodFamiliarity, Method.code)
        .join(Method, Method.id == AthleteMethodFamiliarity.method_id)
        .where(AthleteMethodFamiliarity.athlete_id == athlete.id)
        .order_by(Method.code)
    )).all()
    equipment_by_environment: dict[str, set[str]] = defaultdict(set)
    for row in equipment_rows:
        for environment in row.environments:
            equipment_by_environment[environment].add(row.equipment_code)
    context = CompilerContext(
        starts_on=starts_on,
        athlete_level=level,
        primary_mode=policy.primary_mode,
        availability=tuple(
            AvailabilitySlot(
                row.weekday,
                row.start_minute,
                row.duration_minutes,
                frozenset(row.environments),
            )
            for row in availability
        ),
        equipment=frozenset(row.equipment_code for row in equipment_rows),
        environments=frozenset(value for row in equipment_rows for value in row.environments),
        equipment_by_environment=tuple(
            (environment, frozenset(codes))
            for environment, codes in sorted(equipment_by_environment.items())
        ),
        external_hard_days=frozenset(),
        external_hard_dates=external_hard_dates,
        maximum_session_minutes=athlete.maximum_session_minutes,
        phase_policy=PhasePolicy(
            phase_code=phase_policy_row.phase_code,
            policy_version=phase_policy_row.policy_version,
            progression_mode=phase_policy_row.progression_mode,
            maximum_categories=phase_policy_row.maximum_categories,
            maximum_sessions_per_week=phase_policy_row.maximum_sessions_per_week,
            weekly_volume_multipliers=tuple(phase_policy_row.weekly_volume_multipliers),
            novelty_policy=phase_policy_row.novelty_policy,
            source_hash=phase_policy_row.source_hash,
        ),
        pain_unresolved=pain_unresolved,
        sport_code=primary.sport_code,
        scope_code=scope_code,
        phase_code=phase_code,
        goal_code=goal_code,
        readiness=latest_check_in.readiness if latest_check_in else None,
        acute_illness=latest_check_in.acute_illness if latest_check_in else False,
        scenario_codes=frozenset(scenario_codes),
        method_familiarity=tuple(
            (method_code, row.familiarity)
            for row, method_code in familiarity_rows
        ),
        competition_dates=competition_dates,
        days_to_competition=days_to_competition,
        cross_training_consent=athlete.cross_training_consent,
        external_schedule=tuple({
            "sport_code": row.sport_code,
            "load_type": row.load_type,
            "starts_at": row.starts_at.isoformat(),
            "duration_minutes": row.duration_minutes,
            "intensity": row.intensity,
            "recurrence": row.recurrence_json,
        } for row in sorted(external, key=lambda value: (value.starts_at, str(value.id)))),
    )
    priority = PriorityContext(
        primary_category=priority_row.primary_template_category,
        block_order=tuple(priority_row.session_block_order),
        ranked_categories=tuple(
            RankedCategory(row.category_code, row.rank, float(row.weight))
            for row in priority_items
        ),
        source_hash=priority_row.source_hash,
    )

    # The sport priority matrix selects the main training categories. The
    # released preparation template is also loaded so every generated session
    # has a reviewed warm-up candidate instead of an implied client-side one.
    category_codes = [row.category_code for row in priority_items]
    # Template level and category are the availability contract. Exercises
    # enforce their own minimum level, venue and equipment requirements.
    stable_templates = tuple((await session.scalars(
        select(TrainingReferenceTemplate)
        .join(
            TrainingReferenceTemplateVersion,
            and_(
                TrainingReferenceTemplateVersion.template_id == TrainingReferenceTemplate.id,
                TrainingReferenceTemplateVersion.content_version == TrainingReferenceTemplate.latest_version,
            ),
        )
        .where(
            TrainingReferenceTemplateVersion.category_code.in_((*category_codes, "performance_preparation")),
            TrainingReferenceTemplateVersion.athlete_level == level,
            TrainingReferenceTemplateVersion.status == "released",
        )
    )).all()) if category_codes else ()
    template_codes = [row.code for row in stable_templates]
    # Fetch every exact latest released version in one round trip.  The join
    # retains the same version pinning as the former per-template lookup while
    # avoiding network latency proportional to the number of categories.
    version_rows = tuple((await session.scalars(
        select(TrainingReferenceTemplateVersion)
        .join(
            TrainingReferenceTemplate,
            and_(
                TrainingReferenceTemplate.id == TrainingReferenceTemplateVersion.template_id,
                TrainingReferenceTemplate.latest_version == TrainingReferenceTemplateVersion.content_version,
            ),
        )
        .where(
            TrainingReferenceTemplate.code.in_(template_codes),
            TrainingReferenceTemplateVersion.athlete_level == level,
            TrainingReferenceTemplateVersion.status == "released",
        )
        .order_by(TrainingReferenceTemplate.code)
    )).all()) if template_codes else ()

    template_ids = [row.template_id for row in version_rows]
    method_links = tuple((await session.scalars(
        select(TrainingReferenceMethod).where(
            TrainingReferenceMethod.template_id.in_(template_ids),
        ).order_by(TrainingReferenceMethod.template_id, TrainingReferenceMethod.sequence)
    )).all()) if template_ids else ()
    method_keys = {(row.method_id, row.method_version) for row in method_links}
    method_versions: dict[tuple[UUID, int], MethodVersion] = {}
    method_codes: dict[UUID, str] = {}
    version_code_rows = (await session.execute(
        select(MethodVersion, Method.code)
        .join(Method, Method.id == MethodVersion.method_id)
        .where(
            tuple_(MethodVersion.method_id, MethodVersion.content_version).in_(method_keys),
            MethodVersion.generator_eligible.is_(True),
            MethodVersion.status == "released",
        )
        .order_by(Method.code)
    )).all() if method_keys else ()
    for version, code in version_code_rows:
        method_versions[(version.method_id, version.content_version)] = version
        method_codes[version.method_id] = code
    weeks = tuple((await session.scalars(
        select(TrainingReferenceWeek)
        .where(TrainingReferenceWeek.template_id.in_(template_ids))
        .order_by(TrainingReferenceWeek.template_id, TrainingReferenceWeek.week_number)
    )).all()) if template_ids else ()
    links_by_template: dict[tuple[UUID, int], list[TrainingReferenceMethod]] = defaultdict(list)
    for row in method_links:
        links_by_template[(row.template_id, row.template_version)].append(row)
    weeks_by_template: dict[tuple[UUID, int], list[TrainingReferenceWeek]] = defaultdict(list)
    for row in weeks:
        weeks_by_template[(row.template_id, row.template_version)].append(row)

    stable_by_id = {row.id: row for row in stable_templates}
    templates_by_category: dict[str, list[ReferenceTemplate]] = defaultdict(list)
    for version in version_rows:
        key = (version.template_id, version.content_version)
        reference_methods: list[ReferenceMethod] = []
        for link in links_by_template[key]:
            method = method_versions.get((link.method_id, link.method_version))
            if method is None:
                continue
            reference_methods.append(ReferenceMethod(
                method_id=method.method_id,
                method_version=method.content_version,
                code=method_codes[method.method_id],
                name=method.canonical_name,
                sequence=link.sequence,
                applicable_modes=frozenset(link.applicable_modes),
                equipment=frozenset(method.equipment_codes),
                environments=frozenset(method.environments),
                minimum_level=method.level_minimum,
                technical_cost=method.technical_cost,
                impact_cost=method.impact_cost,
                fatigue_cost=method.fatigue_cost,
                accepted_dose_units=frozenset(method.accepted_dose_units),
                safety_boundaries=tuple(method.safety_boundaries),
                sport_codes=frozenset(link.sport_codes),
                scope_codes=frozenset(link.scope_codes),
                block_role=link.block_role,
            ))
        reference_weeks = tuple(
            ReferenceWeek(
                week_number=row.week_number,
                sessions_per_week=str(row.sessions_per_week),
                intent=row.intent,
                prescription=normalize_reference_prescription(row.prescription_json),
                progression_condition=row.progression_condition,
                regression_condition=row.regression_condition,
            )
            for row in weeks_by_template[key]
        )
        if len(reference_weeks) != 4:
            continue
        templates_by_category[version.category_code].append(ReferenceTemplate(
            template_id=version.template_id,
            template_version=version.content_version,
            code=stable_by_id[version.template_id].code,
            category_code=version.category_code,
            purpose=version.purpose,
            source_hash=version.source_hash,
            methods=tuple(reference_methods),
            weeks=reference_weeks,
            week_4_policy=version.week_4_policy,
        ))
    return (
        context,
        priority,
        {key: tuple(value) for key, value in templates_by_category.items()},
        release.content_hash,
        release.id,
    )
