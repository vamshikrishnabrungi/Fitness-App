from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from backend.db_setup import ensure_database_schema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CRICKET_DIR = PROJECT_ROOT / "backend" / "sport_research" / "cricket"
DRAFT_DIR = CRICKET_DIR / "drafts"
OUTPUT_PATH = CRICKET_DIR / "cricket_level_teaching_database.json"

SOURCE_PACK_ID = "cricket_level_teaching_database_v1"
INGESTION_METHOD = "cricket_research_drafts_curated_level_teaching_v1"


DOMAIN_DRAFTS: Dict[str, List[str]] = {
    "batting": ["batting_skill_tactics_draft.json", "conditions_match_iq_draft.json"],
    "pace_bowling": ["pace_bowling_skill_workload_draft.json", "cricket_snc_injury_macro_planning_draft.json"],
    "spin_bowling": ["spin_bowling_skill_tactics_draft.json", "conditions_match_iq_draft.json"],
    "fielding": ["fielding_throwing_wicketkeeping_draft.json", "cricket_snc_injury_macro_planning_draft.json"],
    "throwing": ["fielding_throwing_wicketkeeping_draft.json", "cricket_snc_injury_macro_planning_draft.json"],
    "wicketkeeping": ["fielding_throwing_wicketkeeping_draft.json", "cricket_snc_injury_macro_planning_draft.json"],
    "match_iq": ["conditions_match_iq_draft.json", "batting_skill_tactics_draft.json", "pace_bowling_skill_workload_draft.json", "spin_bowling_skill_tactics_draft.json"],
    "cricket_snc": ["cricket_snc_injury_macro_planning_draft.json"],
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _dedupe(items: Iterable[Any]) -> List[Any]:
    result: List[Any] = []
    seen = set()
    for item in items:
        if item in (None, "", [], {}):
            continue
        key = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _load_draft(file_name: str) -> Dict[str, Any]:
    path = DRAFT_DIR / file_name
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _source_refs(domain: str, limit: int = 10) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = []
    for file_name in DOMAIN_DRAFTS.get(domain, []):
        draft = _load_draft(file_name)
        for ref in draft.get("source_refs") or []:
            if not isinstance(ref, dict) or not ref.get("title") or not ref.get("url"):
                continue
            refs.append({
                "source_pack_id": SOURCE_PACK_ID,
                "draft_file": file_name,
                "title": ref.get("title"),
                "url": ref.get("url"),
                "source_type": ref.get("source_type"),
                "notes": ref.get("notes"),
            })
    return _dedupe(refs)[:limit]


def _teaching_record(
    domain: str,
    level: str,
    role_tags: Sequence[str],
    learning_goal: str,
    suitable_for: Sequence[str],
    prerequisites: Sequence[str],
    teaching_priorities: Sequence[str],
    technical_focus: Sequence[str],
    tactical_focus: Sequence[str],
    physical_support: Sequence[str],
    practice_design: Sequence[str],
    typical_drills: Sequence[str],
    avoid_until_ready: Sequence[str],
    progression_signals: Sequence[str],
    coach_notes: Sequence[str],
) -> Dict[str, Any]:
    return {
        "id": f"cricket_teach_{domain}_{level}",
        "sport": "cricket",
        "domain": domain,
        "level": level,
        "role_tags": list(role_tags),
        "learning_goal": learning_goal,
        "suitable_for": list(suitable_for),
        "prerequisites": list(prerequisites),
        "teaching_priorities": list(teaching_priorities),
        "technical_focus": list(technical_focus),
        "tactical_focus": list(tactical_focus),
        "physical_support": list(physical_support),
        "practice_design": list(practice_design),
        "typical_drills": list(typical_drills),
        "avoid_until_ready": list(avoid_until_ready),
        "progression_signals": list(progression_signals),
        "coach_notes": list(coach_notes),
        "retrieval_tags": sorted(set([
            "cricket",
            domain,
            level,
            *role_tags,
            *[item.split()[0].lower().replace("-", "_") for item in teaching_priorities[:6]],
        ])),
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs(domain),
    }


TEACHING_PROGRESSIONS: List[Dict[str, Any]] = [
    _teaching_record(
        "batting",
        "beginner",
        ["batter", "all_rounder"],
        "Build a repeatable setup and safe straight-bat scoring foundation before expanding shot range.",
        ["new batters", "recreational users", "users with weak shot selection", "users returning after a break"],
        ["basic hand-eye coordination", "safe protective equipment", "understands scoring and crease basics"],
        ["comfortable stance and guard", "balanced head and eyes", "basic grip and bat face control", "front-foot defense and drive", "back-foot punch/cut introduction", "calling and running basics"],
        ["level eyes", "head close to contact line", "soft hands", "straight bat path", "complete trigger before release", "watch ball from hand"],
        ["play straight early", "know when to leave", "rotate safe singles", "avoid premeditated cross-bat shots"],
        ["basic acceleration", "deceleration and turning", "thoracic rotation", "wrist and shoulder tolerance", "calf and hamstring capacity"],
        ["blocked technical reps first", "underarm/sidearm feeds", "clear target zones", "short sets with feedback", "finish with simple game scenario"],
        ["shadow batting to target line", "drop-feed straight drive", "front-foot defense feed", "back-foot punch feed", "single-call running drill", "basic throwdown net"],
        ["hard bouncer exposure", "full power hitting", "reverse sweep", "fatigue-based batting volume", "heavy rotational gym work before movement control"],
        ["stable stance without falling across", "can defend straight balls", "can choose leave/defend/drive in simple feeds", "can call and turn safely", "no worsening wrist/shoulder/back symptoms"],
        ["Do not force one ideal stance; stabilize outcomes first.", "Technique should support seeing the ball and controlling contact, not looking textbook."]
    ),
    _teaching_record(
        "batting",
        "intermediate",
        ["batter", "all_rounder"],
        "Add adaptable footwork, pace/spin decision-making, strike rotation, and role-specific scoring options.",
        ["regular club batters", "school or college players", "users who can handle basic net pace"],
        ["repeatable setup", "basic straight-bat control", "can run between wickets safely"],
        ["trigger movement consistency", "front/back length recognition", "shot selection by line and length", "playing swing late", "using feet to spin", "sweep/cut/pull control", "strike rotation"],
        ["trigger completed before release", "late contact vs movement", "stable base when sweeping", "head stable under short ball", "bat path matched to shot family"],
        ["new-ball caution", "middle-over rotation", "powerplay scoring zones", "spin matchup options", "partnership tempo"],
        ["rotational power with trunk control", "repeat sprint and turn capacity", "hamstring/adductor resilience", "shoulder/wrist durability"],
        ["variable feeds", "pace/spin contrast blocks", "scenario nets", "field map constraints", "decision score after each ball"],
        ["late drive vs swing feed", "short-ball decision drill", "sweep decision ladder", "use-of-feet to spin", "two-run turn drill", "field-target net game"],
        ["blind slogging", "too many new shots in one block", "advanced ramp/reverse options without base control", "max power work during high batting load"],
        ["can explain plan vs pace and spin", "can rotate strike without panic", "can keep shape under variable feeds", "can recover after false shot", "tolerates cricket plus gym load"],
        ["Intermediate batting should create choices, not just more shots.", "Use scenario constraints so the batter learns why a shot is selected."]
    ),
    _teaching_record(
        "batting",
        "advanced",
        ["batter", "finisher", "top_order", "all_rounder"],
        "Specialize batting plans by role, format, bowler type, field, conditions, and match state.",
        ["high-performing club batters", "academy players", "competitive athletes", "users with clear batting role"],
        ["stable technical model", "multiple scoring options", "good self-awareness under pressure"],
        ["bowler-specific plans", "field manipulation", "tempo control", "matchup selection", "power hitting mechanics", "red-ball session discipline", "death-over options"],
        ["repeatable contact point under pressure", "controlled bat swing speed", "hip-shoulder sequencing", "shot disguise", "stable head during innovation shots"],
        ["risk-reward by phase", "left/right matchups", "boundary option selection", "bowler setup recognition", "conditions-based scoring zones"],
        ["maximal acceleration exposure", "rotational power", "deceleration and turning under fatigue", "trunk stiffness", "shoulder/wrist robustness"],
        ["scenario nets with field and score", "bowler-pattern simulations", "fatigue-managed high-intensity batting", "video review", "opposition-style blocks"],
        ["death-over option tree", "red-ball leave/score discipline", "spin matchup net", "power hitting intent sets", "strike-rate pressure game", "targeted weakness block"],
        ["new high-risk shots in competition week", "max effort power hitting with back/wrist pain", "fatigue-only volume with no decision quality"],
        ["can adapt plan between balls", "has reliable scoring option against each bowling family", "keeps decision quality under fatigue", "can state match role and risk budget"],
        ["Advanced does not mean random innovation; it means better decisions under more constraints.", "Power work should preserve contact quality."]
    ),
    _teaching_record(
        "pace_bowling",
        "beginner",
        ["pace_bowler", "all_rounder"],
        "Create a safe rhythmical action, stock line/length, and basic workload habits before variations or speed chasing.",
        ["new pace bowlers", "young bowlers", "recreational all-rounders"],
        ["pain-free running", "basic throwing tolerance", "safe footwear/surface", "no active back pain"],
        ["repeatable run-up rhythm", "balanced gather", "safe front-foot contact", "seam-up grip", "stock good length", "follow-through and deceleration", "bowling log habit"],
        ["start smooth not maximal", "same take-off point", "front side controlled", "wrist behind ball", "finish balanced"],
        ["bowl at stumps/top of off", "use simple field support", "avoid trying every variation"],
        ["general strength", "landing mechanics", "trunk endurance", "calf/hamstring capacity", "shoulder/scapular control"],
        ["short spells", "target cones", "full rest between technical sets", "no high-volume fatigue spells", "record balls bowled"],
        ["walk-through action drill", "run-up mark consistency", "seam position target", "good-length target bowling", "follow-through channel", "low-volume spell practice"],
        ["bouncers", "yorker marathons", "slower-ball/cutter volume", "max-speed bowling after layoff", "heavy spinal loading after bowling"],
        ["can hit run-up mark", "no back pain next day", "can bowl stock length repeatedly", "can log overs and symptoms", "can recover between sessions"],
        ["Back pain is a stop signal, especially for youth.", "Beginner pace bowling should build repeatability before speed."]
    ),
    _teaching_record(
        "pace_bowling",
        "intermediate",
        ["pace_bowler", "all_rounder"],
        "Develop seam/swing control, spell planning, controlled speed, and one variation at a time with workload guardrails.",
        ["club pace bowlers", "school/college bowlers", "all-rounders with stable stock ball"],
        ["repeatable stock action", "bowling log", "tolerates planned spell volume", "no unresolved lumbar pain"],
        ["run-up speed control", "release consistency", "outswing/inswing or seam plan", "length adjustment by pitch", "basic bouncer/yorker exposure", "one variation progression"],
        ["momentum into crease", "stable head/trunk", "seam presentation", "wrist position", "balanced deceleration"],
        ["new ball top-of-off", "old ball stump attack", "short-ball setup", "death-over yorker plan", "left/right batter line changes"],
        ["posterior-chain strength", "anti-rotation trunk", "sprint mechanics", "shoulder durability", "adductor/calf resilience"],
        ["spell simulation", "target maps", "variation caps", "match-week load trim", "review accuracy and symptoms"],
        ["swing/seam target channel", "bouncer-yorker contrast low volume", "slower ball progression", "two-over spell simulation", "left/right hand plan drill"],
        ["multiple new variations together", "large bowling spikes", "heavy lower-back loading close to long spells", "speed testing when sore"],
        ["can keep pace with accuracy", "can execute one variation without action giveaway", "can adjust line by batter hand", "load trend is stable"],
        ["Intermediate pace work is about controllable weapons, not novelty.", "Variation training should never hide workload spikes."]
    ),
    _teaching_record(
        "pace_bowling",
        "advanced",
        ["pace_bowler", "death_bowler", "new_ball_bowler", "all_rounder"],
        "Build batter-specific plans, phase-specific weapons, and high-quality speed/variation exposure without overload.",
        ["advanced club bowlers", "academy bowlers", "competitive all-rounders"],
        ["stable workload history", "stock ball accuracy", "variation tolerance", "clear role and match format"],
        ["new-ball movement plans", "reverse/old-ball plans when relevant", "death bowling option tree", "short-ball strategy", "field-coupled deception", "spell management"],
        ["repeatable release at high intent", "same action for variation", "front-foot stiffness", "trunk control", "safe deceleration"],
        ["set up batters across overs", "use field to sell plan", "conditions-based lengths", "matchup-specific bouncer/yorker/slower-ball choices"],
        ["max velocity exposure", "heavy strength away from bowling peaks", "rotational power", "lumbar resilience", "recovery monitoring"],
        ["scenario spells", "opposition batter simulation", "field plus target constraints", "high-rest speed sets", "video/action review"],
        ["death-over six-ball plan", "new-ball attacking spell", "reverse/old-ball tactical block", "short-ball setup block", "variation disguise review"],
        ["new weapon in match week", "unmonitored high-intent bowling", "heavy gym work after high bowling load", "bowling through back symptoms"],
        ["can explain ball-by-ball plan", "variation and stock ball look similar", "keeps pace late in spell", "no pain/load trend flags"],
        ["Advanced pace bowling needs high specificity and strict fatigue control.", "The backend should reduce gym stress around high bowling weeks."]
    ),
    _teaching_record(
        "spin_bowling",
        "beginner",
        ["spinner", "all_rounder"],
        "Build a repeatable stock ball, legal action, basic landing accuracy, and safe wrist/finger load before variations.",
        ["new spinners", "recreational bowlers", "young all-rounders"],
        ["understands bowling arm and spin type", "no active wrist/finger/shoulder pain"],
        ["spin family selection", "stock grip", "legal arm path", "repeatable release", "basic line and length", "simple field awareness"],
        ["balanced approach", "stable front side", "wrist/finger action", "same release rhythm", "finish toward target"],
        ["make batter play", "bowl to simple target", "protect easy singles only after accuracy improves"],
        ["shoulder control", "forearm/wrist/finger capacity", "hip/trunk rotation", "single-leg balance"],
        ["short accuracy sets", "large target zones", "stock ball only or one safe variation", "symptom tracking"],
        ["stock ball target mat", "one-step release drill", "spin axis awareness", "line-length ladder", "same-action pace change"],
        ["googly/flipper/doosra volume", "forcing elbow snap", "long variation sessions", "bowling with finger/wrist pain"],
        ["can land stock ball in target", "can repeat action", "no next-day wrist/finger pain", "understands field for stock ball"],
        ["Beginner spin is control first.", "Variation interest should not unlock advanced skills without stock-ball accuracy."]
    ),
    _teaching_record(
        "spin_bowling",
        "intermediate",
        ["spinner", "all_rounder"],
        "Add pace, flight, crease use, handedness plans, and one or two controlled variations around the stock ball.",
        ["club spinners", "school/college spinners", "all-rounders with stock-ball control"],
        ["stock-ball accuracy", "basic spin family mechanics", "tolerates bowling volume"],
        ["flight versus speed", "use of crease", "top-spin/arm-ball or safe variation", "left/right batter lines", "rough/flat pitch adjustments"],
        ["same action across pace change", "release height control", "axis awareness", "balanced follow-through"],
        ["build pressure", "use field for edge/miscue", "bowl to handedness matchup", "respond to sweep", "change pace without telegraphing"],
        ["rotational control", "forearm endurance", "scapular control", "hip mobility", "spell repeatability"],
        ["target plus field simulations", "variation cap", "handedness scenario", "rough target practice"],
        ["pace/flight ladder", "crease angle drill", "sweep response drill", "left/right matchup plan", "stock-plus-one variation set"],
        ["too many variations", "high-risk wrist/finger volume", "large bowling spike", "variation practice when sore"],
        ["can land stock ball under pressure", "can explain field", "can use one variation without losing stock control", "pain trend stable"],
        ["Intermediate spin should add deception without reducing control.", "Use conditions and handedness to decide what to teach next."]
    ),
    _teaching_record(
        "spin_bowling",
        "advanced",
        ["spinner", "wrist_spinner", "finger_spinner", "all_rounder"],
        "Create matchup-specific spin plans using stock-ball pressure, variations, field manipulation, and condition reading.",
        ["advanced club spinners", "academy spinners", "competitive all-rounders"],
        ["reliable stock ball", "variation tolerance", "clear spin family", "good tactical awareness"],
        ["variation sequencing", "drift/dip/turn control", "rough exploitation", "defensive and attacking fields", "batter setup plans", "format-specific risk"],
        ["spin axis intent", "same action for deception", "release disguise", "pace/flight precision", "crease-angle manipulation"],
        ["left/right matchup rules", "T20 boundary protection", "red-ball close-catcher pressure", "new batter plan", "sweep counter-plan"],
        ["shoulder durability", "wrist/finger capacity", "trunk stiffness", "long-spell aerobic support", "throwing load management"],
        ["scenario spells with field", "batter plan simulation", "condition-based target sets", "variation sequencing with caps"],
        ["rough attack spell", "T20 defensive field plan", "left-right partnership adjustment", "variation disguise review", "pressure-over simulation"],
        ["new variation overload", "bowling through wrist/finger symptoms", "ignoring wet ball/dew grip issues"],
        ["can maintain stock ball while varying", "has plan by batter hand and format", "can adjust when conditions change", "arm-load stable"],
        ["Advanced spin bowling is a tactical pressure system.", "Variation use should be justified by matchup and condition, not because it exists."]
    ),
    _teaching_record(
        "fielding",
        "beginner",
        ["fielder", "batter", "bowler", "wicketkeeper"],
        "Build safe ready position, ball tracking, ground-fielding basics, and catching confidence.",
        ["all cricket users", "new players", "users with weak fielding basics"],
        ["can move pain-free", "basic hand-eye coordination"],
        ["ready position", "approach angle", "long barrier", "two-hand pickup", "basic catching shapes", "safe stopping technique"],
        ["eyes to ball", "hips low", "hands soft", "body behind ball", "move through pickup"],
        ["stop runs first", "choose safe throw", "know high-risk vs safe option"],
        ["hip/ankle mobility", "deceleration", "adductor capacity", "trunk control", "hand/wrist tolerance"],
        ["low-speed reps", "predictable feeds", "confidence catches", "no fatigue diving"],
        ["tennis-ball catch ladder", "long barrier drill", "rolling pickup", "approach angle cone drill", "safe stop and return"],
        ["full-speed dives", "hard close catches", "fatigue throwing", "sliding on unsafe surface"],
        ["can stop rolling ball safely", "can catch basic feeds", "can move into pickup", "no knee/groin/wrist pain"],
        ["Every cricket role needs fielding basics.", "Beginner fielding should reduce fear and improve safe body position."]
    ),
    _teaching_record(
        "fielding",
        "intermediate",
        ["fielder", "batter", "bowler", "wicketkeeper"],
        "Add speed, angles, one-hand pickups, catching under movement, and position-specific fielding.",
        ["regular club players", "players who handle basic fielding safely"],
        ["basic catching and ground-fielding confidence", "safe deceleration"],
        ["pickup and release", "moving catches", "infield/outfield positioning", "dive progression", "boundary awareness"],
        ["attack the ball", "low hips through pickup", "feet set for throw", "soft hands on catch", "safe landing mechanics"],
        ["save one first", "create run-out chance when balanced", "know boundary vs infield priorities"],
        ["acceleration", "braking", "lateral movement", "shoulder/scapular control", "groin and hamstring resilience"],
        ["reactive feeds", "field-position constraints", "throw decision after pickup", "dive progressions on safe surface"],
        ["one-hand pickup ladder", "moving catch circuit", "infield run-out drill", "boundary relay drill", "low dive progression"],
        ["high throw volume without shoulder prep", "random full-speed diving", "throwing from unstable positions repeatedly"],
        ["can field at pace", "throws accurately after movement", "can select safe vs aggressive option", "soreness resolves normally"],
        ["Intermediate fielding blends skill and athletic movement.", "Throwing load must be counted separately from bowling."]
    ),
    _teaching_record(
        "fielding",
        "advanced",
        ["fielder", "infield", "outfield", "slips", "boundary_fielder"],
        "Specialize fielding by position, match phase, run-out creation, boundary protection, and pressure catching.",
        ["advanced club players", "academy players", "specialist fielders"],
        ["safe high-speed fielding", "throwing tolerance", "position familiarity"],
        ["position-specific start posture", "anticipation", "high-speed pickup", "diving/sliding", "relay systems", "pressure catches"],
        ["first step efficiency", "clean pickup at speed", "throw momentum", "landing control", "body orientation to target"],
        ["field to batter plan", "protect strong side", "boundary risk management", "cut angle to save two", "attack run-out when odds favor"],
        ["max-speed exposure", "reactive agility", "throwing power", "neck/shoulder resilience", "tissue capacity"],
        ["scenario fielding", "score-pressure catches", "position-specific drills", "throw volume management"],
        ["slip reaction block", "boundary catch and relay", "infield run-out pressure", "dive/slide on safe surface", "field placement scenario"],
        ["new slide technique in match week", "excess throws after shoulder soreness", "fatigue-only fielding volume"],
        ["can execute role-specific actions under pressure", "throw speed/accuracy stable", "understands tactical field purpose", "load trend safe"],
        ["Advanced fielding should create dismissals and prevent extra runs.", "Position context matters more than generic fielding drills."]
    ),
    _teaching_record(
        "throwing",
        "beginner",
        ["fielder", "wicketkeeper", "all_rounder"],
        "Build safe whole-body throwing mechanics and basic accuracy before speed.",
        ["new players", "players with poor throw accuracy", "users returning after shoulder soreness"],
        ["pain-free shoulder/elbow/wrist", "basic fielding stance"],
        ["side-on alignment", "step toward target", "whole-body sequencing", "easy overarm throw", "underarm release basics"],
        ["use legs and trunk", "elbow comfortable", "finish toward target", "throw at controllable effort"],
        ["choose underarm for close range", "do not force run-out from impossible position"],
        ["rotator cuff capacity", "scapular control", "thoracic rotation", "trunk control"],
        ["low-volume accuracy throws", "short distance first", "rest between sets", "symptom check"],
        ["underarm flick target", "step-and-throw", "short overarm accuracy", "catch-and-return", "wall target throws"],
        ["max-distance throws", "sidearm snap volume", "throwing through pain", "fatigue throw marathons"],
        ["can throw accurately at easy effort", "no next-day shoulder/elbow pain", "uses body not arm-only throw"],
        ["Throwing is a workload, not just a skill drill.", "Speed comes after sequencing and tolerance."]
    ),
    _teaching_record(
        "throwing",
        "intermediate",
        ["fielder", "wicketkeeper", "all_rounder"],
        "Improve throw speed, quick release, and accuracy after movement while managing arm load.",
        ["regular fielders", "players with safe basic throw"],
        ["pain-free easy throwing", "basic overarm and underarm accuracy"],
        ["momentum into throw", "pickup-to-release speed", "sidearm/relay options", "accuracy under time pressure"],
        ["hips and trunk lead", "stable front side", "quick feet before throw", "finish balanced"],
        ["select throw type by distance/time", "hit cutoff when better than direct throw", "avoid low-percentage hero throws"],
        ["rotational power", "shoulder endurance", "deceleration strength", "forearm tolerance"],
        ["throw ladders", "movement-to-throw drills", "volume caps", "recovery spacing"],
        ["one-hand pickup to throw", "crow-hop throw", "relay throw", "quick release run-out drill", "sidearm target low volume"],
        ["large volume spikes", "max throws after bowling", "throwing through soreness", "poor-surface full-speed pickups"],
        ["accuracy holds when moving", "can choose correct throw", "shoulder response stable", "throwing volume logged"],
        ["Intermediate throwing should balance speed and accuracy.", "Total arm load includes bowling plus throwing plus gym pressing."]
    ),
    _teaching_record(
        "throwing",
        "advanced",
        ["fielder", "wicketkeeper", "infield", "outfield"],
        "Specialize throwing by position, speed-accuracy tradeoff, release speed, and tactical decision-making.",
        ["advanced fielders", "wicketkeepers", "outfielders", "infield run-out specialists"],
        ["strong throwing base", "load history", "position-specific need"],
        ["throw velocity with control", "off-balance throw management", "relay systems", "keeper/infield quick release", "boundary long throw"],
        ["elastic sequencing", "front-leg block", "shoulder deceleration", "release angle", "quick transfer"],
        ["direct hit vs cutoff decision", "target end selection", "boundary relay", "run-out odds under pressure"],
        ["power throws", "rotator cuff/scapular capacity", "thoracic mobility", "trunk rotation", "recovery monitoring"],
        ["position-specific throw menu", "high-rest max throws", "accuracy scoring", "arm-care blocks"],
        ["outfield long throw set", "infield quick-release pressure", "keeper glove-to-stump throw", "relay decision game"],
        ["untracked max throws", "max throws with shoulder pain", "new arm slot under fatigue"],
        ["maintains accuracy at high intent", "knows tactical throw choice", "recovers between high-load days", "no pain trend"],
        ["Advanced throwing is a performance skill with injury cost.", "The app should cap volume and watch shoulder/elbow trends."]
    ),
    _teaching_record(
        "wicketkeeping",
        "beginner",
        ["wicketkeeper"],
        "Build stance comfort, glove path, basic takes, footwork, and safe crouch tolerance.",
        ["new wicketkeepers", "backup keepers", "players learning keeper basics"],
        ["pain-free squat/crouch", "basic catching confidence", "gloves and protective equipment"],
        ["ready stance", "head and eyes level", "soft hands", "basic lateral step", "standing back take", "safe crouch breaks"],
        ["hands rise with ball", "quiet head", "weight on balls of feet", "move feet before reaching"],
        ["secure take first", "avoid flashy stumpings before clean takes"],
        ["hip/ankle mobility", "quad/adductor endurance", "trunk endurance", "forearm and hand tolerance"],
        ["short sets", "standing-back basics", "low catch confidence", "frequent rest from crouch"],
        ["glove path wall drill", "tennis-ball take", "lateral step catch", "crouch hold intervals", "basic standing-back feed"],
        ["long crouch volume", "standing up to pace", "hard leg-side takes", "diving when basic takes fail"],
        ["can hold stance comfortably", "can take basic balls cleanly", "no knee/hip/back irritation", "moves feet before hands"],
        ["Keeper progression depends on tolerance as much as skill.", "Do not overload crouch time early."]
    ),
    _teaching_record(
        "wicketkeeping",
        "intermediate",
        ["wicketkeeper"],
        "Add standing-up skills, leg-side takes, stumping mechanics, and repeated crouch-to-move capacity.",
        ["regular wicketkeepers", "club keepers", "players with clean standing-back takes"],
        ["basic stance and takes", "safe crouch tolerance", "lateral footwork"],
        ["standing up to spin/medium pace", "leg-side movement", "glove-to-stump speed", "take-and-throw", "keeper communication"],
        ["stay low but relaxed", "head follows ball", "hips move first", "hands soft to hard only at catch", "feet recover to stumps"],
        ["anticipate bowler plan", "know stumping chance", "manage byes and field communication"],
        ["adductor capacity", "quad endurance", "ankle/hip mobility", "trunk endurance", "reaction speed"],
        ["keeper-specific intervals", "standing-up feeds", "stumping reps with rests", "throwing volume tracking"],
        ["standing-up take ladder", "leg-side take drill", "stumping transfer drill", "keeper run-out drill", "crouch-to-lateral repeat"],
        ["high crouch volume plus heavy legs", "standing up to high pace without supervision", "throw volume after shoulder soreness"],
        ["can take both sides", "can stump without rushing", "crouch tolerance stable", "communicates field/bowler clearly"],
        ["Intermediate keeping is repeated skill under fatigue.", "Crouch exposure is a load variable."]
    ),
    _teaching_record(
        "wicketkeeping",
        "advanced",
        ["wicketkeeper"],
        "Specialize keeper tactics, standing-up/standing-back transitions, pressure dismissals, and match endurance.",
        ["advanced wicketkeepers", "competitive keepers", "specialist keepers"],
        ["strong crouch tolerance", "clean takes", "keeper-specific footwork", "throwing tolerance"],
        ["bowler-specific glove paths", "standing up to selected seamers", "leg-side high difficulty takes", "stumping disguise", "keeper field IQ"],
        ["pre-movement control", "late hands", "hips under ball", "fast transfer", "recovery step after take"],
        ["read batter movement", "support bowler plans", "communicate field changes", "pressure run-outs/stumpings"],
        ["keeper endurance", "hip/adductor tissue capacity", "reaction training", "shoulder/forearm durability", "recovery strategy"],
        ["match-simulation sets", "bowler-specific feeds", "fatigue-managed blocks", "dismissal scenario games"],
        ["standing-up pressure over", "leg-side take series", "stumping disguise drill", "keeper run-out under fatigue", "field communication scenario"],
        ["excess crouch volume during knee/hip/back pain", "new high-risk standing-up role before match", "throwing overload"],
        ["can maintain quality late in session", "knows bowler-specific plan", "dismissal execution under pressure", "symptoms stable"],
        ["Advanced keeping is a tactical leadership role, not only catching.", "The app should protect hips/knees/back with exposure tracking."]
    ),
    _teaching_record(
        "match_iq",
        "beginner",
        ["all_roles"],
        "Understand basic format, phase, field, ball age, and safe decision rules.",
        ["new cricket users", "general fitness users adding cricket", "recreational players"],
        ["knows basic rules and scoring"],
        ["format basics", "powerplay/middle/death idea", "red vs white ball", "field positions", "basic pitch labels"],
        ["observe ball behavior", "connect field to plan", "ask what is the safe option"],
        ["bat straight early", "bowl at stumps/top of off", "stop runs first in field"],
        ["general conditioning", "heat tolerance", "mobility for long fielding"],
        ["simple scenario questions", "watch-and-label drills", "coach-guided decisions"],
        ["field map naming", "ball age quiz", "phase decision cards", "basic toss discussion", "safe option scenario"],
        ["complex matchup overload", "advanced field manipulation", "uncertain weather claims as facts"],
        ["can identify innings phase", "can explain simple field", "can adapt basic risk to score/overs"],
        ["Beginner IQ should make play safer and less random.", "Label evidence strength when teaching conditions."]
    ),
    _teaching_record(
        "match_iq",
        "intermediate",
        ["all_roles"],
        "Apply pitch, ball age, weather, field, batter hand, and match phase to tactical choices.",
        ["club players", "school/college players", "users who know core rules"],
        ["basic format and field knowledge", "role familiarity"],
        ["condition reading", "ball age strategy", "field plus bowling plan", "batting tempo", "dew and wet ball response"],
        ["observe first overs", "update plan after evidence", "separate tradition from actual behavior"],
        ["change line/length by surface", "protect boundary by phase", "rotate strike by field", "use matchup basics"],
        ["heat management", "footing/deceleration", "wet-ball grip tolerance"],
        ["scenario cards", "pre-match checklist", "between-over review", "field-setting games"],
        ["green pitch plan", "slow pitch batting plan", "dew bowling plan", "left-right partnership field transitions", "rain interruption decision"],
        ["fixed plan despite evidence", "overclaiming humidity/overcast effects", "ignoring local boundary/skill context"],
        ["can justify plan from condition", "updates after live evidence", "knows format-specific risk", "uses field with bowling/batting plan"],
        ["Intermediate cricket IQ is live decision-making.", "The backend should store evidence labels for condition claims."]
    ),
    _teaching_record(
        "match_iq",
        "advanced",
        ["all_roles", "captain", "senior_player"],
        "Build role-specific match plans, opposition matchups, toss logic, and adaptive in-game decision frameworks.",
        ["captains", "senior players", "advanced competitive users"],
        ["strong rules knowledge", "role-specific skill base", "match review habit"],
        ["opposition analysis", "toss and innings strategy", "field manipulation", "matchup plans", "phase-specific risk budget", "tournament load decisions"],
        ["read evidence early", "communicate plan clearly", "pre-plan contingencies", "review outcomes objectively"],
        ["attack/defend windows", "batter/bowler matchup sequencing", "condition-based role use", "protect best fielders/weak fielders"],
        ["fatigue management", "heat/travel recovery", "role-load adjustment"],
        ["pre-match planning template", "opposition scenario", "post-match review", "captaincy decision tree"],
        ["toss decision matrix", "field-to-plan simulation", "matchup review", "tournament rotation plan", "condition update log"],
        ["strategy without evidence", "too many plan changes", "ignoring player fatigue or injury risk"],
        ["can build and revise plan", "uses evidence labels", "protects workload", "connects tactics to available players"],
        ["Advanced IQ should improve decisions, not create complicated noise.", "The app should store plan, evidence, and review outcome."]
    ),
    _teaching_record(
        "cricket_snc",
        "beginner",
        ["all_roles"],
        "Build a broad athletic base that supports cricket without over-specialization.",
        ["new cricket users", "returning players", "youth and recreational players"],
        ["medical clearance if injured", "basic movement tolerance"],
        ["movement quality", "basic strength", "low-impact conditioning", "mobility", "landing/deceleration basics", "throwing/bowling load awareness"],
        ["hinge/squat/lunge/push/pull/carry basics", "trunk brace", "hip/ankle mobility", "shoulder control"],
        ["understand role load", "do not train hard before match", "log cricket practice"],
        ["general strength", "aerobic base", "calf/hamstring/adductor capacity", "scapular control"],
        ["2-4 gym sessions", "low soreness", "simple progression", "cricket load log"],
        ["goblet squat", "hinge pattern", "split squat", "row", "carry", "dead bug", "dynamic warmup", "easy tempo runs"],
        ["advanced plyometrics", "max lifts", "high-volume bowling plus heavy spine loading", "painful impact"],
        ["completes sessions", "no worsening pain", "basic patterns stable", "recovers between cricket and gym"],
        ["Beginner S&C should create availability and movement quality.", "Skill load counts as training load."]
    ),
    _teaching_record(
        "cricket_snc",
        "intermediate",
        ["all_roles", "batter", "bowler", "wicketkeeper"],
        "Develop role-specific strength, power, speed, durability, and match-week load management.",
        ["regular cricket players", "users with stable training habit"],
        ["basic movement quality", "consistent training", "known role"],
        ["role-led programming", "sprint and deceleration exposure", "rotational power", "shoulder/trunk durability", "fielding athleticism", "match-week taper"],
        ["quality reps", "RPE control", "jump/throw mechanics", "anti-rotation", "single-leg control"],
        ["adjust gym by match and practice load", "separate high stress days", "monitor pain/readiness"],
        ["strength base", "power conversion", "repeat sprint ability", "throwing/bowling capacity", "mobility maintenance"],
        ["block planning", "load monitoring", "role-specific accessories", "deload/taper weeks"],
        ["trap bar or squat pattern", "RDL", "split squat", "med ball throw", "acceleration drill", "rotator cuff series", "adductor/calf capacity"],
        ["all-out circuits before match", "new plyometrics during pain", "rapid bowling or throwing load spikes"],
        ["progresses load or reps", "role skill load tolerated", "readiness stable", "match performance not impaired by gym soreness"],
        ["Intermediate cricket S&C should support role performance.", "Hard days should be placed logically around skill practice."]
    ),
    _teaching_record(
        "cricket_snc",
        "advanced",
        ["all_roles", "advanced_athlete"],
        "Periodize cricket-specific performance qualities while managing competition, travel, fatigue, and role conflicts.",
        ["advanced competitive players", "academy players", "serious athletes"],
        ["training history", "role clarity", "load tracking", "stable injury profile"],
        ["macro blocks", "strength-to-power conversion", "high-speed exposure", "role-specific tissue capacity", "competition taper", "return-to-play rules"],
        ["precise load intent", "velocity/explosive quality", "fatigue management", "technical preservation under load"],
        ["use match schedule to choose stress", "protect fast bowlers and all-rounders", "maintenance in season"],
        ["max strength when appropriate", "power and speed", "elastic capacity", "shoulder/trunk endurance", "recovery systems"],
        ["planned blocks", "testing/retest", "athlete_state review", "competition-week adjustments"],
        ["contrast power block", "high-quality acceleration", "med ball rotation", "heavy lower body away from bowling peaks", "match-week primer", "recovery session"],
        ["random novelty", "high soreness near match", "progressing volume and intensity together", "ignoring pain trend"],
        ["performance trend improves", "load is planned and reviewed", "fatigue does not accumulate blindly", "next block reflects athlete_state"],
        ["Advanced S&C needs a macro plan plus rolling athlete state.", "The AI should choose what/when/why; database supplies safe execution and rules."]
    )
]


SKILL_ASSESSMENTS: List[Dict[str, Any]] = [
    {
        "id": "cricket_assess_batting_level",
        "sport": "cricket",
        "domain": "batting",
        "summary": "Assesses batting level by setup stability, shot control, decision quality, and tactical role clarity.",
        "level_bands": [
            {"level": "beginner", "indicators": ["needs predictable feeds", "limited shot range", "uncertain leave/defend/score choices"], "ready_for_next_when": ["stable stance and head", "basic defense/drive/back-foot option", "safe running calls"]},
            {"level": "intermediate", "indicators": ["handles variable feeds", "has basic pace and spin plans", "can rotate strike"], "ready_for_next_when": ["uses field and phase", "controls sweep/cut/pull choices", "keeps shape under pressure"]},
            {"level": "advanced", "indicators": ["role-specific plan", "matchup awareness", "tempo control", "pressure scoring options"], "ready_for_next_when": ["maintains high decision quality across formats and conditions"]}
        ],
        "hold_if": ["fear or unsafe response to ball speed", "wrist/back pain from batting volume", "decision quality collapses under simple variability"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("batting")
    },
    {
        "id": "cricket_assess_pace_bowling_level",
        "sport": "cricket",
        "domain": "pace_bowling",
        "summary": "Assesses pace bowling by action repeatability, stock accuracy, variation readiness, and workload tolerance.",
        "level_bands": [
            {"level": "beginner", "indicators": ["inconsistent run-up", "stock line/length unstable", "no bowling log"], "ready_for_next_when": ["run-up mark stable", "stock length repeated", "no next-day back pain"]},
            {"level": "intermediate", "indicators": ["stock ball stable", "can plan new/old ball basics", "variation introduced"], "ready_for_next_when": ["one variation controlled", "spell load tolerated", "line changes by batter hand"]},
            {"level": "advanced", "indicators": ["phase-specific weapons", "batter setup plans", "workload managed"], "ready_for_next_when": ["sustains quality and recovery across match blocks"]}
        ],
        "hold_if": ["back pain", "bowling spike after layoff", "youth workload exceeds guidance", "accuracy drops sharply with speed intent"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("pace_bowling")
    },
    {
        "id": "cricket_assess_spin_bowling_level",
        "sport": "cricket",
        "domain": "spin_bowling",
        "summary": "Assesses spin bowling by stock-ball control, variation readiness, field/tactical understanding, and arm-load tolerance.",
        "level_bands": [
            {"level": "beginner", "indicators": ["stock ball inconsistent", "unclear spin family", "variation chasing"], "ready_for_next_when": ["stock ball lands in target", "legal repeatable action", "no wrist/finger pain"]},
            {"level": "intermediate", "indicators": ["stock ball stable", "uses pace/flight or one variation", "basic handedness plan"], "ready_for_next_when": ["variation does not reduce stock control", "field plan clear", "load tolerated"]},
            {"level": "advanced", "indicators": ["matchup plans", "condition-based fields", "variation sequencing"], "ready_for_next_when": ["adapts under pressure while preserving stock-ball threat"]}
        ],
        "hold_if": ["wrist/finger soreness", "loss of stock-ball control", "possible illegal-action concern", "too many new variations"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("spin_bowling")
    },
    {
        "id": "cricket_assess_fielding_throwing_level",
        "sport": "cricket",
        "domain": "fielding_throwing",
        "summary": "Assesses fielding and throwing by safe movement, catch/pickup quality, throw selection, speed-accuracy balance, and arm-load tolerance.",
        "level_bands": [
            {"level": "beginner", "indicators": ["basic catching or ground-fielding inconsistent", "arm-only throw"], "ready_for_next_when": ["safe stop", "basic catch", "accurate easy throw"]},
            {"level": "intermediate", "indicators": ["fields at movement speed", "quick pickup emerging", "throws after movement"], "ready_for_next_when": ["speed and accuracy stable", "throw decision appropriate", "shoulder response stable"]},
            {"level": "advanced", "indicators": ["position-specific skill", "pressure catches", "run-out creation"], "ready_for_next_when": ["role-specific execution under match pressure"]}
        ],
        "hold_if": ["shoulder or elbow pain", "unsafe diving/landing", "throwing load spike", "fear response to catches"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("fielding")
    },
    {
        "id": "cricket_assess_wicketkeeping_level",
        "sport": "cricket",
        "domain": "wicketkeeping",
        "summary": "Assesses wicketkeeping by stance tolerance, glove path, lateral movement, standing-up skill, and dismissal execution.",
        "level_bands": [
            {"level": "beginner", "indicators": ["stance uncomfortable", "basic takes inconsistent"], "ready_for_next_when": ["clean standing-back takes", "safe crouch tolerance", "basic lateral step"]},
            {"level": "intermediate", "indicators": ["standing up introduced", "stumping mechanics developing"], "ready_for_next_when": ["takes both sides", "stumping without rush", "crouch load tolerated"]},
            {"level": "advanced", "indicators": ["bowler-specific keeping", "pressure dismissals", "field communication"], "ready_for_next_when": ["quality maintained late in match blocks"]}
        ],
        "hold_if": ["knee/hip/back pain", "crouch tolerance poor", "throwing soreness", "standing-up risk exceeds skill"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("wicketkeeping")
    },
    {
        "id": "cricket_assess_match_iq_level",
        "sport": "cricket",
        "domain": "match_iq",
        "summary": "Assesses tactical level by format knowledge, condition reading, field-plan logic, and adaptive decision-making.",
        "level_bands": [
            {"level": "beginner", "indicators": ["knows basic rules but not phase/field logic"], "ready_for_next_when": ["identifies phase", "understands basic field", "chooses safe option"]},
            {"level": "intermediate", "indicators": ["connects pitch/ball age/field to plan"], "ready_for_next_when": ["updates plan from evidence", "uses handedness and format"]},
            {"level": "advanced", "indicators": ["opposition and matchup planning", "captaincy decisions", "review loop"], "ready_for_next_when": ["plans and revises under competition constraints"]}
        ],
        "hold_if": ["uses fixed plan despite live evidence", "overclaims conditions", "ignores player fatigue or skill level"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("match_iq")
    }
]


LEVEL_TRANSITION_RULES: List[Dict[str, Any]] = [
    {
        "id": "cricket_level_beginner_to_intermediate_general",
        "sport": "cricket",
        "from_level": "beginner",
        "to_level": "intermediate",
        "applies_to": ["all_roles"],
        "minimum_evidence": ["4+ weeks or 8+ cricket/S&C sessions", "85% planned session completion", "no worsening pain trend", "basic movement/skill checklist passed"],
        "promote_when": ["stock skill is repeatable in predictable practice", "user can explain simple tactical choice", "load response is stable"],
        "hold_when": ["pain worsening", "completion below 65%", "skill breaks under simple variability", "unsafe movement pattern"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("cricket_snc")
    },
    {
        "id": "cricket_level_intermediate_to_advanced_general",
        "sport": "cricket",
        "from_level": "intermediate",
        "to_level": "advanced",
        "applies_to": ["all_roles"],
        "minimum_evidence": ["8+ additional weeks or 16+ sessions", "consistent skill and physical progression", "stable recovery", "role-specific assessment passed"],
        "promote_when": ["user adapts to variable practice", "tactical decisions match role and format", "training load is tracked and tolerated"],
        "hold_when": ["repeated failed sessions", "high fatigue/readiness risk", "unresolved pain flags", "no role clarity"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("cricket_snc")
    },
    {
        "id": "cricket_level_pace_bowler_safety_override",
        "sport": "cricket",
        "from_level": "any",
        "to_level": "hold_or_regress",
        "applies_to": ["pace_bowler", "all_rounder", "youth_fast_bowler"],
        "minimum_evidence": ["back pain", "bowling workload spike", "large layoff then high-intent bowling", "youth workload cap exceeded"],
        "promote_when": [],
        "hold_when": ["lumbar pain", "spike in balls/overs", "poor recovery after spells", "unsafe speed chasing"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("pace_bowling")
    },
    {
        "id": "cricket_level_spin_variation_unlock",
        "sport": "cricket",
        "from_level": "intermediate",
        "to_level": "advanced_variation_access",
        "applies_to": ["spinner", "all_rounder"],
        "minimum_evidence": ["stock ball control stable", "no wrist/finger pain trend", "variation reps tolerated", "field plan understood"],
        "promote_when": ["variation does not reduce stock accuracy", "same action is preserved", "variation has tactical purpose"],
        "hold_when": ["stock ball deteriorates", "pain increases", "user wants many variations at once"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("spin_bowling")
    },
    {
        "id": "cricket_level_wicketkeeper_crouch_load_gate",
        "sport": "cricket",
        "from_level": "beginner",
        "to_level": "intermediate",
        "applies_to": ["wicketkeeper"],
        "minimum_evidence": ["pain-free crouch tolerance", "basic standing-back takes", "lateral footwork control"],
        "promote_when": ["clean takes both sides", "crouch exposure tolerated", "no knee/hip/back pain trend"],
        "hold_when": ["crouch pain", "poor stance recovery", "missed basic takes due to rushing"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("wicketkeeping")
    },
    {
        "id": "cricket_level_youth_growth_safety_override",
        "sport": "cricket",
        "from_level": "any",
        "to_level": "hold_or_conservative_progression",
        "applies_to": ["youth_player", "youth_fast_bowler"],
        "minimum_evidence": ["growth spurt", "inconsistent recovery", "multi-team workload", "back/shoulder/knee pain"],
        "promote_when": [],
        "hold_when": ["maturation risk high", "coordination temporarily reduced", "workload from multiple teams not tracked"],
        "source_pack_id": SOURCE_PACK_ID,
        "source_refs": _source_refs("cricket_snc")
    }
]


def _source_sections() -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    docs: List[Dict[str, Any]] = []
    order = 50000
    for domain, file_names in DOMAIN_DRAFTS.items():
        order += 1
        summaries = []
        for file_name in file_names:
            draft = _load_draft(file_name)
            if draft.get("executive_summary"):
                summaries.append(str(draft["executive_summary"]))
        docs.append({
            "id": f"cricket_teaching_section_{domain}",
            "source_book_id": SOURCE_PACK_ID,
            "section_order": order,
            "section_title": f"Cricket {domain.replace('_', ' ').title()} Teaching Progression",
            "domain": "cricket_level_teaching",
            "topics": ["cricket", domain, "beginner", "intermediate", "advanced", "teaching_progression"],
            "summary": " ".join(summaries)[:1200],
            "source_refs": _source_refs(domain),
            "created_at": now,
            "updated_at": now,
        })
    return docs


def _with_metadata(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.utcnow()
    return [
        {
            **record,
            "ingestion_method": INGESTION_METHOD,
            "version": "v1.0.0",
            "created_at": now,
            "updated_at": now,
        }
        for record in records
    ]


def build_database() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": SOURCE_PACK_ID,
            "title": "SFTC Cricket Level-Based Teaching Database",
            "sport": "cricket",
            "version": "v1.0.0",
            "description": "App-facing cricket teaching progressions by domain and level, derived from structured cricket research drafts.",
            "domains": sorted(DOMAIN_DRAFTS),
            "levels": ["beginner", "intermediate", "advanced"],
        },
        "sport_teaching_progressions": TEACHING_PROGRESSIONS,
        "sport_skill_assessments": SKILL_ASSESSMENTS,
        "sport_level_transition_rules": LEVEL_TRANSITION_RULES,
    }


def export_database(path: Path = OUTPUT_PATH) -> Dict[str, Any]:
    payload = build_database()
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


async def _upsert_many(db: Any, collection_name: str, docs: Sequence[Dict[str, Any]]) -> int:
    count = 0
    collection = db[collection_name]
    for doc in docs:
        if not doc.get("id"):
            continue
        await collection.replace_one({"id": doc["id"]}, doc, upsert=True)
        count += 1
    return count


async def ingest(export_only: bool = False) -> Dict[str, int]:
    payload = export_database()
    if export_only:
        return {
            "exported_sport_teaching_progressions": len(payload["sport_teaching_progressions"]),
            "exported_sport_skill_assessments": len(payload["sport_skill_assessments"]),
            "exported_sport_level_transition_rules": len(payload["sport_level_transition_rules"]),
        }

    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await ensure_database_schema(db)

    now = datetime.utcnow()
    source_doc = {
        "id": SOURCE_PACK_ID,
        "title": payload["metadata"]["title"],
        "source_type": "curated_research_database",
        "sport": "cricket",
        "summary": payload["metadata"]["description"],
        "source_files": sorted(str((DRAFT_DIR / file_name).relative_to(PROJECT_ROOT)) for files in DOMAIN_DRAFTS.values() for file_name in files),
        "created_at": now,
        "updated_at": now,
    }
    counts: Dict[str, int] = {}
    for collection_name in ("source_registry", "knowledge_sources"):
        await db[collection_name].replace_one({"id": SOURCE_PACK_ID}, source_doc, upsert=True)
        counts[collection_name] = 1

    counts["source_sections"] = await _upsert_many(db, "source_sections", _source_sections())
    counts["sport_teaching_progressions"] = await _upsert_many(
        db,
        "sport_teaching_progressions",
        _with_metadata(payload["sport_teaching_progressions"]),
    )
    counts["sport_skill_assessments"] = await _upsert_many(
        db,
        "sport_skill_assessments",
        _with_metadata(payload["sport_skill_assessments"]),
    )
    counts["sport_level_transition_rules"] = await _upsert_many(
        db,
        "sport_level_transition_rules",
        _with_metadata(payload["sport_level_transition_rules"]),
    )
    client.close()
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and ingest cricket level-based teaching database.")
    parser.add_argument("--export-only", action="store_true", help="Only write the JSON export file; do not write MongoDB.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = asyncio.run(ingest(export_only=args.export_only))
    for collection, count in counts.items():
        print(f"{collection}: {count}")
    print(f"export: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
