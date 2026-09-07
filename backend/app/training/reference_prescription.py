from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class NumericRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum: float
    maximum: float


class WorkDose(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["repetitions", "contacts", "duration", "distance"]
    amount: NumericRange
    unit: Literal["count", "seconds", "meters"]
    repetitions: int = Field(default=1, ge=1)
    per_side: bool = False


class IntensityDose(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["rir", "rpe", "relative_percent", "descriptor"]
    amount: NumericRange | None = None
    descriptor: str | None = None
    tempo_eccentric_seconds: NumericRange | None = None
    qualifier: str | None = None


class RecoveryDose(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["duration", "none", "continuous", "rep_and_set"]
    between_efforts_seconds: NumericRange | None = None
    between_sets_seconds: NumericRange | None = None
    qualifier: str | None = None


class NormalizedReferencePrescription(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sets_or_series: int = Field(ge=1, le=20)
    work: WorkDose
    intensity: IntensityDose
    recovery: RecoveryDose
    source: dict[str, Any]


class PrescriptionBindingError(ValueError):
    pass


_NUMBER = r"(?P<low>\d+(?:\.\d+)?)(?:-(?P<high>\d+(?:\.\d+)?))?"


def _range(match: re.Match[str], multiplier: float = 1) -> NumericRange:
    low = float(match.group("low")) * multiplier
    high = float(match.group("high") or match.group("low")) * multiplier
    return NumericRange(minimum=low, maximum=high)


def parse_work(value: str) -> WorkDose:
    text = value.strip().lower()
    interval = re.fullmatch(r"(?P<repetitions>\d+)x(?P<low>\d+(?:\.\d+)?)(?:-(?P<high>\d+(?:\.\d+)?))?m", text)
    if interval:
        return WorkDose(kind="distance", amount=_range(interval), unit="meters", repetitions=int(interval.group("repetitions")))
    contacts = re.fullmatch(_NUMBER + r" contacts", text)
    if contacts:
        return WorkDose(kind="contacts", amount=_range(contacts), unit="count")
    side = re.fullmatch(_NUMBER + r"/side", text)
    if side:
        return WorkDose(kind="repetitions", amount=_range(side), unit="count", per_side=True)
    duration = re.fullmatch(_NUMBER + r"(?P<unit>s|min)", text)
    if duration:
        return WorkDose(kind="duration", amount=_range(duration, 60 if duration.group("unit") == "min" else 1), unit="seconds")
    distance = re.fullmatch(_NUMBER + r"m", text)
    if distance:
        return WorkDose(kind="distance", amount=_range(distance), unit="meters")
    repetitions = re.fullmatch(_NUMBER, text)
    if repetitions:
        return WorkDose(kind="repetitions", amount=_range(repetitions), unit="count")
    raise ValueError(f"unsupported reference work dose: {value}")


def parse_intensity(value: str) -> IntensityDose:
    text = value.strip()
    tempo = re.fullmatch(r"(?P<tempo_low>\d+)(?:-(?P<tempo_high>\d+))?s eccentric/RIR (?P<low>\d+)(?:-(?P<high>\d+))?", text)
    if tempo:
        return IntensityDose(
            kind="rir",
            amount=_range(tempo),
            tempo_eccentric_seconds=NumericRange(
                minimum=float(tempo.group("tempo_low")),
                maximum=float(tempo.group("tempo_high") or tempo.group("tempo_low")),
            ),
        )
    controlled_rir = re.fullmatch(r"(?P<qualifier>controlled)/RIR (?P<low>\d+)(?:-(?P<high>\d+))?", text)
    if controlled_rir:
        return IntensityDose(kind="rir", amount=_range(controlled_rir), qualifier=controlled_rir.group("qualifier"))
    rir = re.fullmatch(r"RIR (?P<low>\d+)(?:-(?P<high>\d+))?", text)
    if rir:
        return IntensityDose(kind="rir", amount=_range(rir))
    rpe = re.fullmatch(r"RPE (?P<low>\d+)(?:-(?P<high>\d+))?(?:/(?P<qualifier>talk test))?", text)
    if rpe:
        return IntensityDose(kind="rpe", amount=_range(rpe), qualifier=rpe.group("qualifier"))
    percent = re.fullmatch(r"(?P<low>\d+)(?:-(?P<high>\d+))?%(?: (?P<qualifier>entry|intent))?", text)
    if percent:
        return IntensityDose(kind="relative_percent", amount=_range(percent), qualifier=percent.group("qualifier"))
    if re.fullmatch(r"[a-z][a-z ,/-]*", text):
        return IntensityDose(kind="descriptor", descriptor=text)
    raise ValueError(f"unsupported reference intensity: {value}")


def _duration_range(value: str) -> tuple[NumericRange, str | None]:
    match = re.fullmatch(_NUMBER + r"(?P<unit>s|min)(?: (?P<qualifier>easy))?", value)
    if not match:
        raise ValueError(f"unsupported recovery duration: {value}")
    return _range(match, 60 if match.group("unit") == "min" else 1), match.group("qualifier")


def parse_recovery(value: str) -> RecoveryDose:
    text = value.strip().lower()
    if text in {"none", "continuous"}:
        return RecoveryDose(kind=text)
    rep_set = re.fullmatch(r"(?P<rep>\d+)s(?: reps)?/(?P<sets>\d+)min(?: sets)?", text)
    if rep_set:
        return RecoveryDose(
            kind="rep_and_set",
            between_efforts_seconds=NumericRange(minimum=float(rep_set.group("rep")), maximum=float(rep_set.group("rep"))),
            between_sets_seconds=NumericRange(minimum=float(rep_set.group("sets")) * 60, maximum=float(rep_set.group("sets")) * 60),
        )
    amount, qualifier = _duration_range(text)
    return RecoveryDose(kind="duration", between_efforts_seconds=amount, qualifier=qualifier)


def normalize_reference_prescription(source: dict[str, Any]) -> NormalizedReferencePrescription:
    return NormalizedReferencePrescription(
        sets_or_series=int(source["sets_or_series"]),
        work=parse_work(str(source["repetitions_distance_or_duration"])),
        intensity=parse_intensity(str(source["intensity"])),
        recovery=parse_recovery(str(source["recovery"])),
        source=dict(source),
    )


def bind_prescription_to_method(
    prescription: NormalizedReferencePrescription,
    accepted_dose_units: set[str] | frozenset[str],
) -> dict[str, Any]:
    """Bind a generic reference dose to one method's registered dose vocabulary.

    No unit is inferred when the catalogue cannot express it. Descriptive
    intensity remains an instruction, while every numeric field must map to an
    accepted method dose unit.
    """
    units = set(accepted_dose_units)
    output: dict[str, Any] = {}
    if "sets" in units:
        output["sets"] = prescription.sets_or_series
    elif prescription.sets_or_series != 1:
        raise PrescriptionBindingError("method does not accept sets")

    work = prescription.work
    amount = work.amount.model_dump()
    if work.kind == "repetitions":
        if "repetitions" not in units:
            raise PrescriptionBindingError("reference repetitions cannot bind to this method")
        output["repetitions"] = {**amount, "per_side": work.per_side}
    elif work.kind == "contacts":
        if "contacts" not in units:
            raise PrescriptionBindingError("reference contacts cannot bind to this method")
        output["contacts"] = amount
    elif work.kind == "distance":
        if "distance_m" not in units:
            raise PrescriptionBindingError("reference distance cannot bind to this method")
        output["distance_m"] = amount
        if work.repetitions > 1:
            if "repetitions" not in units:
                raise PrescriptionBindingError("distance intervals require a repetitions dose unit")
            output["repetitions"] = work.repetitions
    else:
        if "duration_seconds" in units:
            output["duration_seconds"] = amount
        elif "bout_duration_seconds" in units:
            output["bout_duration_seconds"] = amount
        elif "duration_minutes" in units and amount["minimum"] % 60 == 0 and amount["maximum"] % 60 == 0:
            output["duration_minutes"] = {
                "minimum": amount["minimum"] / 60,
                "maximum": amount["maximum"] / 60,
            }
        else:
            raise PrescriptionBindingError("reference duration cannot bind to this method")

    intensity = prescription.intensity
    if intensity.kind == "rir":
        if "rir" not in units:
            raise PrescriptionBindingError("RIR cannot bind to this method")
        output["rir"] = intensity.amount.model_dump() if intensity.amount else None
        if intensity.tempo_eccentric_seconds:
            if "tempo_seconds" not in units:
                raise PrescriptionBindingError("eccentric tempo cannot bind to this method")
            output["tempo_seconds"] = intensity.tempo_eccentric_seconds.model_dump()
    elif intensity.kind == "rpe":
        target = "effort_rpe" if "effort_rpe" in units else "intensity_system" if "intensity_system" in units else None
        if target is None:
            raise PrescriptionBindingError("RPE cannot bind to this method")
        output[target] = {"system": "rpe", **(intensity.amount.model_dump() if intensity.amount else {})}
    elif intensity.kind == "relative_percent":
        target = next((key for key in ("percentage_1rm", "intensity_percent", "approach_intensity_percent") if key in units), None)
        if target:
            output[target] = intensity.amount.model_dump() if intensity.amount else None
        elif "intensity_system" in units:
            output["intensity_system"] = {"system": "relative_percent", **(intensity.amount.model_dump() if intensity.amount else {})}
        else:
            raise PrescriptionBindingError("relative percentage cannot bind to this method")
    else:
        output["intensity_instruction"] = intensity.descriptor

    recovery = prescription.recovery
    if recovery.kind in {"duration", "rep_and_set"}:
        if "recovery_seconds" not in units:
            raise PrescriptionBindingError("recovery duration cannot bind to this method")
        recovery_amount = recovery.between_efforts_seconds.model_dump() if recovery.between_efforts_seconds else None
        # A single ordinary recovery value applies between sets/series. An
        # interval notation (for example 3x20m) makes it between efforts.
        # Rep-and-set syntax is the only form that supplies both scopes.
        if recovery.kind == "rep_and_set" or work.repetitions > 1:
            output["recovery_between_efforts_seconds"] = recovery_amount
        else:
            output["recovery_between_sets_seconds"] = recovery_amount
        if recovery.between_sets_seconds:
            target = "set_recovery_seconds" if "set_recovery_seconds" in units else None
            if not target:
                raise PrescriptionBindingError("set recovery cannot bind to this method")
            output["recovery_between_sets_seconds"] = recovery.between_sets_seconds.model_dump()
    output["reference_source"] = prescription.source
    return output
