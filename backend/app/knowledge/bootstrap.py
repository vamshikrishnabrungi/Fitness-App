from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import KnowledgeTerm, PhysicalQuality, SportTaxon


PHYSICAL_QUALITIES = {
    "maximum_strength": ("Maximum strength", "strength"),
    "explosive_strength": ("Explosive strength", "power"),
    "acceleration": ("Acceleration", "speed"),
    "maximum_velocity": ("Maximum velocity", "speed"),
    "speed_endurance": ("Speed endurance", "speed"),
    "deceleration": ("Deceleration", "movement"),
    "change_of_direction": ("Change of direction", "movement"),
    "reactive_agility": ("Reactive agility", "movement"),
    "vertical_power": ("Vertical power", "power"),
    "horizontal_power": ("Horizontal power", "power"),
    "lateral_power": ("Lateral power", "power"),
    "rotational_power": ("Rotational power", "power"),
    "upper_body_power": ("Upper-body power", "power"),
    "isometric_force_capacity": ("Isometric force capacity", "strength"),
    "eccentric_capacity": ("Eccentric capacity", "strength"),
    "reactive_elastic_strength": ("Reactive and elastic strength", "power"),
    "aerobic_capacity": ("Aerobic capacity", "conditioning"),
    "threshold_capacity": ("Threshold capacity", "conditioning"),
    "high_intensity_aerobic_power": ("High-intensity aerobic power", "conditioning"),
    "anaerobic_power": ("Anaerobic power", "conditioning"),
    "anaerobic_capacity": ("Anaerobic capacity", "conditioning"),
    "repeated_sprint_ability": ("Repeated-sprint ability", "conditioning"),
    "repeated_high_intensity_ability": ("Repeated high-intensity ability", "conditioning"),
    "local_muscular_endurance": ("Local muscular endurance", "capacity"),
    "calf_soleus_capacity": ("Calf–soleus capacity", "tissue_capacity"),
    "hamstring_capacity": ("Hamstring capacity", "tissue_capacity"),
    "adductor_capacity": ("Adductor capacity", "tissue_capacity"),
    "shoulder_capacity": ("Shoulder capacity", "tissue_capacity"),
    "trunk_force_transfer": ("Trunk force transfer", "capacity"),
    "neck_capacity": ("Neck capacity", "tissue_capacity"),
    "grip_capacity": ("Grip capacity", "tissue_capacity"),
    "balance_postural_control": ("Balance and postural control", "movement"),
    "movement_coordination": ("Movement coordination", "movement"),
    "mobility_range_capacity": ("Mobility and range capacity", "capacity"),
    "economy_efficiency": ("Movement economy and efficiency", "conditioning"),
    "landing_capacity": ("Landing capacity", "movement"),
    "mobility_preparation": ("Mobility and preparation", "preparation"),
    "recovery_capacity": ("Recovery capacity", "recovery"),
}

TAXONOMY = {
    "running": {"event": ["run_walk", "5k", "10k", "half_marathon", "marathon", "100m", "200m", "400m"]},
    "football": {"role": ["goalkeeper", "central_defender", "fullback_wingback", "central_midfielder", "winger", "striker"]},
    "cricket": {"role": ["batter", "wicketkeeper", "pace_bowler", "spin_bowler", "all_rounder"]},
    "basketball": {"role": ["guard", "wing", "big"]},
    "volleyball": {"role": ["setter", "outside_hitter", "opposite", "middle_blocker", "libero"]},
    "badminton": {"format": ["singles", "doubles"]},
    "tennis": {"format": ["singles", "doubles"]},
    "cycling": {"event": ["fitness_endurance", "road_endurance", "time_trial", "sprint"]},
    "swimming": {
        "event": ["sprint", "middle_distance", "distance"],
        "discipline": ["freestyle", "backstroke", "breaststroke", "butterfly", "individual_medley"],
    },
    "boxing": {"format": ["amateur", "professional"]},
    "mma": {"format": ["three_round", "five_round"]},
    "hyrox": {"format": ["individual_open", "individual_pro", "doubles"]},
}

TERMS = {
    "training_role": ["preparation", "primary", "accessory", "capacity", "recovery"],
    "force_direction": ["vertical", "horizontal", "lateral", "rotational", "multidirectional"],
    "contraction": ["concentric", "eccentric", "isometric_yielding", "isometric_overcoming", "stretch_shortening"],
    "speed_intent": ["controlled", "slow", "fast", "explosive", "maximal_velocity"],
    "environment": ["home", "gym", "field", "court", "road", "track", "pool", "trail"],
    "surface": ["indoor", "grass", "artificial_turf", "court", "road", "track", "pool", "trail"],
    "dose_unit": ["sets", "repetitions", "contacts", "attempts", "duration_seconds", "duration_minutes", "bout_duration_seconds", "distance_m", "distance_km", "height_cm", "load_kg", "percentage_1rm", "effort_rpe", "rir", "tempo_seconds", "intensity_percent", "intensity_system", "pace", "heart_rate_zone", "power_watts", "velocity", "recovery_seconds", "recovery_minutes", "set_recovery_seconds", "joint_position", "range_of_motion", "approach_intensity_percent", "cut_angle_degrees", "stimulus_type", "choice_count", "pool_length_m", "stroke_code", "send_off_seconds", "sled_load", "velocity_decrement_percent", "build_distance_m", "fly_distance_m", "wicket_spacing_m", "measurement_unit"],
    "method_type": ["exercise", "isometric", "plyometric", "speed_drill", "deceleration_drill", "change_of_direction_drill", "reactive_agility_drill", "preparation_drill", "mobility", "conditioning_modality", "assessment"],
    "athlete_level": ["beginner", "recreational", "intermediate", "club", "regional", "advanced", "national", "international"],
}


async def seed_controlled_taxonomy(session: AsyncSession) -> dict[str, int]:
    created = {"qualities": 0, "sports": 0, "taxa": 0, "terms": 0}
    existing_quality = set((await session.scalars(select(PhysicalQuality.code))).all())
    for code, (name, category) in PHYSICAL_QUALITIES.items():
        if code not in existing_quality:
            session.add(PhysicalQuality(code=code, name=name, category=category, description=f"Controlled Runlete physical quality: {name}.", status="draft"))
            created["qualities"] += 1

    existing_taxa = set((await session.scalars(select(SportTaxon.code))).all())
    for sport, groups in TAXONOMY.items():
        root_code = f"sport_{sport}"
        root = await session.scalar(select(SportTaxon).where(SportTaxon.code == root_code))
        if root is None:
            root = SportTaxon(code=root_code, name=sport.upper() if sport == "mma" else sport.title(), taxon_type="sport", sport_code=sport, status="draft", visible=sport != "hyrox")
            session.add(root)
            await session.flush()
            created["sports"] += 1
        for taxon_type, codes in groups.items():
            for code in codes:
                stable_code = f"{sport}_{taxon_type}_{code}"
                if stable_code in existing_taxa:
                    continue
                session.add(SportTaxon(code=stable_code, name=code.replace("_", " ").title(), taxon_type=taxon_type, sport_code=sport, parent_id=root.id, status="draft", visible=sport != "hyrox"))
                created["taxa"] += 1

    existing_terms = {(category, code) for category, code in (await session.execute(select(KnowledgeTerm.category, KnowledgeTerm.code))).all()}
    for category, codes in TERMS.items():
        for code in codes:
            if (category, code) in existing_terms:
                continue
            name = code.replace("_", " ").title()
            session.add(KnowledgeTerm(category=category, code=code, name=name, description=f"Controlled {category.replace('_', ' ')} value: {name}.", status="draft"))
            created["terms"] += 1
    await session.commit()
    return created
