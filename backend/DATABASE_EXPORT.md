# MongoDB Database Export

- Database: `test_database`
- Exported: `2026-06-16T07:52:12.044661Z`
- Mongo URL: `[redacted/local configured URL]`

## Collection Counts

| Collection | Documents |
|---|---:|
| `athlete_profiles` | 0 |
| `benchmark_tests` | 0 |
| `coach_daily_analyses` | 0 |
| `coach_goals` | 0 |
| `coach_meals` | 0 |
| `coach_relationships` | 0 |
| `coach_requests` | 0 |
| `coach_workouts` | 0 |
| `coaching_progressions` | 50 |
| `daily_snapshots` | 0 |
| `equipment_library` | 0 |
| `exercise_library` | 161 |
| `exercise_results` | 0 |
| `glossary_terms` | 40 |
| `health_metrics` | 0 |
| `injuries` | 0 |
| `injury_logs` | 0 |
| `injury_modifications` | 0 |
| `journal_entries` | 0 |
| `knowledge_extraction_runs` | 4 |
| `knowledge_sources` | 1 |
| `lessons` | 0 |
| `meals` | 0 |
| `mobility_drills` | 33 |
| `moods` | 0 |
| `movement_patterns` | 0 |
| `nutrition_guidelines` | 0 |
| `nutrition_principles` | 27 |
| `nutrition_targets` | 0 |
| `otps` | 0 |
| `physical_qualities` | 0 |
| `program_blocks` | 0 |
| `programming_rules` | 173 |
| `progression_rules` | 0 |
| `quick_logs` | 0 |
| `readiness_rules` | 0 |
| `recovery_rules` | 6 |
| `run_club_memberships` | 0 |
| `run_clubs` | 0 |
| `running_plan_rules` | 0 |
| `running_workouts` | 0 |
| `sleep_sessions` | 0 |
| `source_registry` | 0 |
| `source_sections` | 91 |
| `sport_profiles` | 0 |
| `sport_roles` | 0 |
| `sport_training_rules` | 0 |
| `technical_errors` | 36 |
| `technical_models` | 137 |
| `terra_feed_posts` | 0 |
| `terra_reflections` | 0 |
| `terra_runs` | 0 |
| `terra_training_plans` | 0 |
| `training_principles` | 56 |
| `training_programs` | 0 |
| `users` | 0 |
| `workout_sessions` | 0 |
| `workout_templates` | 0 |
| `workouts` | 0 |

## Notes

- Empty app-user collections mean there are currently no saved accounts, workouts, meals, or runs in this local database.
- Knowledge collections currently come from the Olympic Weightlifting EPUB ingestion.
- Long fields are truncated for readability. This file is an inspection export, not a backup.

## `knowledge_sources` Samples

Showing `1` of `1` documents.

### 1. Olympic Weightlifting: A Complete Guide for Athletes & Coaches, Third Edition

```json
{
  "id": "olympic_weightlifting_complete_guide_3rd_ed",
  "author": "Greg Everett",
  "copyright_handling": "Stores normalized metadata, tags, hashes, and source references; does not store full book prose.",
  "created_at": "2026-06-11T08:04:24.508000",
  "exercise_count": 161,
  "extraction_scope": [
    "complete_epub_section_index",
    "supplemental_exercise_library",
    "major_training_topic_index",
    "technical_models",
    "technical_errors",
    "coaching_progressions",
    "programming_rules",
    "recovery_rules",
    "... 3 more"
  ],
  "file_name": "dokumen.pub_olympic-weightlifting-a-complete-guide-for-athletes-amp-coaches-3nbsped.epub",
  "file_path": "/Users/vamshikrishna/Downloads/Fitness-App-main/dokumen.pub_olympic-weightlifting-a-complete-guide-for-athletes-amp-coaches-3nbsped.epub",
  "file_sha256": "4f390bad275d826808350ce280ca0af3cf4171e13cc47c3e333890abdd6d3c23",
  "publisher": "Catalyst Athletics",
  "section_count": 91,
  "source_type": "epub",
  "title": "Olympic Weightlifting: A Complete Guide for Athletes & Coaches, Third Edition",
  "updated_at": "2026-06-11T08:04:24.508000",
  "version": "v1.0.0",
  "word_count": 318502
}
```

## `exercise_library` Samples

Showing `20` of `161` documents.

### 1. 2-Position / 3-Position Power Snatch

```json
{
  "id": "ow_ex_2_position_3_position_power_snatch",
  "category": "power",
  "coaching_cues": [
    "If performed bottom to top, the 2-position or 3-position power snatch helps primarily with rate of force development, more aggressive and complete extension at the top of the.",
    "If performed from the top down, it can serve as more of a technique exercise that reinforces proper position in the pull at the hang positions chosen, or to gradually prepare a.",
    "The 2-position or 3-position power snatch is simply 2-3 power snatches performed from 2-3 progressive (increasing or decreasing height) starting positions consecutively.",
    "Typically the set will start from the floor and move to progressively higher hang positions; for example, from the floor, then from the knee, then from mid-thigh).",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.302000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "2-Position / 3-Position Power Snatch",
  "note_count_hint": 0,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-85%"
    ],
    "placement_tags": [
      "may_be_loaded_heavily_when_appropriate"
    ],
    "has_programming_guidance": true
  },
  "regressions": [
    "3-position power snatch include different hang positions",
    "pauses in the hang position",
    "pauses in the receiving position",
    "Variations of the 2-position"
  ],
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "2-Position / 3-Position Power Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "f4620b5caed7f93835dfdcd4da695067944335c26a34b0671ecac55219280f71",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "3-position power snatch include different hang positions",
    "pauses in the hang position",
    "pauses in the receiving position",
    "Variations of the 2-position"
  ],
  "summary": "The 2-position or 3-position power snatch is simply 2-3 power snatches performed from 2-3 progressive (increasing or decreasing height) starting positions consecutively. Typically the set will start from the floor and move to progressively higher hang positions; for example, from the floor, then from the knee, then.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "snatch_skill",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.302000",
  "usage_context": [
    "advanced_or_heavy_training",
    "beginner_or_learning_lifter",
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "... 3 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 2. 2-Position / 3-Position Snatch

```json
{
  "id": "ow_ex_2_position_3_position_snatch",
  "category": "power",
  "coaching_cues": [
    "If performed bottom to top, the 2-position or 3-position snatch helps primarily with rate of force development, more aggressive and complete extension at the top of the pull, and.",
    "If performed from the top down, it can serve as more of a technique exercise that reinforces proper position in the pull at the hang positions chosen, or to gradually prepare a.",
    "The 2-position or 3-position snatch is simply 2-3 snatches performed from 2-3 progressive (increasing or decreasing height) starting positions consecutively.",
    "Typically the set will start from the floor and move to progressively higher hang positions; for example, from the floor, then from the knee, then from mid-thigh).",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.303000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "2-Position / 3-Position Snatch",
  "note_count_hint": 0,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-85%"
    ],
    "placement_tags": [
      "may_be_loaded_heavily_when_appropriate"
    ],
    "has_programming_guidance": true
  },
  "regressions": [
    "3-position snatch include different hang positions",
    "pauses in the hang position",
    "pauses in the receiving position",
    "Variations of the 2-position"
  ],
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "2-Position / 3-Position Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "e3b811902e22b3865e80d4d272aff14bd7cc6a2d245b12bb13ba66ba120bba16",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "3-position snatch include different hang positions",
    "pauses in the hang position",
    "pauses in the receiving position",
    "Variations of the 2-position"
  ],
  "summary": "The 2-position or 3-position snatch is simply 2-3 snatches performed from 2-3 progressive (increasing or decreasing height) starting positions consecutively. Typically the set will start from the floor and move to progressively higher hang positions; for example, from the floor, then from the knee, then from.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "snatch_skill",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.303000",
  "usage_context": [
    "advanced_or_heavy_training",
    "beginner_or_learning_lifter",
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "... 3 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 3. Barksi Snatch

```json
{
  "id": "ow_ex_barksi_snatch",
  "category": "power",
  "coaching_cues": [
    "This exercise is a great snatch grip strength developer, and will also help in improving the aggressiveness and completeness of the final extension and turnover.",
    "Not all coaches and athletes agree what constitutes “high hang”.",
    "Typically this is a bar starting height above mid-thigh, but it may or may not involve a forward lean of the torso (i.e."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.303000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Barksi Snatch",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "placement_tags": [
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Barksi Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "24ed63cefa5cf2ad2b070c8c3ee1caceb586f02d3a727ed6cbf99d9f3e69251e",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "The Barksi snatch can be performed as power snatches",
    "without the hook grip for even greater grip work"
  ],
  "summary": "The Barksi snatch, named for Bob Bednarksi, is simply a high-hang snatch triple performed without using straps. The lifter will perform 3 consecutive high-hang snatches without using straps and without setting the bar down between reps.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "snatch_skill",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.303000",
  "usage_context": [
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "snatch_skill",
    "strength"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 4. Block Power Snatch

```json
{
  "id": "ow_ex_block_power_snatch",
  "aliases": [
    "Power snatch from blocks",
    "power snatch off blocks"
  ],
  "category": "power",
  "coaching_cues": [
    "The block power snatch will force the lifter to accelerate the bar more rapidly because of the limited distance available to accelerate, and because it’s beginning from a dead.",
    "When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be during a.",
    "Notes: When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be.",
    "Purpose: The block power snatch will force the lifter to accelerate the bar more rapidly because of the limited distance available to accelerate, and because it’s beginning from a.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.305000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, snatch skill, strength.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "blocks",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Block Power Snatch",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-90%"
    ],
    "rep_ranges": [
      "1-3 reps"
    ],
    "placement_tags": [
      "can_be_used_light_for_technique",
      "may_be_loaded_heavily_when_appropriate"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Block Power Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "e675b16532338debd02460e4d35c8f8245b6b1131585d959e1a19695c5a98e62",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "limit pulling distance"
  ],
  "summary": "The block power snatch is an exercise that can serve a number of purposes depending on the lifter’s or coach’s goals. The block power snatch should be performed identically to the power snatch except that the bar begins resting on blocks instead of the floor.",
  "training_qualities": [
    "explosive_power",
    "snatch_skill",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.305000",
  "usage_context": [
    "advanced_or_heavy_training",
    "explosive_power",
    "mobility_limitation",
    "program_design",
    "recovery",
    "... 3 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 5. Block Snatch

```json
{
  "id": "ow_ex_block_snatch",
  "aliases": [
    "Snatch from blocks",
    "snatch off blocks"
  ],
  "category": "power",
  "coaching_cues": [
    "The block snatch will force the lifter to accelerate the bar more rapidly because of the limited distance available to accelerate, and because it’s beginning from a dead stop with.",
    "When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be during a.",
    "Notes: When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be.",
    "Purpose: The block snatch will force the lifter to accelerate the bar more rapidly because of the limited distance available to accelerate, and because it’s beginning from a dead.",
    "... 2 more"
  ],
  "common_errors": [
    "Some lifters will be able to snatch more from certain block heights than they can from the floor—this is not necessarily a problem, although it can be an indicator of technical or.",
    "The block snatch may be used as a way for a lifter who has a problem lifting from the floor to train the snatch heavy while this problem is being addressed; it can also be a way."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.307000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, snatch skill, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "blocks",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Block Snatch",
  "note_count_hint": 1,
  "paragraph_count": 7,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "placement_tags": [
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Block Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "bef7de235bf0efd0c08ee5f36871247aa953b0dcffb6bb9d58847663a98d3f29",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "may not be used depending on what’s appropriate for the athlete at the time"
  ],
  "summary": "The block snatch should be performed identically to the snatch except that the bar begins resting on blocks instead of the floor. The most common block heights are at the knee and below the knee.",
  "training_qualities": [
    "explosive_power",
    "snatch_skill",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.307000",
  "usage_context": [
    "explosive_power",
    "mobility_limitation",
    "program_design",
    "recovery",
    "snatch_skill",
    "... 1 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 6. Block Snatch High-Pull

```json
{
  "id": "ow_ex_block_snatch_high_pull",
  "aliases": [
    "Snatch high-pull from blocks",
    "snatch high-pull off blocks"
  ],
  "category": "power",
  "coaching_cues": [
    "The block snatch high-pull is a way to train the final extension and upper body movement of the snatch high-pull with reduced fatigue and overall training load on the athlete, or.",
    "It can also be used as a way to emphasize upper body strength development for the initial pull down in the third pull by reducing the contribution of the legs to the barbell’s.",
    "When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be during a.",
    "The block snatch high-pull should be performed identically to the snatch high-pull except that the bar begins resting on blocks instead of the floor.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.307000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, strength.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "blocks",
    "plates"
  ],
  "exercise_family": "pull",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Block Snatch High-Pull",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-85%"
    ],
    "rep_ranges": [
      "3-5 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Block Snatch High-Pull"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "aec7e9f66dd6ce7dc0db41f59a6994667c875c95342b45ba652f9c61f5bde6a3",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "it can be performed without straps"
  ],
  "summary": "The block snatch high-pull should be performed identically to the snatch high-pull except that the bar begins resting on blocks instead of the floor. The most common block heights are at the knee and below the knee.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.307000",
  "usage_context": [
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 7. Block Snatch Pull

```json
{
  "id": "ow_ex_block_snatch_pull",
  "aliases": [
    "Snatch pull from blocks",
    "snatch pull off blocks"
  ],
  "category": "power",
  "coaching_cues": [
    "The block snatch pull is a way to train the final extension with reduced fatigue and overall training load on the athlete, to give the legs and back a break during periods of very.",
    "It can also be used simply for variety if an athlete is doing frequent pulling in a training cycle, in which case it would be used in addition to snatch pulls, probably on.",
    "Finally, it can be used to significantly overload the snatch pull by removing the portion of the pull where the lifter struggles the most (from the floor to the knee, typically).",
    "When lifting from the blocks, the pressure on the feet prior to the bar being separated from the blocks will need to be farther back toward the heels than it would be during a.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.309000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, strength.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "blocks",
    "plates"
  ],
  "exercise_family": "pull",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Block Snatch Pull",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "130%",
      "90-120%"
    ],
    "rep_ranges": [
      "3-5 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Block Snatch Pull"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "cc6473fd247fcc3c7e8e371e688cfb30245e4c5f15b79f1366a28b79f68b909e",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "summary": "The block snatch pull should be performed identically to the snatch pull except that the bar begins resting on blocks instead of the floor. The most common block heights are at the knee and below the knee.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.309000",
  "usage_context": [
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength"
  ],
  "variation_count_hint": 0,
  "version": "v1.0.0"
}
```

### 8. Clean-Grip Snatch

```json
{
  "id": "ow_ex_clean_grip_snatch",
  "aliases": [
    "close-grip snatch",
    "narrow-grip snatch"
  ],
  "category": "weightlifting_skill",
  "coaching_cues": [
    "The clean-grip snatch can be used for different reasons, such as improving turnover strength, mobility, and maintaining proximity of the bar to the body.",
    "The narrower grip means that the bar will contact the body below the hips, meaning that the athlete will need to work even harder to keep the bar close to the body.",
    "The athlete will need to focus on pulling the elbows high and out to the sides during the turnover.",
    "Purpose: The clean-grip snatch can be used for different reasons, such as improving turnover strength, mobility, and maintaining proximity of the bar to the body.",
    "... 1 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.309000",
  "definition": "Olympic weightlifting snatch variation used for mobility, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "weightlifting_skill",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Clean-Grip Snatch",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "placement_tags": [
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Clean-Grip Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "6a76b9208a6813bc44edc7561d684900391ef6cd4facbc01742d83dcef7d97d8",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "summary": "The clean-grip snatch is a fairly obscure exercise, but it can be useful and even fun when implemented appropriately. Exactly as the name implies, the clean-grip snatch is simply a snatch performed with a narrow grip (about the width of the athlete’s clean grip in most cases).",
  "training_qualities": [
    "mobility",
    "pull_mechanics",
    "snatch_skill",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.309000",
  "usage_context": [
    "mobility",
    "mobility_limitation",
    "pain_or_injury_caution",
    "program_design",
    "pull_mechanics",
    "... 5 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 9. Dip Snatch

```json
{
  "id": "ow_ex_dip_snatch",
  "aliases": [
    "high-hang snatch",
    "hip snatch"
  ],
  "category": "power",
  "coaching_cues": [
    "The primary purpose of this exercise is to train the leg drive of the snatch extension for lifters who are overly reliant on hip extension to the detriment of adequate leg.",
    "It’s also helpful to get lifters to remain flat-footed longer through the second pull, to help lifters keep the bar closer to their bodies both in the second and third pulls, and.",
    "The athlete will begin standing in the tall position—standing fully erect with the bar held at arms’ length.",
    "He or she will bend smoothly at the knees only as for a jerk dip, then quickly and aggressively transition in the bottom of the dip and extend the hips and knees together to.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.310000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Dip Snatch",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "60-85%"
    ],
    "rep_ranges": [
      "1-3 reps"
    ],
    "placement_tags": [
      "before_strength_or_accessory_work",
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Dip Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "71ea84de512598dbe61749cfc02238e394c435974be4cbcb5a10af831b76c613",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "but this should generally be only as an introductory stage to the exercise",
    "position (making it a snatch from power position)"
  ],
  "summary": "The terminology gets somewhat confusing, as this exercise is called a high-hang snatch or hip snatch by some coaches. The athlete will begin standing in the tall position—standing fully erect with the bar held at arms’ length.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "snatch_skill"
  ],
  "updated_at": "2026-06-11T08:04:24.310000",
  "usage_context": [
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "recovery",
    "snatch_skill",
    "... 2 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 10. Drop Snatch

```json
{
  "id": "ow_ex_drop_snatch",
  "aliases": [
    "Snatch balance (incorrectly)"
  ],
  "category": "power",
  "coaching_cues": [
    "The drop snatch is a good choice of exercises to develop speed and aggression in the final part of the snatch turnover, to develop precision in bar and foot placement and posture.",
    "Because there is no upward drive on the bar preceding the downward punch of the body, drop snatch weights will be limited relative to the snatch balance and heaving snatch.",
    "If a lifter maintains the hook grip overhead in the snatch, it should also be used in the drop snatch.",
    "The drop snatch is a dynamic snatch receiving position exercise that adds more demand on technique, precision and speed to the overhead squat.",
    "... 2 more"
  ],
  "common_errors": [
    "AKA: Snatch balance (incorrectly)."
  ],
  "contraindications": [
    "achilles_pain",
    "ankle_pain",
    "hamstring_pain",
    "knee_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "... 1 more"
  ],
  "created_at": "2026-06-11T08:04:24.311000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, receiving position.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "achilles_pain",
    "ankle_pain",
    "hamstring_pain",
    "knee_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "jump_landing",
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Drop Snatch",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-100%"
    ],
    "rep_ranges": [
      "1-5 reps"
    ],
    "placement_tags": [
      "after_primary_lift_or_variant",
      "before_strength_or_accessory_work",
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "regressions": [
    "who need a simpler introduction to the exercise"
  ],
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Drop Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "08a0b7fb6c160a55cf966d53f4c7343a21406b6ed9b9d46b0e9df6ae540af296",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "who need a simpler introduction to the exercise"
  ],
  "summary": "The drop snatch is a dynamic snatch receiving position exercise that adds more demand on technique, precision and speed to the overhead squat. It is one of three snatch balance exercises whose names are often confused with each other or used interchangeably.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "receiving_position",
    "snatch_skill",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.311000",
  "usage_context": [
    "beginner_or_learning_lifter",
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "receiving_position",
    "... 5 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 11. Everett Snatch Pull

```json
{
  "id": "ow_ex_everett_snatch_pull",
  "aliases": [
    "Snatch push back + hang snatch pull"
  ],
  "category": "technique",
  "coaching_cues": [
    "The movement will strengthen the back, lats and shoulders to improve the lifter’s ability to stay over the bar and keep it close to the body, and also teach the lifter how to.",
    "Using straps will allow a looser grip on the bar, which will typically allow the athlete to relax the arms and focus more on engaging the lats and shoulders.",
    "The Everett snatch pull is a remedial exercise to strengthen and teach the ability to keep the bar in immediate proximity to the body during the pull of the snatch.",
    "The athlete will stand with a barbell in a snatch-width grip and move down into the mid-hang position.",
    "... 2 more"
  ],
  "common_errors": [
    "Purpose: This is a remedial exercise to help individuals who have problems controlling the path of the bar above the knees due to either strength or a misunderstanding of."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.312000",
  "definition": "Olympic weightlifting snatch variation used for pull mechanics, strength, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "pull",
  "exercise_type": "technique",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Everett Snatch Pull",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "rep_ranges": [
      "3-5 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Everett Snatch Pull"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "d54382156f6e6a83933caeee07cabe4ff0249a5595444a7886363fcc94f9895e",
  "sport_tags": [
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "if the focus is strength in staying over the bar",
    "keeping it close to the body",
    "the exercise can be limited to the movement of the bar out",
    "The lift can be done with",
    "without the snatch pull"
  ],
  "summary": "The Everett snatch pull is a remedial exercise to strengthen and teach the ability to keep the bar in immediate proximity to the body during the pull of the snatch. The athlete will stand with a barbell in a snatch-width grip and move down into the mid-hang position.",
  "training_qualities": [
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.312000",
  "usage_context": [
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength",
    "teaching_progression",
    "... 2 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 12. Floating Snatch Deadlift

```json
{
  "id": "ow_ex_floating_snatch_deadlift",
  "aliases": [
    "hang snatch deadlift",
    "No-touch snatch deadlift"
  ],
  "category": "technique",
  "coaching_cues": [
    "The floating snatch deadlift is a good exercise to develop pulling strength in the snatch, strengthen the proper posture, and emphasize strength in the bottom range of the pull.",
    "Because the primary purpose is to build postural strength and balance, using a more controlled tempo is more effective by allowing the lifter to make adjustments as necessary to.",
    "After standing, the lifter will return to the starting position under control and bring the plates as close to the floor as possible without allowing them to touch, then begin the.",
    "The lifter should pause momentarily in the bottom position between reps.",
    "... 2 more"
  ],
  "common_errors": [
    "In any case, the weight should not exceed what the lifter can do with proper positioning or it is failing to achieve the intended purpose."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.312000",
  "definition": "Olympic weightlifting snatch variation used for pull mechanics, strength, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "deadlift",
  "exercise_type": "technique",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Floating Snatch Deadlift",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-6 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Floating Snatch Deadlift"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "93147406908d7839d522f9becc2ed13ed1973b24b66168d364ec8c874b248422",
  "sport_tags": [
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "a longer pause can be added in the bottom position",
    "snatch segment deadlift"
  ],
  "summary": "The first rep of the floating snatch deadlift will be the same as a snatch deadlift. After standing, the lifter will return to the starting position under control and bring the plates as close to the floor as possible without allowing them to touch, then begin the next rep from this position without setting the bar.",
  "training_qualities": [
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.312000",
  "usage_context": [
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength",
    "technical_correction",
    "... 1 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 13. Floating Snatch Deadlift on Riser

```json
{
  "id": "ow_ex_floating_snatch_deadlift_on_riser",
  "aliases": [
    "hang snatch deadlift on riser",
    "no-touch snatch deadlift on riser",
    "Riser floating snatch deadlift"
  ],
  "category": "technique",
  "coaching_cues": [
    "The floating snatch deadlift on riser is a good exercise to develop pulling strength in the snatch, and emphasize strength in the bottom range of the pull (from the floor to the.",
    "The advantage over the floating snatch deadlift is that standing on the riser allows the bar to move down to the same position it would be during a normal pull from the floor but.",
    "Because the primary purpose is to build postural strength and balance, using a more controlled tempo is more effective by allowing the lifter to make adjustments as necessary to.",
    "If the riser is being used only to allow full depth starting position, the height is unimportant; if the riser is being used to further strengthen the pull from the floor during.",
    "... 2 more"
  ],
  "common_errors": [
    "In any case, the weight should not exceed what the lifter can do with proper positioning or it is failing to achieve the intended purpose."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.313000",
  "definition": "Olympic weightlifting snatch variation used for pull mechanics, strength, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates",
    "riser"
  ],
  "exercise_family": "deadlift",
  "exercise_type": "technique",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Floating Snatch Deadlift on Riser",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-6 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Floating Snatch Deadlift on Riser"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "50d395049cc7ffc0f46123694e0e40ed0e13cb2edf18ff5a42c339ded4bf5f87",
  "sport_tags": [
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "a longer pause can be added in the bottom position",
    "snatch segment deadlift"
  ],
  "summary": "The floating snatch deadlift on riser is identical to the floating snatch deadlift, but the athlete is standing on a riser. The athlete needs to set the starting position properly with the same arm orientation and back angle—the only difference should be that the hips and knees are bent more to accommodate the deficit.",
  "training_qualities": [
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.313000",
  "usage_context": [
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength",
    "technical_correction",
    "... 1 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 14. Floating Snatch Pull

```json
{
  "id": "ow_ex_floating_snatch_pull",
  "aliases": [
    "hang snatch pull",
    "No-touch snatch pull"
  ],
  "category": "technique",
  "coaching_cues": [
    "The floating snatch pull is a good exercise to develop pulling strength in the snatch, and emphasize strength in the bottom range of the pull (from the floor to the knee),.",
    "The floating snatch pull is a variation of the snatch pull in which the bar doesn’t return all the way to the floor between reps.",
    "The first rep of each set will be the same as a snatch pull.",
    "After reaching full extension, the athlete will return to the starting position under control and bring the plates as close to the floor as possible without allowing them to touch.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.315000",
  "definition": "Olympic weightlifting snatch variation used for pull mechanics, strength, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "pull",
  "exercise_type": "technique",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Floating Snatch Pull",
  "note_count_hint": 0,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-5 reps"
    ],
    "placement_tags": [
      "before_strength_or_accessory_work"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Floating Snatch Pull"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "27695e98f2455b4288cffee6cabc2d2651811af1ebaa2abd84084a4c025a17c9",
  "sport_tags": [
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "a longer pause can be added in the bottom position"
  ],
  "summary": "The floating snatch pull is a variation of the snatch pull in which the bar doesn’t return all the way to the floor between reps. The first rep of each set will be the same as a snatch pull.",
  "training_qualities": [
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.315000",
  "usage_context": [
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength",
    "technical_correction",
    "... 1 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 15. Floating Snatch Pull on Riser

```json
{
  "id": "ow_ex_floating_snatch_pull_on_riser",
  "aliases": [
    "hang snatch pull on riser",
    "No-touch snatch pull on riser",
    "riser floating snatch pull",
    "riser hang snatch pull"
  ],
  "category": "technique",
  "coaching_cues": [
    "The floating snatch pull on riser is a good exercise to develop pulling strength in the snatch, and emphasize strength in the bottom range of the pull (from the floor to the.",
    "The advantage over the floating snatch pull is that the lifter can achieve the same starting position as in the snatch while still preventing the weights from resting on the floor.",
    "Riser heights should not exceed what allows the lifter to set a proper starting position.",
    "The floating snatch pull on riser is identical the snatch pull on riser, with the exception that the bar does not return all the way to the floor after the first rep.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.316000",
  "definition": "Olympic weightlifting snatch variation used for pull mechanics, strength, technique.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates",
    "riser"
  ],
  "exercise_family": "pull",
  "exercise_type": "technique",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Floating Snatch Pull on Riser",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-5 reps"
    ],
    "placement_tags": [
      "before_strength_or_accessory_work"
    ],
    "has_programming_guidance": true
  },
  "progressions": [
    "The floating snatch pull on riser can be performed as a snatch high-pull",
    "with",
    "with a longer pause in the bottom position",
    "without straps"
  ],
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "aka",
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Floating Snatch Pull on Riser"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "23f9d222c524064a87d9ffd6cfe2ac03ca7d34ac86e092134bd299abfa91889e",
  "sport_tags": [
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "back arch strength",
    "The floating snatch pull on riser can be performed as a snatch high-pull",
    "with",
    "with a longer pause in the bottom position",
    "without straps"
  ],
  "summary": "The floating snatch pull on riser is identical the snatch pull on riser, with the exception that the bar does not return all the way to the floor after the first rep. After reaching full extension, the athlete will return to a position at which the bottom of the plates are even with the top of the riser—in other.",
  "training_qualities": [
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.316000",
  "usage_context": [
    "mobility_limitation",
    "program_design",
    "pull_mechanics",
    "recovery",
    "strength",
    "... 2 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 16. Halting Snatch Deadlift

```json
{
  "id": "ow_ex_halting_snatch_deadlift",
  "category": "power",
  "coaching_cues": [
    "The halting snatch deadlift is primarily a tool to strengthen an athlete to allow him or her to be able to stay over the bar long enough during the pull of the snatch.",
    "It also helps reinforce position and balance earlier in the pull because it’s typically performed at a more controlled speed.",
    "Finally, it can help improve the lifter’s timing of the initiation of the second pull in the snatch.",
    "Halting snatch deadlifts can be performed without a pause in the top position (i.e.",
    "... 2 more"
  ],
  "common_errors": [
    "In any case, the weight should not exceed what the lifter can do with proper positioning or it is failing to achieve the intended purpose."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.316000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, strength.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "deadlift",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Halting Snatch Deadlift",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-6 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Halting Snatch Deadlift"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "ec777e7f9a17d1de959f8258445256d39bbb6e7aeb3403f91f4195fa663d074c",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "dynamic start. Multiple pause positions may be used",
    "The halting snatch deadlift can be performed standing on a riser",
    "turning the exercise into a halting snatch segment deadlift",
    "with different pause times. The lift can also be done with either a static start",
    "with the pause at different points"
  ],
  "summary": "The halting snatch deadlift is a pull variation that stops short of full extension at the top to strengthen and reinforce the position of the lifter over the bar during the pull of the snatch. The athlete will perform a snatch deadlift up to the designated height (usually mid-thigh), keeping the shoulders over the.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.316000",
  "usage_context": [
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 17. Halting Snatch Deadlift on Riser

```json
{
  "id": "ow_ex_halting_snatch_deadlift_on_riser",
  "category": "power",
  "coaching_cues": [
    "The halting snatch deadlift is primarily a tool to strengthen an athlete to allow him or her to be able to stay over the bar long enough during the pull of the snatch.",
    "It also helps reinforce position and balance earlier in the pull because it’s typically performed at a more controlled speed.",
    "Finally, it can help improve the lifter’s timing of the initiation of the second pull in the snatch.",
    "Riser heights should not exceed what allows the lifter to set a proper starting position.",
    "... 2 more"
  ],
  "common_errors": [
    "In any case, the weight should not exceed what the lifter can do with proper positioning or it is failing to achieve the intended purpose."
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.317000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, strength.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates",
    "riser"
  ],
  "exercise_family": "deadlift",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "hinge",
    "overhead_stability"
  ],
  "name": "Halting Snatch Deadlift on Riser",
  "note_count_hint": 1,
  "paragraph_count": 6,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "110%",
      "80%"
    ],
    "rep_ranges": [
      "2-6 reps"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Halting Snatch Deadlift on Riser"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "96f3ac174f1608b7f44f170bc0f0cf36397ba4b66fc5e9889396312d536c7c9a",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "dynamic start. Multiple pause positions may be done",
    "The halting snatch deadlift can be performed on the floor",
    "turning the exercise into a halting snatch segment deadlift on riser",
    "with different pause times. The lift can also be done with either a static start",
    "with the pause at different points"
  ],
  "summary": "The halting snatch deadlift on riser is identical to the halting snatch deadlift with the exception that the lifter is standing on a riser or platform. The key is ensuring that the starting position is set properly with the same back angle and arm orientation that would be used from the floor—the only difference.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.317000",
  "usage_context": [
    "explosive_power",
    "mobility_limitation",
    "program_design",
    "pull_mechanics",
    "strength",
    "... 1 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 18. Hang Power Snatch

```json
{
  "id": "ow_ex_hang_power_snatch",
  "category": "power",
  "coaching_cues": [
    "It can be an exercise to help teach beginners to snatch that is often easier than lifting from the floor because of the abbreviated movement and the ability to ensure proper.",
    "As a training exercise, the common purpose is to develop better force production in the extension and more aggressiveness in the pull under due to the limited time and distance to.",
    "Another purpose is use as a lighter snatch variation for lighter training days (weights naturally limited relative to the power snatch, and somewhat less work for the legs and.",
    "The hang position needs to be specified when prescribing the hang snatch.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.318000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, mobility, pull mechanics.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Hang Power Snatch",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "65-75%",
      "70-80%",
      "75%"
    ],
    "placement_tags": [
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Hang Power Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "ad970aeb0ea3e3ef2fdc85c7094af47a86e3c56dd9b5d258c3271c03fc6b9443",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "can be done without the hook grip to emphasize grip strength",
    "from a dead stop). The lift can be done with",
    "without a pause in the hang position (i.e. with a countermovement",
    "without straps"
  ],
  "summary": "The hang power snatch is performed identically to the power snatch, but with a starting position at some point above the floor. Hang positions include High-Hang: Upper thigh; Mid-hang: Mid-thigh; Hang: Top of knee caps; Knee: Bar at knee caps; Below knee: Bar below patellar tendon.",
  "training_qualities": [
    "explosive_power",
    "mobility",
    "pull_mechanics",
    "receiving_position",
    "snatch_skill",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.318000",
  "usage_context": [
    "beginner_or_learning_lifter",
    "explosive_power",
    "mobility",
    "mobility_limitation",
    "program_design",
    "... 6 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 19. Hang Snatch

```json
{
  "id": "ow_ex_hang_snatch",
  "category": "power",
  "coaching_cues": [
    "It can be an exercise to help teach beginners to snatch that is often easier than lifting from the floor because of the abbreviated movement and the ability to ensure proper.",
    "As a training exercise, the common purpose is to develop better force production in the extension and more aggressiveness in the pull under due to the limited time and distance to.",
    "The hang position needs to be specified when prescribing the hang snatch.",
    "Generally if no qualifier is present, a hang snatch is done from a starting position with the bar just above the knee.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.319000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, pull mechanics, snatch skill.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Hang Snatch",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-80%",
      "75%"
    ],
    "placement_tags": [
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Hang Snatch"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "a7de205794227d8220175c5c50b4a317b701fc88f53b6f1cacbf386281a50646",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "can be done without the hook grip to emphasize grip strength",
    "from a dead stop). The lift can be done with",
    "without a pause in the hang position (i.e. with a countermovement",
    "without straps"
  ],
  "summary": "The hang snatch is performed identically to the snatch, but with a starting position at some point above the floor. Hang positions include High-Hang: Upper thigh; Mid-hang: Mid-thigh; Hang: Top of knee caps; Knee: Bar at knee caps; Below knee: Bar below patellar tendon.",
  "training_qualities": [
    "explosive_power",
    "pull_mechanics",
    "snatch_skill",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.319000",
  "usage_context": [
    "beginner_or_learning_lifter",
    "explosive_power",
    "program_design",
    "pull_mechanics",
    "recovery",
    "... 3 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

### 20. Heaving Snatch Balance

```json
{
  "id": "ow_ex_heaving_snatch_balance",
  "category": "power",
  "coaching_cues": [
    "The heaving snatch balance develops strength in the receiving position for the snatch with the elements of speed, timing and precision like the snatch balance, but the static foot.",
    "If the athlete maintains the hook grip when overhead in the snatch, the hook grip should be used in the heaving snatch balance.",
    "The execution of the heaving snatch balance was described in detail in the Learning the Snatch chapter of the book.",
    "Notes: If the athlete maintains the hook grip when overhead in the snatch, the hook grip should be used in the heaving snatch balance.",
    "... 2 more"
  ],
  "contraindications": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:24.319000",
  "definition": "Olympic weightlifting snatch variation used for explosive power, mobility, receiving position.",
  "difficulty": "advanced",
  "equipment_required": [
    "barbell",
    "plates"
  ],
  "exercise_family": "snatch",
  "exercise_type": "power",
  "expert_validation_status": "pending",
  "ingestion_method": "epub_heading_labeled_field_extraction_v1",
  "injury_flags": [
    "hamstring_pain",
    "limited_overhead_mobility",
    "low_back_pain",
    "shoulder_pain"
  ],
  "movement_patterns": [
    "olympic_lift",
    "overhead_stability",
    "pull",
    "triple_extension"
  ],
  "name": "Heaving Snatch Balance",
  "note_count_hint": 1,
  "paragraph_count": 5,
  "primary_muscles": [
    "glutes",
    "hamstrings",
    "quadriceps",
    "shoulders",
    "trunk",
    "upper_back"
  ],
  "programming": {
    "intensity_ranges": [
      "70-100%"
    ],
    "rep_ranges": [
      "1-5 reps"
    ],
    "placement_tags": [
      "after_primary_lift_or_variant",
      "before_strength_or_accessory_work",
      "can_be_used_light_for_technique"
    ],
    "has_programming_guidance": true
  },
  "regressions": [
    "but are really considered different exercises—the drop snatch",
    "Two other variations of the snatch balance exist"
  ],
  "secondary_muscles": [
    "calves",
    "grip",
    "serratus_anterior",
    "triceps",
    "trunk"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_fields_available": [
    "notes",
    "programming",
    "purpose",
    "variations"
  ],
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_074_snatch_exercises",
      "section_title": "Snatch Exercises",
      "epub_file": "OEBPS/text00073.html",
      "heading": "Heaving Snatch Balance"
    }
  ],
  "source_section_id": "ow_section_074_snatch_exercises",
  "source_text_hash": "96ee6d9a2cb43fecb63679cd4f9c9f2d99a9c699eafb08feed33b67a085f7211",
  "sport_tags": [
    "court_sports",
    "field_sports",
    "jumping_sports",
    "overhead_athletes",
    "power_development",
    "sprint_transfer",
    "throwing_sports",
    "volleyball"
  ],
  "substitutions": [
    "but are really considered different exercises—the drop snatch",
    "Two other variations of the snatch balance exist"
  ],
  "summary": "The execution of the heaving snatch balance was described in detail in the Learning the Snatch chapter of the book. Notes: If the athlete maintains the hook grip when overhead in the snatch, the hook grip should be used in the heaving snatch balance.",
  "training_qualities": [
    "explosive_power",
    "mobility",
    "receiving_position",
    "snatch_skill",
    "strength",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.319000",
  "usage_context": [
    "beginner_or_learning_lifter",
    "explosive_power",
    "mobility",
    "mobility_limitation",
    "program_design",
    "... 5 more"
  ],
  "variation_count_hint": 1,
  "version": "v1.0.0"
}
```

## `programming_rules` Samples

Showing `12` of `173` documents.

### 1. Progressive Overload & Variation of Stimuli

```json
{
  "id": "ow_rule_program_design_045_001_progressive_overload_and_variation_of_",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "strength"
  ],
  "coaching_cues": [
    "The key is that once the body has adapted to a given type and magnitude of stress, it will maintain that accommodation for as long as it remains regularly exposed to that stress."
  ],
  "content_hash": "8208919cfcc9dd6a821ab1a0b00abc0febb7d6e919b27dfaee4983719679f3d7",
  "created_at": "2026-06-11T08:04:24.915000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "The most basic principle upon which all physical training is predicated is progressive overload .",
    "This describes the notion of progressive overload—the magnitude of a specific training stimulus must continually be increased, or its exact nature modified in certain respects,.",
    "While unfamiliarity of stress can be manifested in a number of ways such as exercise selection and even the speed of execution of a given exercise, the unfamiliarity with which."
  ],
  "paragraph_count": 2,
  "progression_logic": [
    "The most basic principle upon which all physical training is predicated is progressive overload .",
    "In order to stimulate further progress, we need to expose the body to further unfamiliar stress.",
    "This describes the notion of progressive overload—the magnitude of a specific training stimulus must continually be increased, or its exact nature modified in certain respects,.",
    "Without this natural overcompensation, progress would be impossible."
  ],
  "rule_text": "The most basic principle upon which all physical training is predicated is progressive overload . The body adapts to stress in order to survive—this is as basic a biological function as it gets.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Progressive Overload & Variation of Stimuli"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "The most basic principle upon which all physical training is predicated is progressive overload . The body adapts to stress in order to survive—this is as basic a biological function as it gets.",
  "title": "Progressive Overload & Variation of Stimuli",
  "topics": [
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.915000",
  "usage_context": [
    "strength"
  ],
  "version": "v1.0.0"
}
```

### 2. Models of Adaptation

```json
{
  "id": "ow_rule_program_design_045_002_models_of_adaptation",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "fatigue",
    "nutrition",
    "recovery"
  ],
  "coaching_cues": [
    "There are three models of physical adaptation in common use to conceptualize the response of the body to training: The General Adaptation Syndrome, the Fitness-Fatigue Model, and.",
    "None defines the mechanisms in precise detail, but the principles they describe create general guidelines for the systematic manipulation of training load and restoration."
  ],
  "content_hash": "9e9927b3904d68888a1e3d4eee647addc748818c308994dbb8de4001b431b274",
  "created_at": "2026-06-11T08:04:24.915000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "None defines the mechanisms in precise detail, but the principles they describe create general guidelines for the systematic manipulation of training load and restoration."
  ],
  "paragraph_count": 1,
  "progression_logic": [
    "Use Models of Adaptation as a progression or teaching checkpoint."
  ],
  "rule_text": "There are three models of physical adaptation in common use to conceptualize the response of the body to training: The General Adaptation Syndrome, the Fitness-Fatigue Model, and the Supercompensation Model. None defines the mechanisms in precise detail, but.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Models of Adaptation"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "There are three models of physical adaptation in common use to conceptualize the response of the body to training: The General Adaptation Syndrome, the Fitness-Fatigue Model, and the Supercompensation Model. None defines the mechanisms in precise detail, but the principles they describe create general guidelines for.",
  "title": "Models of Adaptation",
  "topics": [
    "fatigue",
    "nutrition",
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:24.915000",
  "usage_context": [
    "fatigue",
    "nutrition",
    "recovery"
  ],
  "version": "v1.0.0"
}
```

### 3. General Adaptation Syndrome

```json
{
  "id": "ow_rule_program_design_045_003_general_adaptation_syndrome",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "fatigue",
    "loading",
    "nutrition",
    "position",
    "power",
    "program_design",
    "recovery",
    "strength"
  ],
  "coaching_cues": [
    "Although originally presented by Hans Selye merely as a general description of the body’s response to stress of any type, the General Adaptation Syndrome has been adopted by.",
    "An exhaustive discussion of the GAS is unnecessary for our purposes here, but a clear picture of its essence can be helpful in guiding programming decisions in a general sense.",
    "Selye defined three stages of stress response: Alarm, Resistance, and Exhaustion."
  ],
  "content_hash": "32014da91e7ab9aaeecb008d880a0722838bb57443ddbcd9958198a6a2dfd13b",
  "contraindications": [
    "high_fatigue"
  ],
  "created_at": "2026-06-11T08:04:24.916000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "That is, an athlete may reach this stage with training volume and intensity no greater than what he or she has been able to manage historically because of factors such as lack of."
  ],
  "paragraph_count": 5,
  "progression_logic": [
    "Selye defined three stages of stress response: Alarm, Resistance, and Exhaustion.",
    "Alarm: The alarm stage is the initial response to a stressor.",
    "During this stage (immediately following a bout of training), performance will diminish to varying degrees depending on the type and dose of stress and the capabilities being.",
    "This stage includes muscle soreness, reduced speed and power, and reduced strength.",
    "... 2 more"
  ],
  "rule_text": "Although originally presented by Hans Selye merely as a general description of the body’s response to stress of any type, the General Adaptation Syndrome has been adopted by coaches and exercise scientists as a vague guide for managing training stimuli and.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "General Adaptation Syndrome"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "Although originally presented by Hans Selye merely as a general description of the body’s response to stress of any type, the General Adaptation Syndrome has been adopted by coaches and exercise scientists as a vague guide for managing training stimuli and recovery. An exhaustive discussion of the GAS is unnecessary.",
  "title": "General Adaptation Syndrome",
  "topics": [
    "fatigue",
    "loading",
    "nutrition",
    "position",
    "power",
    "program_design",
    "recovery",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.916000",
  "usage_context": [
    "fatigue",
    "loading",
    "nutrition",
    "position",
    "power",
    "... 4 more"
  ],
  "version": "v1.0.0"
}
```

### 4. Supercompensation Model

```json
{
  "id": "ow_rule_program_design_045_004_supercompensation_model",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "fatigue",
    "position",
    "recovery"
  ],
  "coaching_cues": [
    "The Supercompensation Model in its most specific form describes the process of adaptation as a reduction in specific substances by training followed by their replenishment during.",
    "While this precise notion of supercompensation has been dismissed as inaccurate because none of the substances have ever been identified (glycogen may be cited as one, but its.",
    "This is, of course, the underlying principle of progressive overload and the margin of adaptation mentioned previously."
  ],
  "content_hash": "f7a1ec7d156165431a11764f6650eb4fa8020b05250c034c4ac4482cea5497f3",
  "created_at": "2026-06-11T08:04:24.917000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "This is, of course, the underlying principle of progressive overload and the margin of adaptation mentioned previously."
  ],
  "paragraph_count": 1,
  "progression_logic": [
    "This is, of course, the underlying principle of progressive overload and the margin of adaptation mentioned previously."
  ],
  "rule_text": "The Supercompensation Model in its most specific form describes the process of adaptation as a reduction in specific substances by training followed by their replenishment during recovery to a level greater than existed previously. While this precise notion.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Supercompensation Model"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "The Supercompensation Model in its most specific form describes the process of adaptation as a reduction in specific substances by training followed by their replenishment during recovery to a level greater than existed previously. While this precise notion of supercompensation has been dismissed as inaccurate because.",
  "title": "Supercompensation Model",
  "topics": [
    "fatigue",
    "position",
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:24.917000",
  "usage_context": [
    "fatigue",
    "position",
    "recovery"
  ],
  "version": "v1.0.0"
}
```

### 5. Fitness-Fatigue Model

```json
{
  "id": "ow_rule_program_design_045_005_fitness_fatigue_model",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "fatigue",
    "nutrition",
    "position",
    "program_design",
    "recovery",
    "strength",
    "training_variables"
  ],
  "coaching_cues": [
    "The Fitness-Fatigue Model avoids the detail that prevented the Supercompensation Model’s acceptance by relying on more flexible terms.",
    "The important idea in this model is that training will simultaneously produce two basic responses: an improvement of physical capacity and fatigue (assuming the training is of an.",
    "The nature of that physical capacity is specific to the training, as is the nature of the accompanying fatigue (e.g."
  ],
  "content_hash": "9d9e9b858b5b9793c62b571d4f798db6678aa7bfbc175a78a1c93508fb6a5017",
  "contraindications": [
    "high_fatigue"
  ],
  "created_at": "2026-06-11T08:04:24.918000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "heavy, low-rep strength training will produce much different fitness and fatigue responses than long distance running).",
    "It’s estimated that for an average training load in a single workout, there is a 3:1 ratio of fitness to fatigue; that is, if the improved fitness lasts 3 days following the."
  ],
  "paragraph_count": 3,
  "progression_logic": [
    "Further, subsequent training must be undertaken before the newly developed capacity diminishes in order to create long-term progress."
  ],
  "rule_text": "The Fitness-Fatigue Model avoids the detail that prevented the Supercompensation Model’s acceptance by relying on more flexible terms. The important idea in this model is that training will simultaneously produce two basic responses: an improvement of.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Fitness-Fatigue Model"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "The Fitness-Fatigue Model avoids the detail that prevented the Supercompensation Model’s acceptance by relying on more flexible terms. The important idea in this model is that training will simultaneously produce two basic responses: an improvement of physical capacity and fatigue (assuming the training is of an.",
  "title": "Fitness-Fatigue Model",
  "topics": [
    "fatigue",
    "nutrition",
    "position",
    "program_design",
    "recovery",
    "strength",
    "training_variables"
  ],
  "updated_at": "2026-06-11T08:04:24.918000",
  "usage_context": [
    "fatigue",
    "nutrition",
    "position",
    "program_design",
    "recovery",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

### 6. Specificity of Adaption

```json
{
  "id": "ow_rule_program_design_045_006_specificity_of_adaption",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "clean",
    "competition",
    "fatigue",
    "jerk",
    "loading",
    "position",
    "program_design",
    "recovery",
    "... 2 more"
  ],
  "coaching_cues": [
    "The snatch and clean & jerk are extremely nuanced combinations of strength, speed, explosiveness, precision, timing, focus and confidence; this combination cannot be replicated or.",
    "That is, weightlifting training must optimally drive physiological adaptation for weightlifting performance, but weightlifters must also limit or eliminate physical activity that."
  ],
  "content_hash": "f005747da3f6abeeae7be696f96fbaefc9de887876aa756abe8c8ac3ba14179d",
  "created_at": "2026-06-11T08:04:24.919000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "Consequently, the competition lifts themselves must represent a significant portion of the total training volume, although how much will vary among lifters, stages of development,."
  ],
  "paragraph_count": 5,
  "progression_logic": [
    "Consequently, the competition lifts themselves must represent a significant portion of the total training volume, although how much will vary among lifters, stages of development,.",
    "The more advanced an athlete desires to be in the sport of weightlifting, the more specialized his or her training must become."
  ],
  "rule_text": "As described by the SAID principle (Specific Adaptation to Imposed Demands), the nature of an athlete’s adaptation to training will be specific to that training. This should to a great extent be quite obvious, and is glaringly so in the most general sense—for.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Specificity of Adaption"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "As described by the SAID principle (Specific Adaptation to Imposed Demands), the nature of an athlete’s adaptation to training will be specific to that training. This should to a great extent be quite obvious, and is glaringly so in the most general sense—for example, few individuals would expect considerable strength.",
  "title": "Specificity of Adaption",
  "topics": [
    "clean",
    "competition",
    "fatigue",
    "jerk",
    "loading",
    "position",
    "program_design",
    "recovery",
    "... 2 more"
  ],
  "updated_at": "2026-06-11T08:04:24.919000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "competition",
    "fatigue",
    "jerk",
    "... 7 more"
  ],
  "version": "v1.0.0"
}
```

### 7. Genetic Potential

```json
{
  "id": "ow_rule_program_design_045_007_genetic_potential",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "fatigue",
    "mobility",
    "recovery",
    "strength"
  ],
  "coaching_cues": [
    "There is no scientific contention regarding the role of genetic potential in an athlete’s success in weightlifting or any other sport, yet opinion on the subject varies.",
    "This variation in opinion arises largely from genetically blessed athletes’ common reluctance to accept the notion that they have natural advantages over other individuals.",
    "While the idea of genetics playing a significant role in one’s athletic success can understandably be unappealing to those athletes, as the implication is that they do not or need."
  ],
  "content_hash": "6cb3191b050fd1456e3c483e81c9a610e698d946e42778d586258949dc7bf5ed",
  "created_at": "2026-06-11T08:04:24.920000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "paragraph_count": 4,
  "progression_logic": [
    "This of course does not mean that athletes not blessed with ideal genetic traits should give up on the pursuit of increasing weightlifting performance; it means simply that such."
  ],
  "rule_text": "There is no scientific contention regarding the role of genetic potential in an athlete’s success in weightlifting or any other sport, yet opinion on the subject varies considerably. This variation in opinion arises largely from genetically blessed athletes’.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Genetic Potential"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "There is no scientific contention regarding the role of genetic potential in an athlete’s success in weightlifting or any other sport, yet opinion on the subject varies considerably. This variation in opinion arises largely from genetically blessed athletes’ common reluctance to accept the notion that they have.",
  "title": "Genetic Potential",
  "topics": [
    "fatigue",
    "mobility",
    "recovery",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.920000",
  "usage_context": [
    "fatigue",
    "mobility",
    "mobility_limitation",
    "recovery",
    "strength"
  ],
  "version": "v1.0.0"
}
```

### 8. Strength & Power Principles

```json
{
  "id": "ow_rule_program_design_045_008_strength_and_power_principles",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "power",
    "recovery",
    "strength"
  ],
  "coaching_cues": [
    "The development of strength and its related qualities is extremely complex from a physiological perspective.",
    "More often than not, training practices are developed in the gym independently of scientific understanding, at least at a significant level, and then evaluated much later by.",
    "Generally speaking, a coach has little or no need to understand the higher level scientific underpinnings of training if he or she has a firm grasp of proven practical elements."
  ],
  "content_hash": "4a8226aa21a603bbf984cf860f2cfa8e08887b2c9d74093b9b05d68875265df9",
  "created_at": "2026-06-11T08:04:24.920000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "paragraph_count": 1,
  "progression_logic": [
    "More often than not, training practices are developed in the gym independently of scientific understanding, at least at a significant level, and then evaluated much later by."
  ],
  "rule_text": "The development of strength and its related qualities is extremely complex from a physiological perspective. More often than not, training practices are developed in the gym independently of scientific understanding, at least at a significant level, and then.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Strength & Power Principles"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "The development of strength and its related qualities is extremely complex from a physiological perspective. More often than not, training practices are developed in the gym independently of scientific understanding, at least at a significant level, and then evaluated much later by researchers to determine the.",
  "title": "Strength & Power Principles",
  "topics": [
    "power",
    "recovery",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.920000",
  "usage_context": [
    "power",
    "recovery",
    "strength"
  ],
  "version": "v1.0.0"
}
```

### 9. Strength Qualities

```json
{
  "id": "ow_rule_program_design_045_009_strength_qualities",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "position",
    "strength"
  ],
  "coaching_cues": [
    "In practical terms, this means that in order to develop the speed strength so critical for weightlifting success, training must address, and even emphasize, this trait."
  ],
  "content_hash": "84b7049cd774cfab4a759dad2404391edfa2263047ec57eb66ff9b9d222c9d03",
  "created_at": "2026-06-11T08:04:24.921000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "the athlete’s ability to manage large training loads.",
    "It takes 0.3-0.4 seconds on average to achieve maximal force (or about 97-98% of it) (Zatsiorksy 1995); explosive movements can occur too quickly for maximal force to be."
  ],
  "paragraph_count": 8,
  "progression_logic": [
    "However, there is no correlation between the ability to produce maximal force and the ability to produce maximal velocity in the same movement with advanced athletes (Zatsiorksy.",
    "Consequently, in general terms, the more advanced the athlete and the greater his or her absolute strength, the more explosive strength must be trained directly rather than."
  ],
  "rule_text": "Strength can be divided into four basic qualities relevant to weightlifting, each of which is functional for given types of movements and activities, and must be trained specifically for maximal development. Absolute Strength This is the ability of the.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Strength Qualities"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "Strength can be divided into four basic qualities relevant to weightlifting, each of which is functional for given types of movements and activities, and must be trained specifically for maximal development. Absolute Strength This is the ability of the muscles to produce maximal force; in other words, to lift as much.",
  "title": "Strength Qualities",
  "topics": [
    "position",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.921000",
  "usage_context": [
    "advanced_or_heavy_training",
    "position",
    "strength"
  ],
  "version": "v1.0.0"
}
```

### 10. Strength Development

```json
{
  "id": "ow_rule_program_design_045_010_strength_development",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "nutrition",
    "power",
    "strength"
  ],
  "coaching_cues": [
    "There are two basic ways to increase strength: morphological and neurological adaptation.",
    "Morphological adaptations are alterations of the actual physical structures of the body.",
    "The primary change for strength is the accumulation of more contractile proteins within the muscle, also known as myofibrillar hypertrophy; in other words, the increase of the."
  ],
  "content_hash": "d4fbc5b307dbcce2cae965867f22b1cc59924f5c7a62ae62d9eae24e224ca7eb",
  "created_at": "2026-06-11T08:04:24.922000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "Also included in morphological changes will be the strengthening of bones and connective tissue in response to increased loading."
  ],
  "paragraph_count": 7,
  "progression_logic": [
    "Also included in morphological changes will be the strengthening of bones and connective tissue in response to increased loading."
  ],
  "rule_text": "There are two basic ways to increase strength: morphological and neurological adaptation. Morphological adaptations are alterations of the actual physical structures of the body.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Strength Development"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "There are two basic ways to increase strength: morphological and neurological adaptation. Morphological adaptations are alterations of the actual physical structures of the body.",
  "title": "Strength Development",
  "topics": [
    "nutrition",
    "power",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.922000",
  "usage_context": [
    "nutrition",
    "power",
    "strength"
  ],
  "version": "v1.0.0"
}
```

### 11. Basic Strength Training Protocols

```json
{
  "id": "ow_rule_program_design_045_011_basic_strength_training_protocols",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "competition",
    "loading",
    "safety",
    "strength"
  ],
  "coaching_cues": [
    "There are different approaches to training strength, each of which has benefits and drawbacks and must be implemented and emphasized appropriately for each athlete based on need,.",
    "In the broadest sense, these are maximal effort, maximal speed with limit weight, repeated effort (maximal or submaximal reps), and dynamic effort (Medvedyev 1986/1989, Zatsiorsky.",
    "Maximal Effort Maximal effort training is the use of the heaviest possible weights with consequently limited repetitions (1-3)."
  ],
  "content_hash": "b21e34da4304d843ca53f5aa5d730a046b0de0399b09bd8c74a0134bef911b74",
  "contraindications": [
    "low_back_pain"
  ],
  "created_at": "2026-06-11T08:04:24.923000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "loading_guidance": [
    "In the broadest sense, these are maximal effort, maximal speed with limit weight, repeated effort (maximal or submaximal reps), and dynamic effort (Medvedyev 1986/1989, Zatsiorsky.",
    "However, high frequency with such high intensity subjects the athlete to overtraining more than other methods, and it produces little if any hypertrophy because of the minimal.",
    "Maximal Speed Limit Weight This is the use of maximal movement speed with heavy weights (80-95%).",
    "Dynamic Effort This approach is the use of maximal speed with necessarily light weights."
  ],
  "paragraph_count": 5,
  "progression_logic": [
    "There are different approaches to training strength, each of which has benefits and drawbacks and must be implemented and emphasized appropriately for each athlete based on need,."
  ],
  "rule_text": "There are different approaches to training strength, each of which has benefits and drawbacks and must be implemented and emphasized appropriately for each athlete based on need, timing, and stage of development. In the broadest sense, these are maximal.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Basic Strength Training Protocols"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "There are different approaches to training strength, each of which has benefits and drawbacks and must be implemented and emphasized appropriately for each athlete based on need, timing, and stage of development. In the broadest sense, these are maximal effort, maximal speed with limit weight, repeated effort (maximal.",
  "title": "Basic Strength Training Protocols",
  "topics": [
    "competition",
    "loading",
    "safety",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.923000",
  "usage_context": [
    "advanced_or_heavy_training",
    "competition",
    "loading",
    "pain_or_injury_caution",
    "program_design",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

### 12. Periodization Structure

```json
{
  "id": "ow_rule_program_design_045_012_periodization_structure",
  "app_usage": "Use for plan construction, loading, frequency, exercise selection, and athlete-level adjustment.",
  "applies_to": [
    "competition",
    "program_design",
    "receiving_position"
  ],
  "coaching_cues": [
    "More advanced program design will typically involve periodization of some type.",
    "There are three primary levels of a training cycle that will be referred to in this book and commonly.",
    "Macrocycle The macrocycle represents what could be considered the entire training program—that is, it’s the complete training cycle that spans the time between subsequent."
  ],
  "content_hash": "f93baff65a209645e9005e562fae1c1ffab1e66627427cba89710ea4a46c2b1f",
  "created_at": "2026-06-11T08:04:24.924000",
  "expert_validation_status": "pending",
  "knowledge_type": "programming_rule",
  "paragraph_count": 4,
  "progression_logic": [
    "More advanced program design will typically involve periodization of some type.",
    "A lifter may train on a single macrocycle beginning after every competition and leading to the next, or in cases of longer periods of time between competitions, may use more than."
  ],
  "rule_text": "More advanced program design will typically involve periodization of some type. There are three primary levels of a training cycle that will be referred to in this book and commonly.",
  "rule_type": "program_design",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_045_introduction_to_program_design",
      "section_title": "Introduction to Program Design",
      "epub_file": "OEBPS/text00044.html",
      "heading": "Periodization Structure"
    }
  ],
  "source_section_id": "ow_section_045_introduction_to_program_design",
  "summary": "More advanced program design will typically involve periodization of some type. There are three primary levels of a training cycle that will be referred to in this book and commonly.",
  "title": "Periodization Structure",
  "topics": [
    "competition",
    "program_design",
    "receiving_position"
  ],
  "updated_at": "2026-06-11T08:04:24.924000",
  "usage_context": [
    "advanced_or_heavy_training",
    "competition",
    "program_design",
    "receiving_position"
  ],
  "version": "v1.0.0"
}
```

## `technical_models` Samples

Showing `10` of `137` documents.

### 1. Phases of the Lifts

```json
{
  "id": "ow_tech_all_lifts_009_001_phases_of_the_lifts",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "More specifically, the snatch and clean will be considered primarily in terms of three different phases in order to aid analysis—the first pull, second pull, and third pull.",
    "In addition to these phases, there will be the preparatory position, starting position, receiving position, and recovery.",
    "The three-pull method is both simple and logical and consequently effective in communication among athletes and coaches.",
    "Preparatory Position: This is the position the lifter assumes once at the barbell, prior to actively setting the starting position.",
    "... 2 more"
  ],
  "content_hash": "a86ab5db0060ce90af04453440aed95a4f59c7ccb491e975dbb6171eb2c1b50a",
  "created_at": "2026-06-11T08:04:24.517000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 10,
  "phase": "phases_of_the_lifts",
  "position_rules": [
    "In the first phase, the lifter elevates the barbell with the lower body; in the second phase, the lifter moves his or her body down underneath the elevated barbell with the upper.",
    "In addition to these phases, there will be the preparatory position, starting position, receiving position, and recovery.",
    "Preparatory Position: This is the position the lifter assumes once at the barbell, prior to actively setting the starting position.",
    "This is a relaxed or semi-relaxed position the lifter habitually holds at least momentarily while focusing and finalizing any pre-lift mental rituals.",
    "Often this is gripping the bar lightly and either leaning over it or sitting in a squat position behind it.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Phases of the Lifts"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "The snatch, clean and jerk can all be considered as being comprised of two basic phases. In the first phase, the lifter elevates the barbell with the lower body; in the second phase, the lifter moves his or her body down underneath the elevated barbell with the upper body (Figure 1.1).",
  "title": "Phases of the Lifts",
  "topics": [
    "clean",
    "fatigue",
    "first_pull",
    "jerk",
    "overhead",
    "position",
    "pull",
    "receiving_position",
    "... 6 more"
  ],
  "updated_at": "2026-06-11T08:04:24.517000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "fatigue",
    "first_pull",
    "jerk",
    "... 11 more"
  ],
  "version": "v1.0.0"
}
```

### 2. Period 1 (The Pull)

```json
{
  "id": "ow_tech_all_lifts_009_002_period_1_the_pull",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "This phase can be compared to the starting position.",
    "Phase 2: The second phase consists of the pull between the separation of the bar from the floor and the beginning of the double knee bend.",
    "This phase is equivalent to the first pull."
  ],
  "content_hash": "4782ba7791a31f53f0514b62dfa252c7f56161cd9e2c770123689487aab21755",
  "created_at": "2026-06-11T08:04:24.517000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 2,
  "phase": "period_1_the_pull",
  "position_rules": [
    "Phase 1: This phase is simply the lifter’s first application of force to the barbell.",
    "It begins with that application of force and ends when the bar separates from the floor.",
    "This phase can be compared to the starting position.",
    "Phase 2: The second phase consists of the pull between the separation of the bar from the floor and the beginning of the double knee bend."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 1 (The Pull)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 1: This phase is simply the lifter’s first application of force to the barbell. It begins with that application of force and ends when the bar separates from the floor.",
  "title": "Period 1 (The Pull)",
  "topics": [
    "bar_path",
    "first_pull",
    "position",
    "pull",
    "starting_position"
  ],
  "updated_at": "2026-06-11T08:04:24.517000",
  "usage_context": [
    "bar_path",
    "first_pull",
    "position",
    "pull",
    "starting_position"
  ],
  "version": "v1.0.0"
}
```

### 3. Period 2 (The Explosion)

```json
{
  "id": "ow_tech_all_lifts_009_003_period_2_the_explosion",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "This phase is the first part of the second pull.",
    "This phase is the final part of the second pull."
  ],
  "content_hash": "f9fa3879647d86d4e3f53fba92f6dbf65c6f014d812648aae39877670e0cad91",
  "created_at": "2026-06-11T08:04:24.517000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 2,
  "phase": "period_2_the_explosion",
  "position_rules": [
    "Phase 4: This phase is the final upward extension of the body and acceleration of the bar—it begins from the point of greatest knee flexion in the double knee bend and ends with."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 2 (The Explosion)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 3: Phase three is essentially the double knee bend or scoop—it is the movement of the knees forward and their slight rebending as the torso moves into a vertical orientation. This phase is the first part of the second pull.",
  "title": "Period 2 (The Explosion)",
  "topics": [
    "first_pull",
    "pull",
    "second_pull"
  ],
  "updated_at": "2026-06-11T08:04:24.517000",
  "usage_context": [
    "first_pull",
    "pull",
    "second_pull"
  ],
  "version": "v1.0.0"
}
```

### 4. Period 3 (The Squat Under)

```json
{
  "id": "ow_tech_all_lifts_009_004_period_3_the_squat_under",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "It begins at the lifter’s complete extension in phase 4 and ends when the barbell reaches its maximum height (the barbell continues to move upward under the momentum created in.",
    "Phase 6: The final phase lasts from the point of the barbell’s maximum height to the point at which the lifter receives the barbell in the squat position.",
    "Preparatory Position: This is the position the lifter assumes prior to initiating the jerk.",
    "It may or may not be the same position used in the jerk itself.",
    "... 2 more"
  ],
  "content_hash": "14f73073359193fbe6d9669d48c03fc2600a1df4b1ca241835ef32ff4528a985",
  "created_at": "2026-06-11T08:04:24.518000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 11,
  "phase": "period_3_the_squat_under",
  "position_rules": [
    "Phase 5: Phase 5 consists of the lifter’s initial movement under the bar.",
    "It begins at the lifter’s complete extension in phase 4 and ends when the barbell reaches its maximum height (the barbell continues to move upward under the momentum created in.",
    "Phase 6: The final phase lasts from the point of the barbell’s maximum height to the point at which the lifter receives the barbell in the squat position.",
    "Preparatory Position: This is the position the lifter assumes prior to initiating the jerk.",
    "It may or may not be the same position used in the jerk itself.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 3 (The Squat Under)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 5: Phase 5 consists of the lifter’s initial movement under the bar. It begins at the lifter’s complete extension in phase 4 and ends when the barbell reaches its maximum height (the barbell continues to move upward under the momentum created in the explosion and in reaction to the lifter pulling against it to.",
  "title": "Period 3 (The Squat Under)",
  "topics": [
    "clean",
    "fatigue",
    "first_pull",
    "jerk",
    "overhead",
    "position",
    "pull",
    "receiving_position",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.518000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "fatigue",
    "first_pull",
    "jerk",
    "... 12 more"
  ],
  "version": "v1.0.0"
}
```

### 5. Period 1 (The Half Squat)

```json
{
  "id": "ow_tech_all_lifts_009_005_period_1_the_half_squat",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "Phase 1: This is the dip of the jerk: the bending of the knees from the initial standing position into the bottom of the dip position."
  ],
  "content_hash": "e217b7e986060459ce2b080a91fb500c8e4596cd93a3b9507d7e96a71d3314d5",
  "created_at": "2026-06-11T08:04:24.518000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 1,
  "phase": "period_1_the_half_squat",
  "position_rules": [
    "Phase 1: This is the dip of the jerk: the bending of the knees from the initial standing position into the bottom of the dip position."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 1 (The Half Squat)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 1: This is the dip of the jerk: the bending of the knees from the initial standing position into the bottom of the dip position.",
  "title": "Period 1 (The Half Squat)",
  "topics": [
    "first_pull",
    "jerk",
    "position",
    "recovery",
    "squat"
  ],
  "updated_at": "2026-06-11T08:04:24.518000",
  "usage_context": [
    "first_pull",
    "jerk",
    "position",
    "recovery",
    "squat"
  ],
  "version": "v1.0.0"
}
```

### 6. Period 2 (The Thrust)

```json
{
  "id": "ow_tech_all_lifts_009_006_period_2_the_thrust",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "Phase 3: This is the drive of the legs out of the dip to accelerate and elevate the barbell."
  ],
  "content_hash": "4cf6914ac36cbfd0d6be18c44583c5fa332ac72f04cabd7714b76d10ce2374e2",
  "created_at": "2026-06-11T08:04:24.519000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 2,
  "phase": "period_2_the_thrust",
  "position_rules": [
    "Phase 2: This is the braking of the dip to stop the downward movement of the lifter and barbell.",
    "Phase 3: This is the drive of the legs out of the dip to accelerate and elevate the barbell."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 2 (The Thrust)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 2: This is the braking of the dip to stop the downward movement of the lifter and barbell. Phase 3: This is the drive of the legs out of the dip to accelerate and elevate the barbell.",
  "title": "Period 2 (The Thrust)",
  "updated_at": "2026-06-11T08:04:24.519000",
  "version": "v1.0.0"
}
```

### 7. Period 3 (The Squat Under)

```json
{
  "id": "ow_tech_all_lifts_009_007_period_3_the_squat_under",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "Phase 4: This is the movement of the legs into the receiving position, typically the split, and the movement of the rest of the body into the proper position under the bar.",
    "Phase 5: The final phase is the securing of the barbell in the overhead position and establishing stability."
  ],
  "content_hash": "ce3acb1d252d5bf66624b143823481aaff92163269cb80d19142e390a306391f",
  "created_at": "2026-06-11T08:04:24.519000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 2,
  "phase": "period_3_the_squat_under",
  "position_rules": [
    "Phase 4: This is the movement of the legs into the receiving position, typically the split, and the movement of the rest of the body into the proper position under the bar.",
    "Phase 5: The final phase is the securing of the barbell in the overhead position and establishing stability."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Period 3 (The Squat Under)"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "Phase 4: This is the movement of the legs into the receiving position, typically the split, and the movement of the rest of the body into the proper position under the bar. Phase 5: The final phase is the securing of the barbell in the overhead position and establishing stability.",
  "title": "Period 3 (The Squat Under)",
  "topics": [
    "fatigue",
    "overhead",
    "position",
    "receiving_position",
    "squat"
  ],
  "updated_at": "2026-06-11T08:04:24.519000",
  "usage_context": [
    "fatigue",
    "overhead",
    "position",
    "receiving_position",
    "recovery",
    "... 1 more"
  ],
  "version": "v1.0.0"
}
```

### 8. Laws of Motion in Weightlifting

```json
{
  "id": "ow_tech_all_lifts_009_008_laws_of_motion_in_weightlifting",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "In other words, an object will maintain its present motion or lack thereof unless and until acted upon by an external force.",
    "When a lifter drives against the ground to lift the barbell, the ground delivers the same magnitude of force in return.",
    "This law will also come into play as the lifter applies force against the barbell’s mass in an elevated position to relocate his or her body underneath it.",
    "When the athlete reaches the peak of productive body extension and can consequently no longer drive against the platform to further elevate and accelerate the bar, the barbell.",
    "... 2 more"
  ],
  "content_hash": "b82af068b0aa8d4a4f0e7ff5c21d320d56ddddbb03c0d8190e15721ecd56a3ee",
  "corrections": [
    "If performing the lift correctly, the lifter will not cease applying force to the barbell at this point, however.",
    "During the first and second pulls, the lifter must maintain contact with the platform until maximal productive body extension is achieved in order to impart maximal acceleration."
  ],
  "created_at": "2026-06-11T08:04:24.521000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 11,
  "phase": "laws_of_motion_in_weightlifting",
  "position_rules": [
    "A barbell will remain on the platform until a lifter moves it; likewise, a moving barbell will continue traveling upward due to the lifter’s force as long as that applied force.",
    "Additionally, the barbell will travel in whatever direction the lifter applies force to it (this becomes important when considering the contact of the barbell and the hips or.",
    "To increase the acceleration of a given barbell, more force must be applied, and the same amount of force will produce less acceleration as the weight on the barbell increases.",
    "When a lifter drives against the ground to lift the barbell, the ground delivers the same magnitude of force in return.",
    "The earth’s far greater mass than the lifter/barbell system results in all noticeable movement being undertaken by the lifter and the bar when driving against the ground.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Laws of Motion in Weightlifting"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "The principles dictating the results of the lifter’s movements are described by the constant interaction of Newton’s Laws of Motion: Law of Inertia: Every body perseveres in its state of being at rest or of moving uniformly straight forward, except insofar as it is compelled to change its state by force impressed. In.",
  "title": "Laws of Motion in Weightlifting",
  "topics": [
    "clean",
    "fatigue",
    "jerk",
    "position",
    "power",
    "press",
    "pull",
    "safety",
    "... 4 more"
  ],
  "updated_at": "2026-06-11T08:04:24.521000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "fatigue",
    "jerk",
    "position",
    "... 11 more"
  ],
  "version": "v1.0.0"
}
```

### 9. Center of Mass, Center of Pressure & Line of Gravity

```json
{
  "id": "ow_tech_all_lifts_009_009_center_of_mass_center_of_pressure_and_li",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "One of the most fundamental elements involved in weightlifting is the constant balancing of the lifter-barbell system over the base of support as the positions of the body and.",
    "In other words, it’s the center of the object in terms of balance—supporting the object directly under the center of mass will keep the object balanced over the base of support.",
    "This point will move continuously as the athlete performs the lift, but must always remain essentially balanced over the feet for a successful lift.",
    "Line of Gravity The athlete’s line of gravity is an imaginary vertical line that passes through the athlete’s center of mass and runs through the point at the base (feet) over.",
    "... 2 more"
  ],
  "content_hash": "b43eb42c1278df542303e2bf394b4b0c9339cf8f742b87b84510a84374c72728",
  "corrections": [
    "With the additional weight of the barbell, which is also not fixed in a constant relative position to the lifter, shifts in balance can very quickly be magnified to degrees beyond."
  ],
  "created_at": "2026-06-11T08:04:24.524000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 11,
  "phase": "center_of_mass_center_of_pressure_and_line_of_gravity",
  "position_rules": [
    "One of the most fundamental elements involved in weightlifting is the constant balancing of the lifter-barbell system over the base of support as the positions of the body and.",
    "In other words, it’s the center of the object in terms of balance—supporting the object directly under the center of mass will keep the object balanced over the base of support.",
    "In weightlifting, the concern primarily is with the combined center of mass of the athlete and the barbell.",
    "This point will move continuously as the athlete performs the lift, but must always remain essentially balanced over the feet for a successful lift.",
    "Line of Gravity The athlete’s line of gravity is an imaginary vertical line that passes through the athlete’s center of mass and runs through the point at the base (feet) over.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Center of Mass, Center of Pressure & Line of Gravity"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "One of the most fundamental elements involved in weightlifting is the constant balancing of the lifter-barbell system over the base of support as the positions of the body and weight change both dramatically and quickly relative to the ground and each other. Center of Mass The center of mass is the point around which.",
  "title": "Center of Mass, Center of Pressure & Line of Gravity",
  "topics": [
    "balance",
    "clean",
    "first_pull",
    "jerk",
    "jump_training",
    "position",
    "press",
    "pull",
    "... 3 more"
  ],
  "updated_at": "2026-06-11T08:04:24.524000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "clean",
    "first_pull",
    "jerk",
    "... 8 more"
  ],
  "version": "v1.0.0"
}
```

### 10. Strength Versus Technique

```json
{
  "id": "ow_tech_all_lifts_009_010_strength_versus_technique",
  "app_usage": "Use as technique context, exercise selection constraints, and coaching focus for Olympic-lift-derived training.",
  "coaching_cues": [
    "There is ongoing discussion and confusion regarding the roles of strength and technique in the sport of weightlifting, although largely carried on outside the competitive.",
    "At the extreme ends of the discussion are the ideas that the sport is wholly dependent on technique, or that that technique is essentially irrelevant with enough strength.",
    "The fact is that neither strength nor technique will adequately compensate for a significant lack of the other."
  ],
  "content_hash": "063fa31c3e0d80624b32d3682f49eaf7fdc59d7d051da0bc14141d241303247e",
  "contraindications": [
    "ankle_pain",
    "knee_pain"
  ],
  "created_at": "2026-06-11T08:04:24.525000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "technical_model",
  "lift": "all_lifts",
  "paragraph_count": 3,
  "phase": "strength_versus_technique",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html",
      "heading": "Strength Versus Technique"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "summary": "There is ongoing discussion and confusion regarding the roles of strength and technique in the sport of weightlifting, although largely carried on outside the competitive weightlifting community, presumably attributable to the sport’s relative obscurity and consequent lack of understanding. At the extreme ends of the.",
  "title": "Strength Versus Technique",
  "topics": [
    "clean",
    "first_pull",
    "jerk",
    "jump_training",
    "press",
    "program_design",
    "recovery",
    "snatch",
    "... 2 more"
  ],
  "updated_at": "2026-06-11T08:04:24.525000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "first_pull",
    "jerk",
    "jump_training",
    "... 6 more"
  ],
  "version": "v1.0.0"
}
```

## `technical_errors` Samples

Showing `8` of `36` documents.

### 1. ow_error_snatch_clean_040_leading_with_the_hips

```json
{
  "id": "ow_error_snatch_clean_040_leading_with_the_hips",
  "causes": [
    {
      "name": "Weak Legs Relative to Hips",
      "topics": [
        "first_pull",
        "position",
        "pull",
        "second_pull",
        "starting_position",
        "strength"
      ],
      "points": [
        {
          "text": "If an athlete’s hips are significantly stronger than his/her legs, the natural tendency, to an increasing degree with increasing weights, will be to extend the knees to a larger angle without moving the shoulders and bar to the same extent.",
          "content_hash": "5b4ba01c84d898e7ed35461b46b80b3efbbd99e292cb67b4b20761d734f400ca",
          "signal_tags": [
            "first_pull",
            "position",
            "second_pull",
            "starting_position",
            "strength"
          ]
        },
        {
          "text": "Exercises to help correct this problem include anything that strengthens knee extension, and in particular, knee extension with the body in the posture we want the lifter to maintain during the first pull.",
          "content_hash": "270201b1ca0bc828170a4a4f9217b46a3d443721e724b393a2320fd44329a49e",
          "signal_tags": [
            "first_pull",
            "position",
            "pull",
            "second_pull",
            "strength"
          ]
        }
      ],
      "summary": "If an athlete’s hips are significantly stronger than his/her legs, the natural tendency, to an increasing degree with increasing weights, will be to extend the knees to a larger angle without moving the shoulders and bar to the same extent. Exercises to help correct this problem include anything that strengthens knee.",
      "content_hash": "dfcf29623da2670540fb1417dc6b576722ab2a46ad723d20dcd973b6957682cd"
    },
    {
      "name": "Rushing off the Floor",
      "topics": [
        "balance",
        "clean",
        "error_correction",
        "first_pull",
        "position",
        "pull",
        "snatch",
        "strength"
      ],
      "points": [
        {
          "text": "If an imbalance of strength is not the cause, the error is often the result of the lifter rushing the initial lift from the floor without being tight and controlled enough to maintain the correct posture. The body’s natural tendency will.",
          "content_hash": "1ccdc2cec0d63a1b4f68a9c7488715656e2c25a11f60ce0e5ace0f6423796df3",
          "signal_tags": [
            "balance",
            "error_correction",
            "first_pull",
            "position",
            "strength"
          ]
        },
        {
          "text": "Exercises to help correct this problem include anything that will force the athlete to control the posture off the floor correctly and help him or her feel the proper position and balance. These are largely the same as the exercises that.",
          "content_hash": "1284805de104960b2240e06abc7f8bca894c7b6f1b275490ae0e922bec91ff26",
          "signal_tags": [
            "balance",
            "clean",
            "first_pull",
            "position",
            "pull",
            "snatch",
            "strength"
          ]
        },
        {
          "text": "Cues that can be helpful, especially if used in combination with the above corrective exercises, include:",
          "content_hash": "e75adf01287e51418383cf33dd9effad354658dccd65a5d98433e027ad9b2b49",
          "signal_tags": [
            "first_pull"
          ]
        }
      ],
      "summary": "If an imbalance of strength is not the cause, the error is often the result of the lifter rushing the initial lift from the floor without being tight and controlled enough to maintain the correct posture. The body’s natural tendency will.",
      "content_hash": "98748b88eac3215a204045b307d39c8b52c13c1fb57360f64a4fdf35e6fc1282"
    }
  ],
  "coaching_cues": [
    "Leading with the hips refers to the hips rising faster than the shoulders in the first pull to a degree larger than what is acceptable.",
    "That is, for most lifters we will expect to see a slight shift in the back angle during the pull from the floor, but too much creates a number of possible problems and can be.",
    "In order to prevent this natural shifting, the athlete’s knee extension strength will need to be increased to allow him to extend the knees from the desired starting position with.",
    "Exercises to help correct this problem include anything that strengthens knee extension, and in particular, knee extension with the body in the posture we want the lifter to.",
    "... 2 more"
  ],
  "common_errors": [
    "Leading with the hips refers to the hips rising faster than the shoulders in the first pull to a degree larger than what is acceptable. That is, for most lifters we will expect to."
  ],
  "content_hash": "0f6bdc3a72cae27627331436e5f1a33684f373a36ee996621fb75581db6d8c1a",
  "contraindications": [
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "In order to prevent this natural shifting, the athlete’s knee extension strength will need to be increased to allow him to extend the knees from the desired starting position with.",
    "Exercises to help correct this problem include anything that strengthens knee extension, and in particular, knee extension with the body in the posture we want the lifter to.",
    "Rushing off the Floor If an imbalance of strength is not the cause, the error is often the result of the lifter rushing the initial lift from the floor without being tight and.",
    "Exercises to help correct this problem include anything that will force the athlete to control the posture off the floor correctly and help him or her feel the proper position and.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.752000",
  "description_points": [
    {
      "text": "Leading with the hips refers to the hips rising faster than the shoulders in the first pull to a degree larger than what is acceptable. That is, for most lifters we will expect to see a slight shift in the back angle during the pull from.",
      "content_hash": "deaaffb484f1338114e0c932e4f88c70208db0f271ece0a54eb4127413254a46",
      "signal_tags": [
        "balance",
        "first_pull",
        "pull",
        "strength"
      ]
    }
  ],
  "error_name": "Leading with the Hips",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 6,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Leading with the Hips"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "Leading with the hips refers to the hips rising faster than the shoulders in the first pull to a degree larger than what is acceptable. That is, for most lifters we will expect to see a slight shift in the back angle during the pull from the floor, but too much creates a number of possible problems and can be.",
  "topics": [
    "balance",
    "clean",
    "error_correction",
    "first_pull",
    "position",
    "pull",
    "second_pull",
    "snatch",
    "... 2 more"
  ],
  "updated_at": "2026-06-11T08:04:24.752000",
  "usage_context": [
    "balance",
    "clean",
    "error_correction",
    "first_pull",
    "position",
    "... 6 more"
  ],
  "version": "v1.0.0"
}
```

### 2. ow_error_snatch_clean_040_jumping_forward

```json
{
  "id": "ow_error_snatch_clean_040_jumping_forward",
  "causes": [
    {
      "name": "Non-Specific Corrections",
      "topics": [
        "balance",
        "bar_path",
        "clean",
        "error_correction",
        "first_pull",
        "jump_training",
        "position",
        "program_design",
        "... 5 more"
      ],
      "points": [
        {
          "text": "The first non-specific correction is the use of barriers to jumping forward by placing an object of some type in front of the lifter. While this can be very effective, it’s critical to only use objects that don’t create the potential for.",
          "content_hash": "450c88bc158dfdd9a673578a04b89964753b7ad659fb1f1e3b6bd5f4103d90d0",
          "signal_tags": [
            "jump_training"
          ]
        },
        {
          "text": "The first choice is a scrap of thin rubber flooring or mat. Half-inch or thinner is ideal—this creates an adequate barrier but is low enough that the athlete will not have much of a problem finishing or bailing out of the lift if one or.",
          "content_hash": "f475f9eefec2e860458de911af04b782083cde6cdae0bccc3e87b39e815245b1",
          "signal_tags": [
            "first_pull",
            "jump_training"
          ]
        },
        {
          "text": "Another choice, which is better if part of the problem may be the bar swinging forward away from the lifter, is a vertical length of PVC pipe or wooden dowel placed in front of one or both ends of the bar (outside the plates). A brave.",
          "content_hash": "23f5378d5f8f78ff1cd778a3fe31967380f60260c1025af1d7f585cc79d82c2d",
          "signal_tags": [
            "position",
            "recovery"
          ]
        },
        {
          "text": "Virtual barriers can also be used, such as placing a length of tape or chalk line on the platform in front of the lifter’s toes and providing the instruction to not jump over it. Despite the absence of a physical barrier and the attendant.",
          "content_hash": "87aa102eb471575e49ba8543a779fefd8ff0c94b755489cfc117c84d67ec3d9f",
          "signal_tags": [
            "jump_training"
          ]
        },
        {
          "text": "We can also attempt over-correction through cueing alone or along with a physical or virtual barrier. That is, rather than instructing the athlete to not jump forward, we can instruct him or her to actually jump backward a small amount.",
          "content_hash": "f6bf6987db8253c6b21768cef04b49292cab282887fe5b62aad9d354227e7267",
          "signal_tags": [
            "balance",
            "jump_training"
          ]
        },
        {
          "text": "The potential problem with all of the previous strategies is that they may not correct the cause of the error but simply create some kind of compensatory effort that itself is a problem or leads to new problems. For example, the lifter may.",
          "content_hash": "34316845e34ad53f0e61105a1a8b03ceca5e826b9ba215cf8733fe193de0f086",
          "signal_tags": [
            "balance",
            "bar_path",
            "error_correction",
            "position",
            "pull",
            "receiving_position",
            "snatch"
          ]
        },
        {
          "text": "Finally, performing the snatch or clean without lifting the feet from the platform is a non-specific approach to forcing the athlete to maintain balance over the same base throughout the lift. This can be successful for some lifters, but.",
          "content_hash": "d602de09d6a2935dea68b33c9597a8090f82fe32d2f7ae741514233f9142ecb3",
          "signal_tags": [
            "balance",
            "clean",
            "position",
            "program_design",
            "pull",
            "receiving_position",
            "recovery",
            "snatch",
            "... 1 more"
          ]
        }
      ],
      "summary": "The first non-specific correction is the use of barriers to jumping forward by placing an object of some type in front of the lifter. While this can be very effective, it’s critical to only use objects that don’t create the potential for.",
      "content_hash": "b3339693aedcdbf1dbc6a6d61090cdb41867cb812f63e85c0dd47e9b34ea4b3e"
    },
    {
      "name": "Failure to Shift Weight Back in First Pull",
      "topics": [
        "balance",
        "bar_path",
        "first_pull",
        "position",
        "pull"
      ],
      "points": [
        {
          "text": "A part of the action of the first pull is to shift the center of mass of the barbell-lifter system slightly farther back over the foot into the balance we want maintained for the remainder of the lift. Needless to say, if this does not.",
          "content_hash": "72993e4c33948bc59a0575559bdbf9b9167c6e88821aef3748a84c210c2c94ca",
          "signal_tags": [
            "balance",
            "bar_path",
            "first_pull",
            "position",
            "pull"
          ]
        },
        {
          "text": "Exercises that will help the athlete perform this backward weight shift and maintain both the proper posture and the bar’s proximity to the body in the first pull include anything that allows controlled performance of and focus on this.",
          "content_hash": "a9239b5689268072f3b44ee9118cef8846739eaab997ec4174c904a79573e6a0",
          "signal_tags": [
            "bar_path",
            "first_pull",
            "position",
            "pull"
          ]
        },
        {
          "text": "Cues that may be helpful to encourage the athlete to perform the movement properly include:",
          "content_hash": "4391b2846858f669333e394eae2d6357971ac38918b84e0b999cf996927ba616",
          "signal_tags": [
            "first_pull",
            "pull"
          ]
        }
      ],
      "summary": "A part of the action of the first pull is to shift the center of mass of the barbell-lifter system slightly farther back over the foot into the balance we want maintained for the remainder of the lift. Needless to say, if this does not.",
      "content_hash": "3c641d68f2d87995de6533b037553ef124e7c6a5af4534f0ecf39127b501e7fd"
    },
    {
      "name": "Improper Starting Position",
      "topics": [
        "balance",
        "clean",
        "first_pull",
        "position",
        "pull",
        "recovery",
        "snatch",
        "starting_position"
      ],
      "points": [
        {
          "text": "While some degree of adjustment can be accomplished early in the lift, it’s limited, and an improper starting position can easily produce a forward imbalance during the snatch or clean. Starting with the weight too far forward over the.",
          "content_hash": "a8c7ec6748842e070d42baafcc54730a097fc13798f0321d6da59f2091fefc70",
          "signal_tags": [
            "balance",
            "clean",
            "position",
            "snatch",
            "starting_position"
          ]
        },
        {
          "text": "Exercises that can help the lifter improve the starting position are the same as for the previous cause, as we are in essence trying to accomplish the same basic task. Of course, the focus will be primarily on the starting position. It.",
          "content_hash": "1cca6e4185865278d37f94663658238c2fbe8ba1f09e1ef2eb951926ddc0cf06",
          "signal_tags": [
            "clean",
            "position",
            "snatch",
            "starting_position"
          ]
        },
        {
          "text": "&#9;",
          "content_hash": "e42eddefbe25cf527beaab5d180b8d223d55a28fafc411f377c4dc555d2d23a4",
          "signal_tags": [
            "position",
            "starting_position"
          ]
        },
        {
          "text": "Cues in this case will be directed at helping the athlete establish the starting position itself correctly rather than with the movement of the first pull. These will of course vary depending on the nature of each athlete’s deviation from.",
          "content_hash": "04c8d4576fa015d9b9d7cfef79fe11adcda2277b39c544dc7d9582c59a8c8c58",
          "signal_tags": [
            "first_pull",
            "position",
            "pull",
            "recovery",
            "starting_position"
          ]
        }
      ],
      "summary": "While some degree of adjustment can be accomplished early in the lift, it’s limited, and an improper starting position can easily produce a forward imbalance during the snatch or clean. Starting with the weight too far forward over the.",
      "content_hash": "4a2c9180a6ba429c193bebec99e65dd619509068577605ba2f3cab2561dd1278"
    },
    {
      "name": "Bar Moving Straight up Past Knees",
      "topics": [
        "bar_path",
        "clean",
        "first_pull",
        "position",
        "power",
        "pull",
        "second_pull",
        "snatch"
      ],
      "points": [
        {
          "text": "A common mistake made by new lifters is lifting the bar straight up from the knees or lower thighs, continuing to lean forward over the bar and allow it to remain away from the body. The combined effort to keep the bar as close to the body.",
          "content_hash": "c99849101c1866467ab8248bdd3692a64125736b2190cd63d9fa0ce7420edbd9",
          "signal_tags": [
            "clean",
            "first_pull",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Exercises to help correct this problem should focus primarily on the movement between the knees and the power position or extension, the maintenance of maximal proximity of the bar to the body, and possibly the movement of the knees under.",
          "content_hash": "e0824567ee04e687a8e135aa8735c7101d66cc84d9361312ebc82c2b228d5e0b",
          "signal_tags": [
            "bar_path",
            "first_pull",
            "position",
            "power",
            "second_pull"
          ]
        },
        {
          "text": "Note that it is actually possible to move the barbell too far back between the knee and hip, which will result in a snatch or clean in the lifter’s weight shifting excessively forward or backward as the second pull is performed. Cues or.",
          "content_hash": "9bf5a01e2977eefe511cae109ac7e4ea5d66b0a1f443a7694b02679f683efe24",
          "signal_tags": [
            "clean",
            "first_pull",
            "pull",
            "second_pull",
            "snatch"
          ]
        },
        {
          "text": "Helpful cues will depend on what exactly the problem is, and include:",
          "content_hash": "29e442d4fbab0199cccee3569b6d174d777871780ce8e82d0a27d6aab1d75544",
          "signal_tags": [
            "first_pull"
          ]
        }
      ],
      "summary": "A common mistake made by new lifters is lifting the bar straight up from the knees or lower thighs, continuing to lean forward over the bar and allow it to remain away from the body. The combined effort to keep the bar as close to the body.",
      "content_hash": "d5cdf37e87fc9f6b629ebb2077f59f1b4554aa4e66276123c8a0b2565915da83"
    },
    {
      "name": "Bumping or Swinging Bar Forward in Second Pull",
      "topics": [
        "error_correction",
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "Any forward movement of the bar in the second pull has the potential to pull the lifter forward to a degree dependent on the bar’s forward inertia and its weight relative to the lifter’s. See more about and corrections for this error in.",
          "content_hash": "3927403a14a99b324a703c16d851c32b52be25aef2b9572d1a182bcf4487d6c1",
          "signal_tags": [
            "error_correction",
            "pull",
            "second_pull"
          ]
        }
      ],
      "summary": "Any forward movement of the bar in the second pull has the potential to pull the lifter forward to a degree dependent on the bar’s forward inertia and its weight relative to the lifter’s. See more about and corrections for this error in.",
      "content_hash": "663d076f5b4e4d88a47d52606b2c0162ef783864d42867058f8cc623a4ad815a"
    },
    {
      "name": "Pushing Bar Too Far Back Toward Hips",
      "topics": [
        "balance",
        "position",
        "pull",
        "recovery",
        "second_pull"
      ],
      "points": [
        {
          "text": "Occasionally lifters will be so focused on bringing the bar back toward the hips that they move it too far back relative to the feet; that is, it moves behind approximately the middle of the foot. This shifts the line of gravity too far.",
          "content_hash": "e811fc2cb72c4f7f47fd55f5077eef9378506a8e95457a9ffabae994af11a174",
          "signal_tags": [
            "balance",
            "position",
            "pull",
            "recovery",
            "second_pull"
          ]
        },
        {
          "text": "Cues that may help the athlete maintain the proper barbell and body relative positions and balance over the feet include:",
          "content_hash": "5cef5019a187f4bb936950d0b195a0a2546e06a57142146ebcdc6c6dfe45b7cd",
          "signal_tags": [
            "balance",
            "position"
          ]
        }
      ],
      "summary": "Occasionally lifters will be so focused on bringing the bar back toward the hips that they move it too far back relative to the feet; that is, it moves behind approximately the middle of the foot. This shifts the line of gravity too far.",
      "content_hash": "ab606adba21a7ca7a256c12712e6bd3037dd4f52c5b8f977334d82b21bfaf656"
    },
    {
      "name": "Bar Swinging Forward in Third Pull",
      "topics": [
        "error_correction",
        "pull",
        "third_pull"
      ],
      "points": [
        {
          "text": "See more about this error and corrections in its own section below.",
          "content_hash": "4b34a1b638e0b5f6e9481eca0cefbd21f8018969708163b30797a23e74adfe5c",
          "signal_tags": [
            "error_correction",
            "pull",
            "third_pull"
          ]
        }
      ],
      "summary": "See more about this error and corrections in its own section below.",
      "content_hash": "4b34a1b638e0b5f6e9481eca0cefbd21f8018969708163b30797a23e74adfe5c"
    }
  ],
  "coaching_cues": [
    "Jumping forward in the snatch or clean is always a symptom of a forward imbalance of the barbell-lifter system at some point during the lift.",
    "However, this imbalance can have a number of sources, and correction will vary depending on the cause.",
    "Half-inch or thinner is ideal—this creates an adequate barrier but is low enough that the athlete will not have much of a problem finishing or bailing out of the lift if one or.",
    "This also allows the coach to view the lift from whatever position he or she prefers rather than be stuck right next to the athlete.",
    "... 2 more"
  ],
  "common_errors": [
    "Jumping forward in the snatch or clean is always a symptom of a forward imbalance of the barbell-lifter system at some point during the lift. However, this imbalance can have a.",
    "This is an error, however, that will sometimes respond to non-specific corrections. If the cause of the problem is proving difficult to diagnose or is not obvious, using this."
  ],
  "content_hash": "3cd25c08f08700ba989b2c1f8fb37da1619f8d7400892a3f744e25d132e04722",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "However, this imbalance can have a number of sources, and correction will vary depending on the cause.",
    "Often this error proves extremely difficult and frustrating to correct, but investing the time and effort is well worth it.",
    "This is an error, however, that will sometimes respond to non-specific corrections.",
    "First discussed are non-specific corrections that can be effective, followed by specific possible causes and suggested corrections for each.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.753000",
  "description_points": [
    {
      "text": "Jumping forward in the snatch or clean is always a symptom of a forward imbalance of the barbell-lifter system at some point during the lift. However, this imbalance can have a number of sources, and correction will vary depending on the.",
      "content_hash": "e0301bfeb5bb2250c92444e683080bad8d16999add6286a58240cbdb410795db",
      "signal_tags": [
        "balance",
        "clean",
        "error_correction",
        "jump_training",
        "snatch"
      ]
    },
    {
      "text": "This is an error, however, that will sometimes respond to non-specific corrections. If the cause of the problem is proving difficult to diagnose or is not obvious, using this approach can be a smart way to begin resolving the problem.",
      "content_hash": "99222c5b4da7b69d8f32780e2c74c7a6b92632d6d7ba28aa6b7ad8af63736e8f",
      "signal_tags": [
        "error_correction",
        "jump_training"
      ]
    }
  ],
  "error_name": "Jumping Forward",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 24,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Jumping Forward"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "Jumping forward in the snatch or clean is always a symptom of a forward imbalance of the barbell-lifter system at some point during the lift. However, this imbalance can have a number of sources, and correction will vary depending on the cause.",
  "topics": [
    "balance",
    "bar_path",
    "clean",
    "error_correction",
    "first_pull",
    "jump_training",
    "position",
    "power",
    "... 9 more"
  ],
  "updated_at": "2026-06-11T08:04:24.753000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "bar_path",
    "beginner_or_learning_lifter",
    "clean",
    "... 16 more"
  ],
  "version": "v1.0.0"
}
```

### 3. ow_error_snatch_clean_040_bumping_or_swinging_bar_forward_in_second_pull

```json
{
  "id": "ow_error_snatch_clean_040_bumping_or_swinging_bar_forward_in_second_pull",
  "causes": [
    {
      "name": "Excessive or Improper Hip Extension",
      "topics": [
        "clean",
        "error_correction",
        "pull",
        "recovery",
        "safety",
        "second_pull",
        "snatch",
        "third_pull"
      ],
      "points": [
        {
          "text": "How and how much the hips are extended in the second pull will affect where the bar is directed to a large extent. While we want explosive and essentially maximal effort hip extension, it must be properly executed to be effective. We can.",
          "content_hash": "4561ef5904cf94388d35c5a7784bc2da552dee7e4d8a947188fdaf2a53bc0b07",
          "signal_tags": [
            "clean",
            "error_correction",
            "pull",
            "recovery",
            "safety",
            "second_pull",
            "snatch",
            "third_pull"
          ]
        },
        {
          "text": "Excessive hip extension in the finish of the second pull can be improved with a few different exercises:",
          "content_hash": "dd21f7cf8a9e9b457235bb87f3de4a3cdf1df94d8690928327ca8285117ced11",
          "signal_tags": [
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Helpful cues for preventing excessive hip extension include:",
          "content_hash": "008b4b8d74dbdb61056134f7f9ed5372f0251209d0396ad6de5480dba370e516",
          "signal_tags": [
            "second_pull"
          ]
        }
      ],
      "summary": "How and how much the hips are extended in the second pull will affect where the bar is directed to a large extent. While we want explosive and essentially maximal effort hip extension, it must be properly executed to be effective.",
      "content_hash": "9fe4a9ea69bb469e25dd4b18f1ea22fe781ace76e860083b0d7395e65677356b"
    },
    {
      "name": "Inadequate or Incomplete Leg Drive",
      "topics": [
        "error_correction",
        "first_pull",
        "power",
        "pull",
        "safety",
        "second_pull"
      ],
      "points": [
        {
          "text": "As mentioned above, one cause of the bar being pushed forward with the hips in the second pull is weak or incomplete leg drive against the floor—that is, the leg drive in the second pull is either not aggressive enough, or the lifter stops.",
          "content_hash": "7d6136849932db2daeadf9b9f511f199ecce1fbd9a2e214523c26263cbea6f82",
          "signal_tags": [
            "first_pull",
            "pull",
            "safety",
            "second_pull"
          ]
        },
        {
          "text": "Conveniently enough, the exercises that will help correct this are largely the same as for the previous error, with a couple additions (the final three are to improve the power of the leg drive generally):",
          "content_hash": "d4a3ecb5e39a758a6b5b5281ff7d7ea661a7fceda73f8886365633b331f9f6e9",
          "signal_tags": [
            "error_correction",
            "power"
          ]
        },
        {
          "text": "Likewise, the cues are similar to the previous problem of excessive hip extension:",
          "content_hash": "87f54522e1ff84624b79d43e30d39754954d7f86319e097fce5232fc55882b44",
          "signal_tags": [
            "second_pull"
          ]
        }
      ],
      "summary": "As mentioned above, one cause of the bar being pushed forward with the hips in the second pull is weak or incomplete leg drive against the floor—that is, the leg drive in the second pull is either not aggressive enough, or the lifter stops. Conveniently enough, the exercises that will help correct this are largely the.",
      "content_hash": "b6adeca5297237b6be8f36e4b13de54ee7611a6fcec2d0f1c3b89d95771ea804"
    },
    {
      "name": "Excessive Distance Between Bar & Body Before Contact",
      "topics": [
        "bar_path",
        "clean",
        "first_pull",
        "position",
        "power",
        "second_pull",
        "snatch"
      ],
      "points": [
        {
          "text": "Failing to maintain proximity of the bar to the body prior to its contact with the hips in the snatch or upper thighs in the clean will make the bar being pushed forward more likely. The solution is not to reduce the power of the hip.",
          "content_hash": "c65dc458641d7e519310f3a9609dd0339f633d58c6a39247bd349c634db2c2d3",
          "signal_tags": [
            "bar_path",
            "clean",
            "position",
            "power",
            "second_pull",
            "snatch"
          ]
        },
        {
          "text": "If we face two cars bumper to bumper and have the drivers floor the gas, we may get a lot of burned rubber, but no collision to speak of, despite the cars creating maximal force against each other. However, if we back the cars up away from.",
          "content_hash": "5c454e91f30f86bf928c8fa507e1680648b4996560f9b9e5229c34d419170e52",
          "signal_tags": [
            "bar_path",
            "first_pull",
            "position",
            "second_pull"
          ]
        },
        {
          "text": "Exercises to practice this proximity of the bar to the body include:",
          "content_hash": "2f018876b6bb770e855bc505bbe80726f8b781d66aa60f32e902445f7b4a60a3",
          "signal_tags": [
            "bar_path",
            "position"
          ]
        },
        {
          "text": "Cues to help prevent excessive distance between the bar and body include:",
          "content_hash": "98a7093200050caf2573280bc3a01bae7a03b1b88579bdc0be73f3c5fc0e749f",
          "signal_tags": [
            "position"
          ]
        }
      ],
      "summary": "Failing to maintain proximity of the bar to the body prior to its contact with the hips in the snatch or upper thighs in the clean will make the bar being pushed forward more likely. The solution is not to reduce the power of the hip.",
      "content_hash": "363c0bf25b039717e0bc2c1d26f9f2f967086f04197052003254fd6ba136093d"
    },
    {
      "name": "Stiff Arms",
      "topics": [
        "pull",
        "second_pull",
        "third_pull"
      ],
      "points": [
        {
          "text": "Stiff arms (i.e. locked elbows) during the second pull can cause the bar to swing forward as the lifter finishes the extension—with upward momentum on the bar and the arms locked, the bar has nowhere to go, and it has to pivot around the.",
          "content_hash": "57aaeaa9e96214a10489f93a4d5593dab0280888b298c460ca0bc02832d0d2d5",
          "signal_tags": [
            "pull",
            "second_pull",
            "third_pull"
          ]
        },
        {
          "text": "Exercises to help the lifter train passive extension of the arms in the second pull and transitioning to active arms in the third pull include:",
          "content_hash": "11fdeada3a41d543f2cdd63629219fe44f634e94c47d62a9b71493a6666b18e0",
          "signal_tags": [
            "pull",
            "second_pull",
            "third_pull"
          ]
        },
        {
          "text": "Cues that may be helpful include:",
          "content_hash": "9800eba1b72d260f6af8de9552a1fe2aefb1ba1ee39b14f1ed3bcdbb0aebd6cd"
        }
      ],
      "summary": "locked elbows) during the second pull can cause the bar to swing forward as the lifter finishes the extension—with upward momentum on the bar and the arms locked, the bar has nowhere to go, and it has to pivot around the. Exercises to help the lifter train passive extension of the arms in the second pull and.",
      "content_hash": "af133988f9dfcbb193e52070e2d692e620e42aafaf18e411991e0297e06567f9"
    }
  ],
  "coaching_cues": [
    "A forward-traveling barbell will cause forward movement of the lifter to a magnitude commensurate to the relative weights of the bar and lifter and the inertia of the bar in that.",
    "There can be a few different reasons the barbell moves forward away from the body at the finish of the second pull and each will have its own corrections.",
    "Excessive or Improper Hip Extension How and how much the hips are extended in the second pull will affect where the bar is directed to a large extent.",
    "Extending the hips through this line creates too much forward force on the bar that disrupts its upward movement and reduces its upward speed and elevation; additionally, it will.",
    "... 2 more"
  ],
  "common_errors": [
    "A forward-traveling barbell will cause forward movement of the lifter to a magnitude commensurate to the relative weights of the bar and lifter and the inertia of the bar in that."
  ],
  "content_hash": "0088d6c0418bb1124f54f6cbb11fa5182d53ada91d63b9a2379049b81b9fd2ed",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "There can be a few different reasons the barbell moves forward away from the body at the finish of the second pull and each will have its own corrections.",
    "Extending the hips through this line creates too much forward force on the bar that disrupts its upward movement and reduces its upward speed and elevation; additionally, it will.",
    "Part of preventing excessive hip extension is ensuring complete and adequately aggressive vertical leg drive; this is addressed specifically as its own error below.",
    "Excessive hip extension in the finish of the second pull can be improved with a few different exercises: Helpful cues for preventing excessive hip extension include: Inadequate or.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.757000",
  "description_points": [
    {
      "text": "A forward-traveling barbell will cause forward movement of the lifter to a magnitude commensurate to the relative weights of the bar and lifter and the inertia of the bar in that direction; the heavier the barbell and the faster it’s.",
      "content_hash": "dd0d7cabd4471eec083435b793f2f0d27606c8d82fdcf81f140b92543b9f621c",
      "signal_tags": [
        "pull",
        "second_pull"
      ]
    }
  ],
  "error_name": "Bumping or Swinging Bar Forward in Second Pull",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 14,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Bumping or Swinging Bar Forward in Second Pull"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "A forward-traveling barbell will cause forward movement of the lifter to a magnitude commensurate to the relative weights of the bar and lifter and the inertia of the bar in that direction; the heavier the barbell and the faster it’s moving forward, the more it will pull the lifter forward (although, the heavier the.",
  "topics": [
    "bar_path",
    "clean",
    "error_correction",
    "first_pull",
    "position",
    "power",
    "pull",
    "recovery",
    "... 4 more"
  ],
  "updated_at": "2026-06-11T08:04:24.757000",
  "usage_context": [
    "advanced_or_heavy_training",
    "bar_path",
    "clean",
    "error_correction",
    "first_pull",
    "... 9 more"
  ],
  "version": "v1.0.0"
}
```

### 4. ow_error_snatch_clean_040_swinging_bar_forward_in_third_pull

```json
{
  "id": "ow_error_snatch_clean_040_swinging_bar_forward_in_third_pull",
  "coaching_cues": [
    "The bar may also swing forward during the third pull.",
    "This is often a continuation of forward swinging in the second pull, but it warrants its own section as it can be a problem specific to the third pull as well.",
    "Just like stiff arms will cause the bar to swing forward in the second pull, they will force the bar to swing forward in the third pull.",
    "Likewise, failing to perform the mechanics of the third pull properly will cause the bar to either move or stay too far forward and either prevent a successful turnover or force.",
    "... 1 more"
  ],
  "common_errors": [
    "The bar may also swing forward during the third pull. This is often a continuation of forward swinging in the second pull, but it warrants its own section as it can be a problem.",
    "There are two basic causes of this problem: stiff arms and improper mechanics. They are combined here because the corrective strategies are the same.",
    "Just like stiff arms will cause the bar to swing forward in the second pull, they will force the bar to swing forward in the third pull. If the elbows don’t bend during the.",
    "Likewise, failing to perform the mechanics of the third pull properly will cause the bar to either move or stay too far forward and either prevent a successful turnover or force.",
    "... 1 more"
  ],
  "content_hash": "d0de4183c9ef76a2b518f7f4da5cd2a697ea2bf59bb96a2669b211bcc032b05b",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "Corrections for the latter will also help the former.",
    "They are combined here because the corrective strategies are the same.",
    "Likewise, failing to perform the mechanics of the third pull properly will cause the bar to either move or stay too far forward and either prevent a successful turnover or force.",
    "Exercises to correct the third pull and ensure maximal proximity include: Cues to help correct the problem and remind the lifter of the desired upper body movement include:"
  ],
  "created_at": "2026-06-11T08:04:24.759000",
  "description_points": [
    {
      "text": "The bar may also swing forward during the third pull. This is often a continuation of forward swinging in the second pull, but it warrants its own section as it can be a problem specific to the third pull as well. Corrections for the.",
      "content_hash": "a2e24113c77c72406be8597c915c06034c21a7aff4c5148f4524e380eb544d1c",
      "signal_tags": [
        "pull",
        "second_pull",
        "third_pull"
      ]
    },
    {
      "text": "There are two basic causes of this problem: stiff arms and improper mechanics. They are combined here because the corrective strategies are the same.",
      "content_hash": "a39e25ddabfbaeda7aa1c885526c1cdcd4ed6e11e8de8a3d3428c0ad5a1bfead",
      "signal_tags": [
        "pull",
        "third_pull"
      ]
    },
    {
      "text": "Just like stiff arms will cause the bar to swing forward in the second pull, they will force the bar to swing forward in the third pull. If the elbows don’t bend during the lifter’s movement under the bar, the only possibility is the bar.",
      "content_hash": "651f8870c5e0e04fbb032f32d1762cef4a009eceada49818873b1e37f0f1b69b",
      "signal_tags": [
        "pull",
        "second_pull",
        "third_pull"
      ]
    },
    {
      "text": "Likewise, failing to perform the mechanics of the third pull properly will cause the bar to either move or stay too far forward and either prevent a successful turnover or force the lifter to jump or lean forward to attempt to save the.",
      "content_hash": "7f8ea173f3d37646255fbe5dd788dd5655cc21a76da5ba0c531a13e3f3d55e9e",
      "signal_tags": [
        "jump_training",
        "pull",
        "third_pull"
      ]
    },
    {
      "text": "Exercises to correct the third pull and ensure maximal proximity include:",
      "content_hash": "d50fde190e297b7aea5b0d4768f0f0981c3038fe1a1d1046f50b5b8542335e7c",
      "signal_tags": [
        "bar_path",
        "pull",
        "third_pull"
      ]
    },
    {
      "text": "Cues to help correct the problem and remind the lifter of the desired upper body movement include:",
      "content_hash": "2e4e367035ae3a79c95eeed54fa42f71860234eb692a241d352847fc229a4b14",
      "signal_tags": [
        "pull",
        "third_pull"
      ]
    }
  ],
  "error_name": "Swinging Bar Forward in Third Pull",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 6,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Swinging Bar Forward in Third Pull"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "The bar may also swing forward during the third pull. This is often a continuation of forward swinging in the second pull, but it warrants its own section as it can be a problem specific to the third pull as well.",
  "topics": [
    "bar_path",
    "jump_training",
    "pull",
    "second_pull",
    "third_pull"
  ],
  "updated_at": "2026-06-11T08:04:24.759000",
  "usage_context": [
    "advanced_or_heavy_training",
    "bar_path",
    "jump_training",
    "pull",
    "second_pull",
    "... 2 more"
  ],
  "version": "v1.0.0"
}
```

### 5. ow_error_snatch_clean_040_jumping_backward

```json
{
  "id": "ow_error_snatch_clean_040_jumping_backward",
  "causes": [
    {
      "name": "Weight Too Far Back in Pull",
      "topics": [
        "balance",
        "jump_training",
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "Any backward jump is caused by the lifter’s balance being too far back over the feet at some point—in this case, it’s too far back during the first and second pull or both. As was discussed earlier in the book, ideally we want the line of.",
          "content_hash": "e09e8ccc4832e6b91e188a72bbc2884c36fc073326559236b1cf5fc3eb223b18",
          "signal_tags": [
            "balance",
            "jump_training",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Cues to help encourage the lifter to maintain the proper balance during the lift include:",
          "content_hash": "e9eff508d7409dcac63bd1a721cd6a87305e44df0d56ca34db462056e26ee64a",
          "signal_tags": [
            "balance",
            "pull"
          ]
        }
      ],
      "summary": "Any backward jump is caused by the lifter’s balance being too far back over the feet at some point—in this case, it’s too far back during the first and second pull or both. As was discussed earlier in the book, ideally we want the line of.",
      "content_hash": "5d832a751cd5711e7e563dd4f4dc521f70583e0466b72633e35058e478935e3a"
    },
    {
      "name": "Excessive Hip Extension",
      "topics": [
        "deadlift",
        "position",
        "second_pull",
        "snatch"
      ],
      "points": [
        {
          "text": "Unlike the excessive hip extension discussed previously that causes the bar to swing forward, in this case, the excessive extension is occurring without the hips moving too far forward—in other words, the legs are still vertical or nearly.",
          "content_hash": "ee464766e0f4262b03170c60d509e3baa58886728a41c71def8d7ab9e06c9c3b",
          "signal_tags": [
            "second_pull"
          ]
        },
        {
          "text": "Exercises to help the lifter feel the proper degree of extension will essentially simulate that finish position, and so must be done properly. For example, if the lifter is leaning back excessively in a snatch deadlift to fix excessive hip.",
          "content_hash": "66d8341c9596de3b3303035d7e757c842f59bd446f9040f9b29806d92eedeb2f",
          "signal_tags": [
            "deadlift",
            "position",
            "second_pull",
            "snatch"
          ]
        },
        {
          "text": "Helpful cues may include:",
          "content_hash": "678c315977acbaa93ce5f3cb9a559f3e75e9e8d30b6d3886ccafec82b656dff2",
          "signal_tags": [
            "second_pull"
          ]
        }
      ],
      "summary": "Unlike the excessive hip extension discussed previously that causes the bar to swing forward, in this case, the excessive extension is occurring without the hips moving too far forward—in other words, the legs are still vertical or nearly. Exercises to help the lifter feel the proper degree of extension will.",
      "content_hash": "308e71f3d41498b2945ceda19b5730b9ee3220b0a1c1fe9a498a25e379d588f7"
    }
  ],
  "coaching_cues": [
    "However, it can become excessive and create problems in the receiving position, and can be unintentional and unwanted, in which case, it should be corrected.",
    "That is, the lifter’s feet land farther back from their starting point, but the bar comes with the lifter and the receiving position is correct and balanced.",
    "Weight Too Far Back in Pull Any backward jump is caused by the lifter’s balance being too far back over the feet at some point—in this case, it’s too far back during the first and.",
    "Exercises to help the athlete feel the proper balance over the feet and correct it in the pull include: Cues to help encourage the lifter to maintain the proper balance during the.",
    "... 2 more"
  ],
  "common_errors": [
    "Jumping backward during a snatch or clean is not necessarily problematic and therefore may not qualify as a technical error. However, it can become excessive and create problems.",
    "Additionally, a distinction needs to be made between jumping backward and moving only the feet backward. Jumping backward here refers to the entire barbell-lifter system moving."
  ],
  "content_hash": "8f1f1a32cd21de51210be7d163e61416f0a37f4e05572e0ea6ab1eec89f2584a",
  "contraindications": [
    "ankle_pain",
    "high_fatigue",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "However, it can become excessive and create problems in the receiving position, and can be unintentional and unwanted, in which case, it should be corrected.",
    "That is, the lifter’s feet land farther back from their starting point, but the bar comes with the lifter and the receiving position is correct and balanced.",
    "Exercises to help the athlete feel the proper balance over the feet and correct it in the pull include: Cues to help encourage the lifter to maintain the proper balance during the.",
    "Exercises to help the lifter feel the proper degree of extension will essentially simulate that finish position, and so must be done properly.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.760000",
  "description_points": [
    {
      "text": "Jumping backward during a snatch or clean is not necessarily problematic and therefore may not qualify as a technical error. However, it can become excessive and create problems in the receiving position, and can be unintentional and.",
      "content_hash": "9f97be94069e766076214537679333476329ceb3f2dc3117661ef8c6940a7526",
      "signal_tags": [
        "clean",
        "error_correction",
        "jump_training",
        "position",
        "receiving_position",
        "snatch"
      ]
    },
    {
      "text": "Additionally, a distinction needs to be made between jumping backward and moving only the feet backward. Jumping backward here refers to the entire barbell-lifter system moving backward together. That is, the lifter’s feet land farther.",
      "content_hash": "16d79f273fe31cfff6b398c1416bcbc418b3ce44502c0a5179f7b6b68ece6584",
      "signal_tags": [
        "balance",
        "fatigue",
        "jump_training",
        "position",
        "receiving_position"
      ]
    }
  ],
  "error_name": "Jumping Backward",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 7,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Jumping Backward"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "Jumping backward during a snatch or clean is not necessarily problematic and therefore may not qualify as a technical error. However, it can become excessive and create problems in the receiving position, and can be unintentional and unwanted, in which case, it should be corrected.",
  "topics": [
    "balance",
    "clean",
    "deadlift",
    "error_correction",
    "fatigue",
    "jump_training",
    "position",
    "pull",
    "... 3 more"
  ],
  "updated_at": "2026-06-11T08:04:24.760000",
  "usage_context": [
    "balance",
    "clean",
    "deadlift",
    "error_correction",
    "fatigue",
    "... 8 more"
  ],
  "version": "v1.0.0"
}
```

### 6. ow_error_snatch_clean_040_feet_sweeping_backward

```json
{
  "id": "ow_error_snatch_clean_040_feet_sweeping_backward",
  "causes": [
    {
      "name": "Incomplete Leg Drive",
      "topics": [
        "balance",
        "clean",
        "press",
        "pull",
        "second_pull",
        "snatch"
      ],
      "points": [
        {
          "text": "In this case, at least part of the problem is that the lifter has not continued driving with the legs against the ground long enough in the pull—the drive has stopped prior to the hips finishing their extension, which removes the pressure.",
          "content_hash": "88ddfbfcf4ac5b321bb4658ea16491012faed19d5004477f97f5d4806397044b",
          "signal_tags": [
            "balance",
            "press",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Cues to help encourage adequate and complete leg drive during the snatch or clean include:",
          "content_hash": "ae08ae936a74413525d388a5bbcdcbc6849d60c930338f2357750421e4a37420",
          "signal_tags": [
            "clean",
            "snatch"
          ]
        }
      ],
      "summary": "In this case, at least part of the problem is that the lifter has not continued driving with the legs against the ground long enough in the pull—the drive has stopped prior to the hips finishing their extension, which removes the pressure. Cues to help encourage adequate and complete leg drive during the snatch or.",
      "content_hash": "af97adf8dca170e57a3db230e26f9f8d2887c2748383a4a0c4327c9ee4781a60"
    },
    {
      "name": "Improper Foot Movement in Third Pull",
      "topics": [
        "balance",
        "clean",
        "first_pull",
        "jump_training",
        "pull",
        "snatch",
        "squat",
        "third_pull"
      ],
      "points": [
        {
          "text": "Backward sweeping of the feet can also occur without any significant imbalance in the pull due simply to poor mechanics in the relocation of the feet itself. This is usually due to a lift of the feet rather than of the knees—that is, the.",
          "content_hash": "6462e4e04b3d9db28e73fca8c5e0428a01e295f7fc2dd2f3eb3ed60f80615142",
          "signal_tags": [
            "balance",
            "clean",
            "first_pull",
            "jump_training",
            "pull",
            "snatch",
            "squat",
            "third_pull"
          ]
        },
        {
          "text": "Exercises to help practice moving the feet correctly include the following. All need to be performed with a focus on completely lifting the feet from the floor and replacing them flat and in the correct location.",
          "content_hash": "7bd7d0fdee91ca45f979d2292fb4a80cab129d2ece0fc20e84a9562fc2ec516e",
          "signal_tags": [
            "first_pull",
            "pull",
            "third_pull"
          ]
        },
        {
          "text": "Cues to help with proper foot movement include:",
          "content_hash": "08322e61d6ecc4bbc7ac576dc8823d5181f0e1c1e27e93d7411c537599159bf8",
          "signal_tags": [
            "pull",
            "third_pull"
          ]
        }
      ],
      "summary": "Backward sweeping of the feet can also occur without any significant imbalance in the pull due simply to poor mechanics in the relocation of the feet itself. This is usually due to a lift of the feet rather than of the knees—that is, the.",
      "content_hash": "b3bc3080f95276c44a253b3af1ceb7d2a20464f1726b5cee72cf99c4305d2e86"
    }
  ],
  "coaching_cues": [
    "The effect of this is essentially the same as the bar moving forward—in the receiving position, the center of mass is in front of the base and cannot be supported easily or at all.",
    "Generally the reason for this error is the same in a basic sense as for actually jumping backward—the lifter’s weight is too far back during the pull—but the timing may differ and.",
    "Additionally, there is usually a weak, unaggressive or improper elevation of the feet in the third pull that causes them to drag rather than separate cleanly from the platform.",
    "Incomplete Leg Drive In this case, at least part of the problem is that the lifter has not continued driving with the legs against the ground long enough in the pull—the drive has.",
    "... 2 more"
  ],
  "common_errors": [
    "Unlike in the backward jump discussed in the previous section, this error involves only the lifter’s feet moving backward during the lift while the rest of the body and the bar.",
    "Generally the reason for this error is the same in a basic sense as for actually jumping backward—the lifter’s weight is too far back during the pull—but the timing may differ and."
  ],
  "content_hash": "70f3ca7e2d40f5b485af43fbfff8d2aee1f4daa3af4cd39bf00eeff47fe3ee8c",
  "contraindications": [
    "ankle_pain",
    "high_fatigue",
    "hip_pain",
    "knee_pain",
    "low_back_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "Exercises to help with this include: Cues to help encourage adequate and complete leg drive during the snatch or clean include: Improper Foot Movement in Third Pull Backward.",
    "A rubber mat can also be placed on the platform behind the lifter’s heels during snatches or cleans or any of the related drills being used to correct the problem in the same way.",
    "Exercises to help practice moving the feet correctly include the following.",
    "All need to be performed with a focus on completely lifting the feet from the floor and replacing them flat and in the correct location."
  ],
  "created_at": "2026-06-11T08:04:24.761000",
  "description_points": [
    {
      "text": "Unlike in the backward jump discussed in the previous section, this error involves only the lifter’s feet moving backward during the lift while the rest of the body and the bar remain over the same original area. The effect of this is.",
      "content_hash": "6dcb5a44570cbbccce58e66ee368a26d1f87f4aab22937ea10910da285917a5e",
      "signal_tags": [
        "balance",
        "error_correction",
        "fatigue",
        "jump_training",
        "position",
        "receiving_position"
      ]
    },
    {
      "text": "Generally the reason for this error is the same in a basic sense as for actually jumping backward—the lifter’s weight is too far back during the pull—but the timing may differ and likely the feet will move from the floor sooner in this.",
      "content_hash": "53a930dd8fdb8ae0d367013a2882e67dfe915b7ea28d86d273b580d44012b1e6",
      "signal_tags": [
        "clean",
        "error_correction",
        "first_pull",
        "jump_training",
        "pull",
        "safety",
        "third_pull"
      ]
    }
  ],
  "error_name": "Feet Sweeping Backward",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 7,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Feet Sweeping Backward"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "Unlike in the backward jump discussed in the previous section, this error involves only the lifter’s feet moving backward during the lift while the rest of the body and the bar remain over the same original area. The effect of this is essentially the same as the bar moving forward—in the receiving position, the center.",
  "topics": [
    "balance",
    "clean",
    "error_correction",
    "fatigue",
    "first_pull",
    "jump_training",
    "position",
    "press",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.761000",
  "usage_context": [
    "balance",
    "clean",
    "error_correction",
    "fatigue",
    "first_pull",
    "... 12 more"
  ],
  "version": "v1.0.0"
}
```

### 7. ow_error_snatch_clean_040_premature_arm_bend

```json
{
  "id": "ow_error_snatch_clean_040_premature_arm_bend",
  "causes": [
    {
      "name": "Non-Specific Correction",
      "topics": [
        "balance",
        "clean",
        "first_pull",
        "position",
        "pull",
        "safety",
        "second_pull",
        "snatch",
        "... 1 more"
      ],
      "points": [
        {
          "text": "We can attempt some non-specific corrections for premature arm bending if the cause is not clear. Essentially these will simply allow the athlete to focus on maintaining relaxed arms and moving through the correct positions with the.",
          "content_hash": "2d2ed95a4aa1facc902fff0465af183b7ba1d5b39f77e2fc4c5ace502ef3c505",
          "signal_tags": [
            "balance",
            "clean",
            "first_pull",
            "position",
            "pull",
            "safety",
            "second_pull",
            "snatch",
            "... 1 more"
          ]
        }
      ],
      "summary": "We can attempt some non-specific corrections for premature arm bending if the cause is not clear. Essentially these will simply allow the athlete to focus on maintaining relaxed arms and moving through the correct positions with the.",
      "content_hash": "1f14ee846ef7a37f4be73b56c6226ceb2ba408539695b7f2b4fcbbb1518ef3ee"
    },
    {
      "name": "Forward Imbalance in Pull",
      "topics": [
        "balance",
        "fatigue",
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "If the athlete’s weight is too far forward over the feet during the first and second pull and the bar is consequently pulling him or her forward, a natural reaction is to row the bar back and up toward the body to correct the imbalance.",
          "content_hash": "d06300338ce4814de81803b9cd5518846796a67920ceb0882d8b1efee66816b4",
          "signal_tags": [
            "balance",
            "fatigue",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Exercises to work on this include:",
          "content_hash": "084a336bbd79870739fc3f110a0cb1cf4b950a9ac9205142071ae9b9a912f1c6",
          "signal_tags": [
            "balance",
            "pull"
          ]
        },
        {
          "text": "Cues that may prove helpful include:",
          "content_hash": "1141bc9eb60d00ec0a4e5192af2b661d1a48491725ad9fe739b44744cedfd129",
          "signal_tags": [
            "balance",
            "pull"
          ]
        }
      ],
      "summary": "If the athlete’s weight is too far forward over the feet during the first and second pull and the bar is consequently pulling him or her forward, a natural reaction is to row the bar back and up toward the body to correct the imbalance. Exercises to work on this include: Cues that may prove helpful include:",
      "content_hash": "9d36c6e07b9668af14784231ce3fa1798631c1eb8e4d35c5853e7398957ad057"
    },
    {
      "name": "Too Far Over The Bar",
      "topics": [
        "balance",
        "jump_training",
        "position",
        "pull",
        "second_pull",
        "technique"
      ],
      "points": [
        {
          "text": "While the shoulders should be at least slightly in front of the bar as the lifter enters the second pull, being too far over the bar can create a number of problems, including forward imbalance, a premature second pull, a forward jump, and.",
          "content_hash": "7bc2de77e8de58041110ab704612c9794d3f5db1da5c737fe246ce463f6bc3e3",
          "signal_tags": [
            "balance",
            "jump_training",
            "position",
            "pull",
            "second_pull",
            "technique"
          ]
        },
        {
          "text": "Cues to help prevent the lifter from allowing the shoulders to move too far in front of the bar include:",
          "content_hash": "01d47bd6a76d1d3d173880ddf7f4b81f6b99a9fe07fa18ba9e082e81bb5e710d"
        }
      ],
      "summary": "While the shoulders should be at least slightly in front of the bar as the lifter enters the second pull, being too far over the bar can create a number of problems, including forward imbalance, a premature second pull, a forward jump, and. Cues to help prevent the lifter from allowing the shoulders to move too far in.",
      "content_hash": "8ad257604fb19d42eb69095d4abe45b4b9cbaaf35e074c95c3f9bb3b474b9839"
    },
    {
      "name": "Premature Second Pull",
      "topics": [
        "balance",
        "first_pull",
        "position",
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "Initiating the second pull early will mean that the bar is relatively low on the thighs when the knees begin to move forward, creating interference for the barbell’s path and pushing it forward. In reaction to this (usually unconscious),.",
          "content_hash": "a13cca992b8dedebee822618a2c01d21f267bd9b46b8ce383d739018d8b3826e",
          "signal_tags": [
            "balance",
            "first_pull",
            "position",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Cues to help the athlete maintain the correct position and time the second pull properly include:",
          "content_hash": "fbefcc0df6fb0a5f59ed7ceb9b16767ba77406b069d77533a0e08e698e0b20bf",
          "signal_tags": [
            "position",
            "pull",
            "second_pull"
          ]
        }
      ],
      "summary": "Initiating the second pull early will mean that the bar is relatively low on the thighs when the knees begin to move forward, creating interference for the barbell’s path and pushing it forward. In reaction to this (usually unconscious),.",
      "content_hash": "05815297889025ee5e919e2f595550e01aea18c90258291426d264b07060ba87"
    },
    {
      "name": "Grip Too Narrow",
      "topics": [
        "clean",
        "error_correction",
        "overhead",
        "position",
        "pull",
        "receiving_position",
        "second_pull",
        "snatch",
        "... 1 more"
      ],
      "points": [
        {
          "text": "The simplest possible cause for premature arm bending is too narrow of a grip on the bar. This causes the bar to be too low on the thighs as the second pull begins, creating the same kind of interference described in the previous error..",
          "content_hash": "a454cf02170dc90df4ddea23c6f94d2a2c40dfad110234868c2c1c60b6fd3248",
          "signal_tags": [
            "error_correction",
            "position",
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "The grip width should be corrected to allow optimal contact with the body (crease of the hip for the snatch and high thigh for the clean) if possible. In some cases, this will not be possible, however. For example, a lifter with very long.",
          "content_hash": "97c5dbf4ee66ad2cfa50425d3b154dc9e617bd7990d14475e65b9608c8674d78",
          "signal_tags": [
            "clean",
            "overhead",
            "position",
            "pull",
            "receiving_position",
            "snatch",
            "technique"
          ]
        },
        {
          "text": "In order to allow the bar to contact higher toward the hip without bending the elbows, the lifter can shrug the shoulders back and slightly up—this can move the bar a significant amount and will have less of a negative effect on the lift.",
          "content_hash": "af7207e4c1b17d79f42e1b43dfca7c720fcbfb86fe7a717779158ea54db28d62",
          "signal_tags": [
            "position"
          ]
        }
      ],
      "summary": "The simplest possible cause for premature arm bending is too narrow of a grip on the bar. This causes the bar to be too low on the thighs as the second pull begins, creating the same kind of interference described in the previous error..",
      "content_hash": "1894c8933d00bedb15cfff9f095dab3f2be3da8b4c30aca498f0ccb19b36141c"
    },
    {
      "name": "Lack Of Confidence",
      "topics": [
        "position",
        "pull",
        "third_pull"
      ],
      "points": [
        {
          "text": "A lack of confidence with the lift will often cause the lifter to bend the arms early, either in an attempt to lift it higher or to pull under early—neither will work if the weight is significant. The confidence in the ability of the legs.",
          "content_hash": "8d56d20b28a05c07f9c0d24f6b4ad730d5cc6520b70b5bef1f728a65ad88820f",
          "signal_tags": [
            "position",
            "pull",
            "third_pull"
          ]
        },
        {
          "text": "Exercises to help correct the problem include:",
          "content_hash": "dfd01c7121b2ff3b8728d9d1f010f910332b06f61615d690f0fb0933c763908d"
        },
        {
          "text": "Cues to help remind the lifter to trust the legs and hips include:",
          "content_hash": "059c49b39bff5b14f6a47aba8f9057f1cf7e5e82e268d4cef31002fae6140a8f"
        }
      ],
      "summary": "A lack of confidence with the lift will often cause the lifter to bend the arms early, either in an attempt to lift it higher or to pull under early—neither will work if the weight is significant. The confidence in the ability of the legs.",
      "content_hash": "4b250af386ea1cdbcf12f10f5c61a6cec65ef2449e04a62cc4cfe4061a8290f1"
    },
    {
      "name": "Grip Too Tight",
      "topics": [
        "clean",
        "position",
        "program_design",
        "snatch",
        "strength",
        "technique"
      ],
      "points": [
        {
          "text": "Premature arm bending may be the result of an excessively tight grip on the bar, which will create excessive tension in the elbow flexors. Gripping the bar too tightly may be a simple mistake or the result of a weak grip or poorly executed.",
          "content_hash": "756c9511756ffe51c0e79587fdcbc37ac213f961a521f7217e7772988fb94bb9",
          "signal_tags": [
            "clean",
            "position",
            "program_design",
            "snatch",
            "strength"
          ]
        },
        {
          "text": "Using straps, however, may help a lifter whose grip strength isn’t a problem get the feel for using only the necessary tension rather than over-gripping. This doesn’t mean that all snatching should be done with straps; they can be used in.",
          "content_hash": "b010ce049f33799c692db43295145eb1e6621f4d0477d74700a209721568ae44",
          "signal_tags": [
            "position",
            "snatch",
            "strength",
            "technique"
          ]
        }
      ],
      "summary": "Premature arm bending may be the result of an excessively tight grip on the bar, which will create excessive tension in the elbow flexors. Gripping the bar too tightly may be a simple mistake or the result of a weak grip or poorly executed.",
      "content_hash": "5dcea71f6f1347468227998851ce44759ad529698808aa3a2f0a850aa285a2b1"
    },
    {
      "name": "Under-Extension",
      "topics": [
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "New lifters will often cut the second pull short in a rush to get under the bar—the hips will not open fully and the shoulders will remain above or even slightly in front of the bar rather than finishing behind the hips and bar. This.",
          "content_hash": "1036fc055563ac16c6781cc7d92e24131f27c15103c187e46bf0dd36b0d368d2",
          "signal_tags": [
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Exercises to help correct this include:",
          "content_hash": "0f43c3a62687f3397933cc90cec57fa42c10aaf70d06768be521591f1bf7f986",
          "signal_tags": [
            "second_pull"
          ]
        },
        {
          "text": "Cues to encourage complete extension in the pull include:",
          "content_hash": "77e6cfecfe64a41c03770da2b0782ff2bac21982f512c594181efa57fdb33e26",
          "signal_tags": [
            "pull",
            "second_pull"
          ]
        }
      ],
      "summary": "New lifters will often cut the second pull short in a rush to get under the bar—the hips will not open fully and the shoulders will remain above or even slightly in front of the bar rather than finishing behind the hips and bar. Exercises to help correct this include: Cues to encourage complete extension in the pull.",
      "content_hash": "29f2550b79c84b2b3840027808df5f0acd2df5c17962f3ef108f03470e89b45e"
    },
    "... 1 more"
  ],
  "coaching_cues": [
    "Ideally during the first and second pulls of the snatch and clean, the lifter’s arms are passively extended.",
    "Essentially these will simply allow the athlete to focus on maintaining relaxed arms and moving through the correct positions with the correct timing.",
    "Generally it’s best to reduce the movement as much as possible and start with a snatch or clean pull from the hang at knee level.",
    "Ensure correct posture and balance in the starting position, and begin with a slow extension, focusing on maintaining relaxed arms.",
    "... 2 more"
  ],
  "common_errors": [
    "Ideally during the first and second pulls of the snatch and clean, the lifter’s arms are passively extended. This allows the maximal transfer of force into the bar from the legs."
  ],
  "content_hash": "8ad20d73498838be31a191594fc41e3301a07df4fbbcb30cace93fc6a4352f64",
  "contraindications": [
    "ankle_pain",
    "high_fatigue",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain",
    "... 1 more"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "The more hip-dominant the lifting style, the less of a negative effect premature arm bend will have, but it does not improve the snatch or clean in any significant way other than.",
    "Reasons for premature arm bend can vary widely, and strategies to correct them vary accordingly.",
    "Non-Specific Correction We can attempt some non-specific corrections for premature arm bending if the cause is not clear.",
    "Essentially these will simply allow the athlete to focus on maintaining relaxed arms and moving through the correct positions with the correct timing.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.762000",
  "description_points": [
    {
      "text": "Ideally during the first and second pulls of the snatch and clean, the lifter’s arms are passively extended. This allows the maximal transfer of force into the bar from the legs and hips. The more hip-dominant the lifting style, the less.",
      "content_hash": "a859e954ebc12461d3684c631df9d81436ce9d4f78f3a88df6ef965f68e01f1b",
      "signal_tags": [
        "clean",
        "pull",
        "recovery",
        "second_pull",
        "snatch"
      ]
    }
  ],
  "error_name": "Premature Arm Bend",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 22,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Premature Arm Bend"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "Ideally during the first and second pulls of the snatch and clean, the lifter’s arms are passively extended. This allows the maximal transfer of force into the bar from the legs and hips.",
  "topics": [
    "balance",
    "bar_path",
    "clean",
    "error_correction",
    "fatigue",
    "first_pull",
    "jump_training",
    "overhead",
    "... 12 more"
  ],
  "updated_at": "2026-06-11T08:04:24.762000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "bar_path",
    "beginner_or_learning_lifter",
    "clean",
    "... 20 more"
  ],
  "version": "v1.0.0"
}
```

### 8. ow_error_snatch_clean_040_early_scoop

```json
{
  "id": "ow_error_snatch_clean_040_early_scoop",
  "causes": [
    {
      "name": "Improper Timing of Second Pull",
      "topics": [
        "pull",
        "second_pull"
      ],
      "points": [
        {
          "text": "The athlete may simply be initiating the final upward explosion too early due to improper instruction, impatience or lack of confidence. Exercises to help train and practice better timing include:",
          "content_hash": "3e081ad6d60b06bf4447ff4c4c59f6c994b8445358b993e8f68131f653c3892b",
          "signal_tags": [
            "pull",
            "second_pull"
          ]
        },
        {
          "text": "Cues to help the athlete improve the timing of the second pull include:",
          "content_hash": "96b0a9ce16108c897b3d4a75ec0df4b3f42ae3e3017fb608be6134a452322028",
          "signal_tags": [
            "pull",
            "second_pull"
          ]
        }
      ],
      "summary": "The athlete may simply be initiating the final upward explosion too early due to improper instruction, impatience or lack of confidence. Exercises to help train and practice better timing include: Cues to help the athlete improve the timing of the second pull include:",
      "content_hash": "05ce749c47c237a6dbe9c8a83a9897f6cc6ea4cee1f5e6832f3b06252edd265d"
    },
    {
      "name": "Intentional Double Knee Bend",
      "topics": [
        "balance",
        "clean",
        "first_pull",
        "position",
        "power",
        "pull",
        "second_pull",
        "snatch"
      ],
      "points": [
        {
          "text": "As was discussed in the Double Knee Bend chapter of the book, the phenomenon is a natural reaction to the proper timing, positions and actions of the snatch and clean pull. Performing it intentionally will nearly always cause the knees to.",
          "content_hash": "76ce780126b584a085e155ae384295c9c56002a73e03b28b1b1b8f922dbe1b7f",
          "signal_tags": [
            "balance",
            "clean",
            "first_pull",
            "position",
            "power",
            "pull",
            "second_pull",
            "snatch"
          ]
        },
        {
          "text": "Exercises to help the athlete learn to allow the double knee bend to occur naturally and at the correct time include:",
          "content_hash": "316686546020617bc7392d9f61735f18a5ef6ceb5175ef84bd8191ab4001cfd2",
          "signal_tags": [
            "first_pull"
          ]
        }
      ],
      "summary": "As was discussed in the Double Knee Bend chapter of the book, the phenomenon is a natural reaction to the proper timing, positions and actions of the snatch and clean pull. Performing it intentionally will nearly always cause the knees to.",
      "content_hash": "42356b9b980dc7587378ed87d5105a1ae2815df0ff2894701177a46f7853b89c"
    },
    {
      "name": "Forward Imbalance in Pull",
      "topics": [
        "balance",
        "error_correction",
        "first_pull",
        "jump_training",
        "position",
        "pull",
        "second_pull",
        "starting_position"
      ],
      "points": [
        {
          "text": "Forward imbalance in the pull will usually force the lifter to initiate the second pull (and the scoop as a part of it) prematurely in order to rebalance the system before it exceeds the threshold of possible correction. This includes the.",
          "content_hash": "0c735fda17afd7a3c9cc1b1addf41cc29d2be50427945fab58c5b5c439e865a5",
          "signal_tags": [
            "balance",
            "error_correction",
            "first_pull",
            "jump_training",
            "position",
            "pull",
            "second_pull",
            "starting_position"
          ]
        }
      ],
      "summary": "Forward imbalance in the pull will usually force the lifter to initiate the second pull (and the scoop as a part of it) prematurely in order to rebalance the system before it exceeds the threshold of possible correction.",
      "content_hash": "dd321d9d8ece46b5d0988adae984fdcd1e7aa32f388717a6f69b548d9c033ac3"
    },
    {
      "name": "Postural Weakness",
      "topics": [
        "position",
        "strength",
        "technique"
      ],
      "points": [
        {
          "text": "Finally, a premature scoop may simply be the result of the lifter being physically incapable of maintaining the proper position over the bar to a high enough point. No amount of cuing or technique work will correct this, although it will.",
          "content_hash": "0bab495d25ef55252dd02a9fb45a10c3675ec7d2ce46c74fe4780fae2c5737c4",
          "signal_tags": [
            "position",
            "strength",
            "technique"
          ]
        }
      ],
      "summary": "Finally, a premature scoop may simply be the result of the lifter being physically incapable of maintaining the proper position over the bar to a high enough point. No amount of cuing or technique work will correct this, although it will.",
      "content_hash": "5d37b7f17898579a513625d0582789c0d34a96f4eeb71959ba4907f83ff3c6ec"
    }
  ],
  "coaching_cues": [
    "An early scoop can be a symptom of another problem, as seen previously, and can be a problem itself by reducing speed, power and bar elevation, and shifting the lifter’s balance.",
    "Improper Timing of Second Pull The athlete may simply be initiating the final upward explosion too early due to improper instruction, impatience or lack of confidence.",
    "Exercises to help train and practice better timing include: Cues to help the athlete improve the timing of the second pull include: Intentional Double Knee Bend As was discussed.",
    "Performing it intentionally will nearly always cause the knees to move forward too soon, resulting in poor balance over the feet, reduced bar speed, and less power in the final.",
    "... 2 more"
  ],
  "common_errors": [
    "An early scoop can be a symptom of another problem, as seen previously, and can be a problem itself by reducing speed, power and bar elevation, and shifting the lifter’s balance."
  ],
  "content_hash": "0cba3e3b84abe85c15249f7ccc8f62a4865752b7c2c2c27c6b2ef0b847ee1aa4",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "correction_signal_tags": [
    "coaching_cues",
    "corrective_exercises"
  ],
  "corrections": [
    "Exercises to help train and practice better timing include: Cues to help the athlete improve the timing of the second pull include: Intentional Double Knee Bend As was discussed.",
    "Performing it intentionally will nearly always cause the knees to move forward too soon, resulting in poor balance over the feet, reduced bar speed, and less power in the final.",
    "Exercises to help the athlete learn to allow the double knee bend to occur naturally and at the correct time include: Forward Imbalance in Pull Forward imbalance in the pull will.",
    "See the exercises and cues under the Jumping Forward section.",
    "... 1 more"
  ],
  "created_at": "2026-06-11T08:04:24.765000",
  "description_points": [
    {
      "text": "An early scoop can be a symptom of another problem, as seen previously, and can be a problem itself by reducing speed, power and bar elevation, and shifting the lifter’s balance forward.",
      "content_hash": "b71b386c253d62a3f0e81f95ef068614be8fa4ea29c10063605696607e190a2e",
      "signal_tags": [
        "balance",
        "power"
      ]
    }
  ],
  "error_name": "Early Scoop",
  "expert_validation_status": "pending",
  "knowledge_type": "technical_error",
  "lift": "snatch_clean",
  "paragraph_count": 7,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_040_universal_errors",
      "section_title": "Universal Errors",
      "epub_file": "OEBPS/text00039.html",
      "heading": "Early Scoop"
    }
  ],
  "source_section_id": "ow_section_040_universal_errors",
  "summary": "An early scoop can be a symptom of another problem, as seen previously, and can be a problem itself by reducing speed, power and bar elevation, and shifting the lifter’s balance forward. Improper Timing of Second Pull The athlete may simply be initiating the final upward explosion too early due to improper.",
  "topics": [
    "balance",
    "clean",
    "error_correction",
    "first_pull",
    "jump_training",
    "position",
    "power",
    "pull",
    "... 5 more"
  ],
  "updated_at": "2026-06-11T08:04:24.765000",
  "usage_context": [
    "balance",
    "clean",
    "error_correction",
    "first_pull",
    "jump_training",
    "... 9 more"
  ],
  "version": "v1.0.0"
}
```

## `coaching_progressions` Samples

Showing `8` of `50` documents.

### 1. The Progression Process

```json
{
  "id": "ow_coach_all_lifts_010_001_the_progression_process",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "For example, an athlete of an appropriate age who learns very quickly may move in short order into a training cycle with significant loading in the competition lifts; on the other."
  ],
  "content_hash": "c206918b1e53f0a3428d3b234f9f527bde82082ed4b96351a88f4f85e7fcf2ba",
  "created_at": "2026-06-11T08:04:24.833000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "all_lifts",
  "paragraph_count": 3,
  "progression_steps": [
    "The process of teaching or learning the snatch and clean & jerk will vary considerably in duration.",
    "The progression presented in this book is not intended to be undertaken in any specific period of time; it will need to be implemented appropriately for each athlete.",
    "This can range from teaching the foundational elements, snatch, clean and jerk each over the course of a few training sessions, to spending several weeks, and possibly longer,.",
    "It is presented, however, with the steps in the recommended order, from foundational elements through the completion of each lift.",
    "Further, what occurs after the lifter has learned to perform the snatch and clean & jerk reasonably well will vary.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_010_learning_and_teaching_the_lifts",
      "section_title": "Learning & Teaching the Lifts",
      "epub_file": "OEBPS/text00009.html",
      "heading": "The Progression Process"
    }
  ],
  "source_section_id": "ow_section_010_learning_and_teaching_the_lifts",
  "stage": "the_progression_process",
  "summary": "The process of teaching or learning the snatch and clean & jerk will vary considerably in duration. The progression presented in this book is not intended to be undertaken in any specific period of time; it will need to be implemented appropriately for each athlete.",
  "title": "The Progression Process",
  "topics": [
    "clean",
    "competition",
    "jerk",
    "mobility",
    "program_design",
    "snatch",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.833000",
  "usage_context": [
    "beginner_or_learning_lifter",
    "clean",
    "competition",
    "jerk",
    "mobility",
    "... 5 more"
  ],
  "version": "v1.0.0"
}
```

### 2. Implementing the Progression Drills

```json
{
  "id": "ow_coach_all_lifts_010_002_implementing_the_progression_drills",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "For example, these athletes may train the snatch or power snatch from the hang only and perform snatch pulls and overhead squats for a period of time, and then later learn the.",
    "It needs to be understood very clearly that there is a simple order of priorities throughout the learning process: Position, movement, speed, load.",
    "Performing a correct movement from an incorrect position is impossible, because it is, by definition, a different movement, and the introduction of excessive speed or weight.",
    "These points are critical to keep in mind at this earliest stage of learning.",
    "... 2 more"
  ],
  "content_hash": "561cef49c47dff1928c7c896b93daeb77fca1d4c1aedf9832817820fcc86076c",
  "contraindications": [
    "hip_pain",
    "knee_pain",
    "shoulder_pain"
  ],
  "corrections": [
    "The teaching progression drills for the snatch, clean and jerk are presented in following sections of the book.",
    "When and how these drills are introduced and practiced by various athletes can vary considerably.",
    "In most situations of athletes in the late teens to adult age with existing training experience, the drills for a given lift will all be learned and practiced together in a single.",
    "In other cases, the coach may choose to introduce only certain drills in a given session, and expose the athlete to the complete progression in smaller individual doses over a.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.835000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "coaching_progression",
  "lift": "all_lifts",
  "paragraph_count": 9,
  "progression_steps": [
    "The teaching progression drills for the snatch, clean and jerk are presented in following sections of the book.",
    "In most situations of athletes in the late teens to adult age with existing training experience, the drills for a given lift will all be learned and practiced together in a single.",
    "In other cases, the coach may choose to introduce only certain drills in a given session, and expose the athlete to the complete progression in smaller individual doses over a.",
    "A more gradual progression is usually a better choice for young athletes beginning to specialize in weightlifting in combination with instruction and practice of general and.",
    "For example, these athletes may train the snatch or power snatch from the hang only and perform snatch pulls and overhead squats for a period of time, and then later learn the.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_010_learning_and_teaching_the_lifts",
      "section_title": "Learning & Teaching the Lifts",
      "epub_file": "OEBPS/text00009.html",
      "heading": "Implementing the Progression Drills"
    }
  ],
  "source_section_id": "ow_section_010_learning_and_teaching_the_lifts",
  "stage": "implementing_the_progression_drills",
  "summary": "The teaching progression drills for the snatch, clean and jerk are presented in following sections of the book. When and how these drills are introduced and practiced by various athletes can vary considerably.",
  "title": "Implementing the Progression Drills",
  "topics": [
    "balance",
    "clean",
    "first_pull",
    "jerk",
    "loading",
    "overhead",
    "position",
    "power",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.835000",
  "usage_context": [
    "balance",
    "beginner_or_learning_lifter",
    "clean",
    "first_pull",
    "jerk",
    "... 14 more"
  ],
  "version": "v1.0.0"
}
```

### 3. Coaching

```json
{
  "id": "ow_coach_all_lifts_010_003_coaching",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "For any coach, the success of the athletes must be the top priority by a significant margin—any interest on the coach’s part in public recognition, appreciation or fame is.",
    "Coaches who consistently produces exemplary weightlifters will receive their due credit and recognition eventually without actively seeking it."
  ],
  "content_hash": "c57a01bffd22068445c25939969161af949a4ac3d8aea73bc22b253e87d5694c",
  "contraindications": [
    "high_fatigue",
    "hip_pain",
    "low_back_pain"
  ],
  "corrections": [
    "And most troubling, it seems evident that giving credit and paying respect to lineage is often not overlooked, but actually intentionally avoided.",
    "Not practice the lifts, not enjoy the lifts, not do the lifts as part of another sport or activity, but live the life—live a life that is constructed around the demands of being a."
  ],
  "created_at": "2026-06-11T08:04:24.837000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "all_lifts",
  "paragraph_count": 12,
  "progression_steps": [
    "The coach needs to be committed fully to the preparation and success of his or her weightlifters, not only to create the optimal programming prescriptions, but to provide the.",
    "Lineage & Legacy All great craftsmen learn from those who have come before them—the best learn from experience working directly under the masters.",
    "A new coach can learn from books, video, magazines and articles, but this kind of learning is incomplete and lacking the intangible quality that is truly the key to solving the.",
    "Presumably the individuals posing as spontaneously materializing coaches are doing so because they believe it bolsters their image—geniuses who needed no teaching or assistance to.",
    "It’s easy to be a technician—to learn protocols and algorithms and repeat what has been said or written, particularly these days when so much information is so readily available.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_010_learning_and_teaching_the_lifts",
      "section_title": "Learning & Teaching the Lifts",
      "epub_file": "OEBPS/text00009.html",
      "heading": "Coaching"
    }
  ],
  "source_section_id": "ow_section_010_learning_and_teaching_the_lifts",
  "stage": "coaching",
  "summary": "Coaching is an art form encompassing multiple disciplines and fields of knowledge that must be blended in such a way that the lines of delineation among them are blurred if not erased. It’s the knowledge and understanding of relevant scientific principles, the experience of implementation of training methodologies,.",
  "title": "Coaching",
  "topics": [
    "assessment",
    "fatigue",
    "masters",
    "position",
    "program_design",
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:24.837000",
  "usage_context": [
    "assessment",
    "beginner_or_learning_lifter",
    "fatigue",
    "masters",
    "position",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

### 4. The Mid-Hang Position

```json
{
  "id": "ow_coach_snatch_023_002_the_mid_hang_position",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "The first step is establishing the mid-hang position (Figure 14.1), in which the bar is positioned at approximately the level of mid-thigh.",
    "This is the position from which the athlete will first learn to snatch before learning the pull from the floor.",
    "The importance of the mid-hang position cannot be overstated—it is the position he or she will be in immediately prior to the initiation of the final explosion of the hips and.",
    "The precision and consistency of this position will have enormous influence on the successfulness of the lifter’s snatches.",
    "... 2 more"
  ],
  "content_hash": "4ab6198a3be3c52dafd847ce96dbec6e1c141e116c3ad866204a46ae3727e1e9",
  "contraindications": [
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain",
    "wrist_pain"
  ],
  "corrections": [
    "Athletes will commonly want to move the bar farther down the thighs than they should, and over the course of a series of drills starting from the mid-hang position, the bar height.",
    "It’s important in this early stage to establish and reinforce the correct position by preventing this divergence.",
    "Learning and practicing it at this point is far easier than attempting to correct problems related to this position later."
  ],
  "created_at": "2026-06-11T08:04:24.845000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "snatch",
  "paragraph_count": 8,
  "progression_steps": [
    "The first step is establishing the mid-hang position (Figure 14.1), in which the bar is positioned at approximately the level of mid-thigh.",
    "This is the position from which the athlete will first learn to snatch before learning the pull from the floor.",
    "Learning and ingraining it at the earliest stages of training will maximize the lifter’s progress.",
    "The mid-hang position begins familiarizing the athlete with the proper positioning and timing for the all-important second pull, and allows the double knee bend to occur naturally.",
    "Athletes will commonly want to move the bar farther down the thighs than they should, and over the course of a series of drills starting from the mid-hang position, the bar height.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html",
      "heading": "The Mid-Hang Position"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "stage": "the_mid_hang_position",
  "summary": "The first step is establishing the mid-hang position (Figure 14.1), in which the bar is positioned at approximately the level of mid-thigh. This is the position from which the athlete will first learn to snatch before learning the pull from the floor.",
  "title": "The Mid-Hang Position",
  "topics": [
    "balance",
    "bracing",
    "first_pull",
    "position",
    "press",
    "pull",
    "recovery",
    "safety",
    "... 2 more"
  ],
  "updated_at": "2026-06-11T08:04:24.845000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "beginner_or_learning_lifter",
    "bracing",
    "first_pull",
    "... 9 more"
  ],
  "version": "v1.0.0"
}
```

### 5. Mid-Hang Snatch Jump

```json
{
  "id": "ow_coach_snatch_023_003_mid_hang_snatch_jump",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "The mid-hang snatch jump (Figure 14.3) provides an opportunity for the athlete to feel a violent, concerted explosion of the hips and knees from the proper position while.",
    "This movement will not look exactly like the finish of a snatch; the point is not to mimic the lift perfectly, but to create an extremely quick, sharp extension of the hips and.",
    "Starting in the mid-hang position, the athlete will simply jump vertically as high as possible while actively pushing the bar back with the lats and shoulders to maintain light.",
    "There should be no countermovement to begin the jump—it must be performed directly from the static mid-thigh position.",
    "... 2 more"
  ],
  "content_hash": "9ef0e4e8d2c328acd70b355846c189ece530591ce92af408b0679170b1e5416d",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "corrections": [
    "The presence of this drill should not be misinterpreted to mean that the athlete should jump in the air when snatching, as has been discussed in previous chapters.",
    "Too often athletes fixate on either hip or knee extension and neglect the other; this drill helps establish the feeling of both contributing simultaneously to the explosion.",
    "Starting in the mid-hang position, the athlete will simply jump vertically as high as possible while actively pushing the bar back with the lats and shoulders to maintain light.",
    "Prior to each jump, the athlete should be sure to have his or her weight balanced over the front edge of the heel, and to prevent a last-moment shift of balance to the balls of.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.846000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "snatch",
  "paragraph_count": 5,
  "progression_steps": [
    "Too often athletes fixate on either hip or knee extension and neglect the other; this drill helps establish the feeling of both contributing simultaneously to the explosion.",
    "Starting in the mid-hang position, the athlete will simply jump vertically as high as possible while actively pushing the bar back with the lats and shoulders to maintain light.",
    "There should be no countermovement to begin the jump—it must be performed directly from the static mid-thigh position.",
    "It’s equally important for the bar to start at the correct height on the thigh—this jumping motion must be extremely brief and violent like the second pull will be in the snatch.",
    "The movement will be refined in the next drill and continue increasing in precision throughout the learning process."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html",
      "heading": "Mid-Hang Snatch Jump"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "stage": "mid_hang_snatch_jump",
  "summary": "The mid-hang snatch jump (Figure 14.3) provides an opportunity for the athlete to feel a violent, concerted explosion of the hips and knees from the proper position while controlling the bar’s proximity to the body. The presence of this drill should not be misinterpreted to mean that the athlete should jump in the air.",
  "title": "Mid-Hang Snatch Jump",
  "topics": [
    "balance",
    "bar_path",
    "first_pull",
    "jump_training",
    "position",
    "pull",
    "safety",
    "second_pull",
    "... 1 more"
  ],
  "updated_at": "2026-06-11T08:04:24.846000",
  "usage_context": [
    "balance",
    "bar_path",
    "beginner_or_learning_lifter",
    "first_pull",
    "jump_training",
    "... 7 more"
  ],
  "version": "v1.0.0"
}
```

### 6. Mid-Hang Snatch Pull

```json
{
  "id": "ow_coach_snatch_023_004_mid_hang_snatch_pull",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "The mid-hang snatch pull (Figure 14.4) brings together the aggressive concerted hip and knee extension of the mid-hang snatch jump and the precision necessary to channel it into.",
    "This movement—the second pull of the lift in isolation—is responsible for the most critical acceleration of the barbell, and will directly influence the precision and speed of the.",
    "Essentially, the athlete will perform the mid-hang snatch jump drill while keeping the balls of the feet connected to the floor at the top of the extension.",
    "The intent is still aggressive leg drive against the floor that continues into complete knee extension and the force of which naturally causes the athlete to rise onto the balls.",
    "... 2 more"
  ],
  "content_hash": "bd0b5ad3782b6e85231d9485e1eeac764b8be07ba4b26763467de8257cf9b790",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "corrections": [
    "The importance of learning and practicing this section correctly cannot be overstated.",
    "It can be difficult for athletes initially to feel the movement and perform it properly with the weightlessness of a PVC bar; if needed, an empty barbell can be used in this stage.",
    "Essentially, the athlete will perform the mid-hang snatch jump drill while keeping the balls of the feet connected to the floor at the top of the extension.",
    "Additionally, although the goal is to mimic the leg drive of the vertical jump from the previous drill, the magnitude of the force needs to be controlled to prevent the athlete.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.848000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "snatch",
  "paragraph_count": 15,
  "progression_steps": [
    "The importance of learning and practicing this section correctly cannot be overstated.",
    "It can be difficult for athletes initially to feel the movement and perform it properly with the weightlessness of a PVC bar; if needed, an empty barbell can be used in this stage.",
    "The feet should remain in the same position on the floor from start to finish—if the athlete is sliding forward, he or she has the weight balanced too far forward over the feet.",
    "During the extension, the bar should remain in immediate proximity to the thighs and then come into full contact at the hips.",
    "However, the shrug will span both the end of the second pull and beginning of the third pull—it is transitional and consequently needs to be present in the segments of the lift on.",
    "... 1 more"
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html",
      "heading": "Mid-Hang Snatch Pull"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "stage": "mid_hang_snatch_pull",
  "summary": "The mid-hang snatch pull (Figure 14.4) brings together the aggressive concerted hip and knee extension of the mid-hang snatch jump and the precision necessary to channel it into what will become the second pull of the snatch. The importance of learning and practicing this section correctly cannot be overstated.",
  "title": "Mid-Hang Snatch Pull",
  "topics": [
    "balance",
    "bar_path",
    "first_pull",
    "jump_training",
    "mobility",
    "position",
    "press",
    "pull",
    "... 4 more"
  ],
  "updated_at": "2026-06-11T08:04:24.848000",
  "usage_context": [
    "balance",
    "bar_path",
    "beginner_or_learning_lifter",
    "first_pull",
    "jump_training",
    "... 11 more"
  ],
  "version": "v1.0.0"
}
```

### 7. Remedial Modification

```json
{
  "id": "ow_coach_snatch_023_005_remedial_modification",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "If an athlete is struggling to correctly perform the vertical leg drive in this drill, a remedial modification can be used to help temporarily before returning to the standard.",
    "Rather than beginning at the mid-hang position, the lifter will start in a dip position in which only the knees are bent, the trunk vertical, and the bar in contact in the crease.",
    "From this position, the movement is greatly simplified and it will be easy for the athlete to focus on driving vertically against the ground with the legs.",
    "All other criteria for the lift remain the same, such as keeping the bar against the body and finishing with the shoulders slightly behind the hips with the balance still over the."
  ],
  "content_hash": "84da665a5abc2c04f57b8fad5a70ed6c152549b42b409e88b7fcf74e33410eba",
  "corrections": [
    "If an athlete is struggling to correctly perform the vertical leg drive in this drill, a remedial modification can be used to help temporarily before returning to the standard."
  ],
  "created_at": "2026-06-11T08:04:24.849000",
  "expert_validation_status": "pending",
  "heading_level": "heading-c",
  "knowledge_type": "coaching_progression",
  "lift": "snatch",
  "paragraph_count": 1,
  "progression_steps": [
    "Rather than beginning at the mid-hang position, the lifter will start in a dip position in which only the knees are bent, the trunk vertical, and the bar in contact in the crease."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html",
      "heading": "Remedial Modification"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "stage": "remedial_modification",
  "summary": "If an athlete is struggling to correctly perform the vertical leg drive in this drill, a remedial modification can be used to help temporarily before returning to the standard exercise (Figure 14.7). Rather than beginning at the mid-hang position, the lifter will start in a dip position in which only the knees are.",
  "title": "Remedial Modification",
  "topics": [
    "balance",
    "bracing",
    "first_pull",
    "position",
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:24.849000",
  "usage_context": [
    "balance",
    "bracing",
    "first_pull",
    "position",
    "recovery",
    "... 1 more"
  ],
  "version": "v1.0.0"
}
```

### 8. Tall Muscle Snatch

```json
{
  "id": "ow_coach_snatch_023_006_tall_muscle_snatch",
  "app_usage": "Use as teaching order, progression, regression, and correction context.",
  "coaching_cues": [
    "The tall muscle snatch (Figure 14.8) introduces the isolated movement of the upper body during the third pull.",
    "In an actual snatch, the arms actively bend only to pull the lifter underneath the bar, and consequently, there should be no active elbow flexion without concurrent downward.",
    "However, the mechanics of the upper body in the third pull are critical for successful lifting, and therefore isolated introduction and practice is warranted at this stage.",
    "The athlete will begin in the tall position—standing straight up with the bar hanging at arms’ length, the weight balanced over the front edge of the heel, and the arms internally.",
    "... 2 more"
  ],
  "content_hash": "92a303032c0498eb29ffa093a32dec57a3dfadd6e1d782e6251f875511efae89",
  "corrections": [
    "However, the mechanics of the upper body in the third pull are critical for successful lifting, and therefore isolated introduction and practice is warranted at this stage.",
    "As the elbows reach their maximum height, which will vary somewhat depending on the athlete’s build and present mobility, the lifter will turn the arms over to bring the bar.",
    "If the hook is released too early, the lifter has to relax the grip and will lose the necessary tight connection to the bar; if the hook is released too late, the bar will already.",
    "The importance of internally rotating the arms to orient the elbows outward from the start of the lift should become apparent in this exercise.",
    "... 2 more"
  ],
  "created_at": "2026-06-11T08:04:24.850000",
  "expert_validation_status": "pending",
  "heading_level": "heading-a",
  "knowledge_type": "coaching_progression",
  "lift": "snatch",
  "paragraph_count": 8,
  "progression_steps": [
    "At this point, the progression has diverged from strict reality by bending the arms to elevate the bar without any downward movement of the athlete.",
    "However, the mechanics of the upper body in the third pull are critical for successful lifting, and therefore isolated introduction and practice is warranted at this stage.",
    "The athlete will begin in the tall position—standing straight up with the bar hanging at arms’ length, the weight balanced over the front edge of the heel, and the arms internally.",
    "The turnover is not simply the action of swinging the bar around the head and back into its final position—it is an active pull of the elbows up and out, then a rotation of the.",
    "The importance of internally rotating the arms to orient the elbows outward from the start of the lift should become apparent in this exercise."
  ],
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html",
      "heading": "Tall Muscle Snatch"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "stage": "tall_muscle_snatch",
  "summary": "The tall muscle snatch (Figure 14.8) introduces the isolated movement of the upper body during the third pull. At this point, the progression has diverged from strict reality by bending the arms to elevate the bar without any downward movement of the athlete.",
  "title": "Tall Muscle Snatch",
  "topics": [
    "balance",
    "bar_path",
    "mobility",
    "overhead",
    "position",
    "power",
    "press",
    "pull",
    "... 6 more"
  ],
  "updated_at": "2026-06-11T08:04:24.850000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "bar_path",
    "mobility",
    "mobility_limitation",
    "... 13 more"
  ],
  "version": "v1.0.0"
}
```

## `mobility_drills` Samples

Showing `8` of `33` documents.

### 1. Optimal Mobility

```json
{
  "id": "ow_mobility_principle_083_001_optimal_mobility",
  "body_regions": [
    "hip",
    "lat",
    "shoulder",
    "thoracic_spine",
    "trunk"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "This is important to keep in mind when considering the mobility-injury-performance curve: increasing mobility will increase performance and decrease risk of injury if an athlete.",
    "The poor rack position may prevent a solid connection between the bar and torso, limiting the athlete’s ability to accelerate the bar upward; it may place the bar too far forward.",
    "As the immobility that prevents proper positioning is reduced, the athlete’s ability to jerk will increase accordingly within his or her strength, explosiveness and technical.",
    "Once the athlete has achieved as much mobility as is required for perfect jerk positions and motions, further increases in mobility will have no more positive effect on jerk."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "high_fatigue",
    "hip_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:25.183000",
  "expert_validation_status": "pending",
  "instructions": [
    "The field of athletic training is abounding with conflicting information regarding mobility and stretching.",
    "The reigning popular notion of mobility and stretching is that their relationships to both athletic performance and injury protection are positive and linear; that is, as.",
    "The actual research and experience of coaches and athletes, however, have failed to demonstrate this relationship, and the evidence in concert with a dose of reason suggests a.",
    "It’s more likely that the relationship of mobility to both injury and performance describes a modified bell curve; that is, both hypomobility and hypermobility increase the risk.",
    "However, in close proximity to the apex representing optimal mobility—the degree of mobility associated with the least risk of injury and the greatest performance—hypomobility is."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Optimal Mobility",
  "paragraph_count": 5,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Optimal Mobility"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "The field of athletic training is abounding with conflicting information regarding mobility and stretching. The reigning popular notion of mobility and stretching is that their relationships to both athletic performance and injury protection are positive and linear; that is, as stretching and mobility increase, so do.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.183000",
  "usage_context": [
    "advanced_or_heavy_training",
    "bar_path",
    "fatigue",
    "jerk",
    "mobility",
    "... 9 more"
  ],
  "version": "v1.0.0"
}
```

### 2. Supported & Unsupported Range of Motion

```json
{
  "id": "ow_mobility_principle_083_002_supported_and_unsupported_range_of_motio",
  "body_regions": [
    "lat"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "The supported range of motion is the portion of the movement in which the athlete is able to maintain stability through the effort of the muscles and nervous system feedback and.",
    "This athlete will require specific flexibility and mobility work to increase range of motion; the weightlifting training will help maintain the balance between mobility and.",
    "A hypermobile athlete, on the other hand, may have range of motion that exceeds what is necessary for weightlifting, and in the range beyond necessary is likely to be unstable, as."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "low_back_pain"
  ],
  "created_at": "2026-06-11T08:04:25.184000",
  "expert_validation_status": "pending",
  "instructions": [
    "The issue of stability brings into consideration the idea of supported and unsupported ranges of motion.",
    "The supported range of motion is the portion of the movement in which the athlete is able to maintain stability through the effort of the muscles and nervous system feedback and.",
    "The goal of mobility work for the weightlifter is to minimize and eventually eliminate any unsupported range of motion to reduce the potential for instability and injury.",
    "The process can involve both increasing stability and actually reducing mobility; how much of each is required depends on the athlete’s present levels of stability and mobility.",
    "For example, an immobile new lifter will not have any unsupported range of motion because his or her range of motion has not even reached the minimal requirement."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Supported & Unsupported Range of Motion",
  "paragraph_count": 4,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Supported & Unsupported Range of Motion"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "The issue of stability brings into consideration the idea of supported and unsupported ranges of motion. The supported range of motion is the portion of the movement in which the athlete is able to maintain stability through the effort of the muscles and nervous system feedback and responses; the unsupported range of.",
  "updated_at": "2026-06-11T08:04:25.184000",
  "usage_context": [
    "balance",
    "beginner_or_learning_lifter",
    "mobility",
    "mobility_limitation",
    "pain_or_injury_caution",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

### 3. Determining Mobility Demands

```json
{
  "id": "ow_mobility_principle_083_003_determining_mobility_demands",
  "body_regions": [
    "hip",
    "lat",
    "shoulder",
    "trunk"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "Universal mobility requirements include the ability to squat with the thighs past a horizontal position while maintaining a neutral spine, properly aligned knees and flat feet;."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:25.184000",
  "expert_validation_status": "pending",
  "instructions": [
    "As should be clear with any consideration, the demands of mobility will vary, sometimes greatly, among sports.",
    "The first step of developing any mobility protocol is determining the needs of the athlete.",
    "There are two categories of mobility requirements—universal and sport-specific.",
    "That is, there is a range of motion for each joint and a degree of collective mobility that can be considered necessary to support orthopedic health and functional capacity for.",
    "Universal mobility requirements include the ability to squat with the thighs past a horizontal position while maintaining a neutral spine, properly aligned knees and flat feet;."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Determining Mobility Demands",
  "paragraph_count": 3,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Determining Mobility Demands"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "As should be clear with any consideration, the demands of mobility will vary, sometimes greatly, among sports. The first step of developing any mobility protocol is determining the needs of the athlete.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.184000",
  "usage_context": [
    "first_pull",
    "mobility",
    "mobility_limitation",
    "position",
    "squat",
    "... 1 more"
  ],
  "version": "v1.0.0"
}
```

### 4. Mobility Requirements

```json
{
  "id": "ow_mobility_principle_083_005_mobility_requirements",
  "body_regions": [
    "ankle",
    "hip",
    "shoulder",
    "thoracic_spine",
    "trunk",
    "wrist"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "Specific mobility requirements are simply the positions and ranges of motion demanded by the athlete’s sport.",
    "For weightlifting, the necessary positions have been described in great detail throughout this book.",
    "Weightlifters are required to be capable of achieving the following positions according to the criteria discussed in the relevant chapters: &#9; Generalizations can certainly be.",
    "Problems tend to exist with thoracic spine and shoulder mobility in the overhead position for both the snatch and jerk; with the hips at the bottom of the squat and the starting."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "ankle_pain",
    "hip_pain",
    "knee_pain",
    "low_back_pain",
    "shoulder_pain",
    "wrist_pain"
  ],
  "created_at": "2026-06-11T08:04:25.185000",
  "expert_validation_status": "pending",
  "instructions": [
    "Specific mobility requirements are simply the positions and ranges of motion demanded by the athlete’s sport.",
    "Any experienced athlete or coach will be able to quickly and easily identify these with little effort.",
    "For weightlifting, the necessary positions have been described in great detail throughout this book.",
    "Weightlifters are required to be capable of achieving the following positions according to the criteria discussed in the relevant chapters: &#9; Generalizations can certainly be.",
    "Problems tend to exist with thoracic spine and shoulder mobility in the overhead position for both the snatch and jerk; with the hips at the bottom of the squat and the starting."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Mobility Requirements",
  "paragraph_count": 3,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Mobility Requirements"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "Specific mobility requirements are simply the positions and ranges of motion demanded by the athlete’s sport. Any experienced athlete or coach will be able to quickly and easily identify these with little effort.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.185000",
  "usage_context": [
    "advanced_or_heavy_training",
    "clean",
    "jerk",
    "mobility",
    "mobility_limitation",
    "... 6 more"
  ],
  "version": "v1.0.0"
}
```

### 5. Expectations

```json
{
  "id": "ow_mobility_principle_083_006_expectations",
  "category": "mobility_principles",
  "coaching_cues": [
    "Extremely mobile athletes have preserved and improved upon the natural mobility of youth, and in many cases, are predisposed anatomically to allow maximal range of motion.",
    "There is unquestionably a limit to how much mobility can be improved in an adult athlete; however, it can be improved with consistent long-term hard work.",
    "An adult who has allowed his or her natural juvenile mobility to be reduced through a lack of adequate movement will never be able to achieve the same degree of mobility as an."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-06-11T08:04:25.185000",
  "expert_validation_status": "pending",
  "instructions": [
    "Extremely mobile athletes have preserved and improved upon the natural mobility of youth, and in many cases, are predisposed anatomically to allow maximal range of motion.",
    "There is unquestionably a limit to how much mobility can be improved in an adult athlete; however, it can be improved with consistent long-term hard work.",
    "An adult who has allowed his or her natural juvenile mobility to be reduced through a lack of adequate movement will never be able to achieve the same degree of mobility as an.",
    "Expectations should be adjusted accordingly, but the pursuit of improved mobility by adults should not be abandoned."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Expectations",
  "paragraph_count": 1,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Expectations"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "Extremely mobile athletes have preserved and improved upon the natural mobility of youth, and in many cases, are predisposed anatomically to allow maximal range of motion. There is unquestionably a limit to how much mobility can be improved in an adult athlete; however, it can be improved with consistent long-term.",
  "updated_at": "2026-06-11T08:04:25.185000",
  "usage_context": [
    "advanced_or_heavy_training",
    "mobility",
    "mobility_limitation",
    "youth"
  ],
  "version": "v1.0.0"
}
```

### 6. Mobility Training Protocols

```json
{
  "id": "ow_mobility_principle_083_007_mobility_training_protocols",
  "body_regions": [
    "shoulder"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "Just as we approach training from the perspective of movement and position rather than the use of specific muscles, so too should we primarily concern ourselves with positions and.",
    "In other words, we need to determine in which positions an athlete is immobile, and then find or create exercises that improve these inadequate ranges of motion."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-06-11T08:04:25.186000",
  "expert_validation_status": "pending",
  "instructions": [
    "In order to effectively improve mobility, we need to understand the available methods and determine which are most appropriate—this considers not only the effectiveness, but also.",
    "The most effective stretch in the world is only effective if it can be and is done by the athlete with adequate frequency and regularity.",
    "It is unnecessary to identify the actual muscles in need of stretching; attempts at naming such muscles are typically inaccurate and incomplete anyway.",
    "There are approximately 640 skeletal muscles in the human body—it’s extremely uncommon to find a coach or athlete who can name more than 10% of them, and even less common for.",
    "Additionally, the mobility of a joint involves more than just the extensibility of the muscles that control it; consequently, joint mobility is much easier to improve if it is."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Mobility Training Protocols",
  "paragraph_count": 5,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Mobility Training Protocols"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "In order to effectively improve mobility, we need to understand the available methods and determine which are most appropriate—this considers not only the effectiveness, but also the efficiency and accessibility. The most effective stretch in the world is only effective if it can be and is done by the athlete with.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.186000",
  "usage_context": [
    "mobility",
    "mobility_limitation",
    "position",
    "recovery",
    "warmup_or_technique_primer"
  ],
  "version": "v1.0.0"
}
```

### 7. Static Stretching

```json
{
  "id": "ow_mobility_principle_083_008_static_stretching",
  "body_regions": [
    "ankle",
    "hamstring",
    "hip",
    "lat",
    "quad",
    "shoulder",
    "wrist"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "Static-Passive Stretching The most common type of mobility training is static-passive stretching—entering a stretched position and maintaining it for a given period of time, using.",
    "For example, leaning forward over an extended leg to stretch the hamstrings, using gravity and/or pulling against the leg with the hands to pull the muscles into a stretched.",
    "That is, aggressive static stretching should be employed to bring an athlete’s mobility up to optimal as quickly as possible, but once that optimal mobility has been achieved,.",
    "This practice will be limited to athletes with extreme immobility that prevents their ability to achieve necessary positions within a safe range.",
    "... 2 more"
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "ankle_pain",
    "high_fatigue",
    "hip_pain",
    "knee_pain",
    "shoulder_pain",
    "wrist_pain"
  ],
  "created_at": "2026-06-11T08:04:25.187000",
  "expert_validation_status": "pending",
  "instructions": [
    "Static-Passive Stretching The most common type of mobility training is static-passive stretching—entering a stretched position and maintaining it for a given period of time, using.",
    "For example, leaning forward over an extended leg to stretch the hamstrings, using gravity and/or pulling against the leg with the hands to pull the muscles into a stretched.",
    "Static stretching offers the most potential for dramatic increases in mobility, and is the easiest, most accessible method, but should be primarily considered a remediation tool.",
    "That is, aggressive static stretching should be employed to bring an athlete’s mobility up to optimal as quickly as possible, but once that optimal mobility has been achieved,.",
    "Research has demonstrated that static stretching may temporarily disrupt nerve function, resulting in diminished force production capacity and delayed reaction to proprioceptive."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Static Stretching",
  "paragraph_count": 14,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Static Stretching"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "Static-Passive Stretching The most common type of mobility training is static-passive stretching—entering a stretched position and maintaining it for a given period of time, using anything but the antagonists of the stretched muscles to achieve and hold the position. For example, leaning forward over an extended leg.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.187000",
  "usage_context": [
    "advanced_or_heavy_training",
    "bracing",
    "clean",
    "competition",
    "fatigue",
    "... 17 more"
  ],
  "version": "v1.0.0"
}
```

### 8. Dynamic Stretching

```json
{
  "id": "ow_mobility_principle_083_009_dynamic_stretching",
  "body_regions": [
    "lat",
    "shoulder"
  ],
  "category": "mobility_principles",
  "coaching_cues": [
    "Additional dynamic mobility work serves more as a bridge between inactivity and activity in the context of a warm-up or to ensure more balanced mobility for athletic specialists.",
    "Lifting Interestingly enough, working on the actual exercises or positions we’re trying to improve—performing the lifts themselves—is itself effective mobility training."
  ],
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "contraindications": [
    "high_fatigue",
    "low_back_pain"
  ],
  "created_at": "2026-06-11T08:04:25.188000",
  "expert_validation_status": "pending",
  "instructions": [
    "Dynamic Range of Motion Drills (DROMs) The type of stretches that will remain an indefinitely valuable tool irrespective of the athlete’s present level of mobility are dynamic.",
    "These are drills like those discussed in the Warming Up chapter of the book.",
    "Training itself may be considered a form of dynamic mobility work because the movements—assuming they’re being performed correctly through the full range of motion—will preserve.",
    "Additional dynamic mobility work serves more as a bridge between inactivity and activity in the context of a warm-up or to ensure more balanced mobility for athletic specialists.",
    "DROMs upon rising in the morning can help improve mobility throughout the day by essentially helping to neurologically reset muscle length that diminishes due to the limited."
  ],
  "knowledge_type": "mobility_principle",
  "name": "Dynamic Stretching",
  "paragraph_count": 4,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
      "section_title": "Introduction to Mobility & Flexibility",
      "epub_file": "OEBPS/text00082.html",
      "heading": "Dynamic Stretching"
    }
  ],
  "source_section_id": "ow_section_083_introduction_to_mobility_and_flexibility",
  "summary": "Dynamic Range of Motion Drills (DROMs) The type of stretches that will remain an indefinitely valuable tool irrespective of the athlete’s present level of mobility are dynamic range of motion drills (DROMs). These are drills like those discussed in the Warming Up chapter of the book.",
  "topics": [
    "mobility"
  ],
  "updated_at": "2026-06-11T08:04:25.188000",
  "usage_context": [
    "balance",
    "fatigue",
    "mobility",
    "mobility_limitation",
    "position",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

## `nutrition_principles` Samples

Showing `8` of `27` documents.

### 1. Quantity

```json
{
  "id": "ow_nutrition_nutrition_079_001_quantity",
  "action_guidance": [
    "It refers to the total amount of food being eaten in a given period of time, measured in calories, or more accurately, kilocalories (kcal)."
  ],
  "category": "nutrition",
  "content_hash": "14a8bc0317bb2bd044c15844703549399bec69ffa004d69b108f62dee78232e0",
  "created_at": "2026-06-11T08:04:25.158000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 1,
  "principle_text": "Quantity is the simplest value to understand. It refers to the total amount of food being eaten in a given period of time, measured in calories, or more accurately, kilocalories (kcal).",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Quantity"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "Quantity is the simplest value to understand. It refers to the total amount of food being eaten in a given period of time, measured in calories, or more accurately, kilocalories (kcal).",
  "title": "Quantity",
  "topics": [
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:25.158000",
  "usage_context": [
    "recovery"
  ],
  "version": "v1.0.0"
}
```

### 2. Quality

```json
{
  "id": "ow_nutrition_nutrition_079_002_quality",
  "action_guidance": [
    "This leaves meat, fish, eggs, vegetables, fruit, tubers, nuts and seeds, certain oils, and possibly certain dairy products as the types of foods that will ideally comprise the.",
    "A discussion of the depth required to fully explain the science behind this perspective is better left for more appropriate channels and those with greater expertise on the.",
    "To a great extent, food quality will also support athletic performance, but as health and performance diverge at times, so too will this relationship change occasionally to some.",
    "For example, a large serving of carbohydrates at a certain time (such as post-workout to replenish glycogen stores and aid in the recovery process) is far easier to achieve (and."
  ],
  "category": "nutrition",
  "content_hash": "686f7b0e8730da93337fb5fb19293896de14e077c3bd360b54a7249b10a4aee8",
  "contraindications": [
    "high_fatigue",
    "hip_pain"
  ],
  "created_at": "2026-06-11T08:04:25.159000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 3,
  "principle_text": "Food quality is a more nebulous value than quantity, with widespread and occasionally vehement contention existing. The guiding principle in food quality is remarkably simple: natural foods are generally superior in terms of their support of basic health.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Quality"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "Food quality is a more nebulous value than quantity, with widespread and occasionally vehement contention existing. The guiding principle in food quality is remarkably simple: natural foods are generally superior in terms of their support of basic health.",
  "title": "Quality",
  "topics": [
    "fatigue",
    "nutrition",
    "position",
    "recovery",
    "safety"
  ],
  "updated_at": "2026-06-11T08:04:25.159000",
  "usage_context": [
    "fatigue",
    "nutrition",
    "pain_or_injury_caution",
    "position",
    "recovery",
    "... 1 more"
  ],
  "version": "v1.0.0"
}
```

### 3. Macronutrient Composition

```json
{
  "id": "ow_nutrition_nutrition_079_003_macronutrient_composition",
  "action_guidance": [
    "The final fundamental element of nutrition is macronutrient composition: the relative quantities of protein, fat and carbohydrate that produce the total caloric intake.",
    "Protein should be considered the first priority in terms of macronutrients, particularly for strength athletes.",
    "Recommendations for protein intake vary from extremely minimal to quite epic.",
    "The recommended baseline for protein intake is 1 gram per pound (or approximately 2 grams per kilogram) of bodyweight (Zatsiorksy 1995).",
    "The quality of protein varies with its source.",
    "... 1 more"
  ],
  "category": "nutrition",
  "content_hash": "a387cb0f90286c03fdb99b99ba881fbe8993b6756604a45f96f3c24330c29fa1",
  "contraindications": [
    "hip_pain"
  ],
  "created_at": "2026-06-11T08:04:25.161000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 11,
  "principle_text": "The final fundamental element of nutrition is macronutrient composition: the relative quantities of protein, fat and carbohydrate that produce the total caloric intake. With the total quantity acting as our gross adjustment tool, macronutrient composition.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Macronutrient Composition"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "The final fundamental element of nutrition is macronutrient composition: the relative quantities of protein, fat and carbohydrate that produce the total caloric intake. With the total quantity acting as our gross adjustment tool, macronutrient composition provides us a tool for generally more minor but potentially.",
  "title": "Macronutrient Composition",
  "topics": [
    "balance",
    "loading",
    "nutrition",
    "position",
    "safety",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:25.161000",
  "usage_context": [
    "balance",
    "loading",
    "nutrition",
    "pain_or_injury_caution",
    "position",
    "... 3 more"
  ],
  "version": "v1.0.0"
}
```

### 4. Macronutrient Timing

```json
{
  "id": "ow_nutrition_nutrition_079_004_macronutrient_timing",
  "action_guidance": [
    "Pre-Workout: The pre-workout period will most often involve nothing more than the athlete’s normal eating habits—a balanced meal of protein, fat and carbohydrate.",
    "Timing of the last meal before training will vary among athletes depending on what the meal is comprised of and how the athlete tolerates such foods with training, but typically.",
    "For athletes attempting to gain weight, 20-40 grams of easily-digested protein (supplemental whey protein) 10-20 minutes prior to training may create a more anabolic environment.",
    "Instead of or in addition to this, athletes may find similar results from a high dose of a branched-chain amino acid supplement, although this will often create GI discomfort.",
    "Pre-workout energy supplements are also used commonly.",
    "... 1 more"
  ],
  "category": "nutrition",
  "content_hash": "062a3bbf53ed59b71e4d76213a3e23381ebbdfc439251260f3081a38c8e8636f",
  "created_at": "2026-06-11T08:04:25.162000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 10,
  "principle_text": "The timing of macronutrient consumption will have the least significant effect on performance, body composition and health relative to quantity, quality and macronutrient composition, but certain practices around training can be helpful. As with nearly all.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Macronutrient Timing"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "The timing of macronutrient consumption will have the least significant effect on performance, body composition and health relative to quantity, quality and macronutrient composition, but certain practices around training can be helpful. As with nearly all subjects in the realm of nutrition, much of the more detailed.",
  "title": "Macronutrient Timing",
  "topics": [
    "balance",
    "loading",
    "nutrition",
    "position"
  ],
  "updated_at": "2026-06-11T08:04:25.162000",
  "usage_context": [
    "advanced_or_heavy_training",
    "balance",
    "loading",
    "nutrition",
    "position",
    "... 2 more"
  ],
  "version": "v1.0.0"
}
```

### 5. Planning Nutrition

```json
{
  "id": "ow_nutrition_nutrition_079_005_planning_nutrition",
  "action_guidance": [
    "To assemble this into practical application, first we need to know that protein and carbohydrate provide approximately 4 kcals per gram and fat 9 kcals.",
    "To do this, we can use any number of formulas, none of which are ever remarkably accurate, or we can use a food journal to track food consumption and bodyweight for at least a.",
    "This average will be the starting point for daily calorie consumption (This assumes bodyweight is presently static—weight loss, gain, and maintenance are covered in the next.",
    "Since we’ve made protein the first priority and defined a clear quantitative guide for its consumption, we can determine the baseline daily protein requirements of the athlete: 1.",
    "So with an 85kg athlete, we would end up with a starting point of 187 grams of protein per day (748 kcal).",
    "... 1 more"
  ],
  "category": "nutrition",
  "content_hash": "9dd9f565e804782b2cc8707309d2d8a1abc2dc4e37fc73f4aa9939241b84def9",
  "contraindications": [
    "high_fatigue",
    "knee_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:25.164000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 15,
  "principle_text": "To assemble this into practical application, first we need to know that protein and carbohydrate provide approximately 4 kcals per gram and fat 9 kcals. Next we need to determine the athlete’s approximate daily caloric needs.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Planning Nutrition"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "To assemble this into practical application, first we need to know that protein and carbohydrate provide approximately 4 kcals per gram and fat 9 kcals. Next we need to determine the athlete’s approximate daily caloric needs.",
  "title": "Planning Nutrition",
  "topics": [
    "balance",
    "fatigue",
    "loading",
    "nutrition",
    "position",
    "receiving_position",
    "recovery"
  ],
  "updated_at": "2026-06-11T08:04:25.164000",
  "usage_context": [
    "balance",
    "fatigue",
    "loading",
    "nutrition",
    "position",
    "... 4 more"
  ],
  "version": "v1.0.0"
}
```

### 6. Water Intake

```json
{
  "id": "ow_nutrition_nutrition_079_006_water_intake",
  "action_guidance": [
    "A reasonable starting point is: &#9; Bodyweight (kg) X 0.026 = L/day or Bodyweight (lbs) X 0.4 = oz/day For our 85 kg (187 lb) athlete, we would end up with about 2.2 L (75 oz).",
    "This is a baseline intake and doesn’t take into account water loss during physical activity.",
    "Before, during and after any activity, water should be consumed according to the intensity and duration of the activity and obvious loss through sweat.",
    "For more accurate re-hydration, replace every kilogram of bodyweight lost during activity with 1 liter of water (or every pound of bodyweight with 16 ounces of water)."
  ],
  "category": "nutrition",
  "content_hash": "4e416a47c4d2b96a461674fae49e8d271fe6b29cac099cc5d6cb309f9dc062f9",
  "created_at": "2026-06-11T08:04:25.164000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 6,
  "principle_text": "There should be no need to make a case for the importance of adequate hydration here—make it happen. Intake recommendations vary dramatically, and recently some have begun to lean toward lower quantities.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_079_introduction_to_nutrition",
      "section_title": "Introduction to Nutrition",
      "epub_file": "OEBPS/text00078.html",
      "heading": "Water Intake"
    }
  ],
  "source_section_id": "ow_section_079_introduction_to_nutrition",
  "summary": "There should be no need to make a case for the importance of adequate hydration here—make it happen. Intake recommendations vary dramatically, and recently some have begun to lean toward lower quantities.",
  "title": "Water Intake",
  "topics": [
    "loading",
    "nutrition"
  ],
  "updated_at": "2026-06-11T08:04:25.164000",
  "usage_context": [
    "loading",
    "nutrition",
    "program_design"
  ],
  "version": "v1.0.0"
}
```

### 7. Maintaining Weight

```json
{
  "id": "ow_nutrition_bodyweight_080_001_maintaining_weight",
  "action_guidance": [
    "Bodyweight maintenance can range from requiring no work at all to being extremely troublesome.",
    "The maintenance of bodyweight is simply a matter of balancing energy consumed as food and energy expended through metabolism.",
    "For those whose bodyweights fluctuate continually, the goal is developing consistency in eating and activity—to establish the body’s set point at the desired weight and body.",
    "A detailed food journal should be kept for at least a week and ideally two, describing accurate quantities of all food and any beverages, including water—daily weight fluctuations.",
    "In this journal, records of bodyweight can be kept as well.",
    "... 1 more"
  ],
  "category": "bodyweight",
  "content_hash": "628467e32e09139b7790d0a9f67fc098904cf8107b0ebf1cd2a42e59c66814fb",
  "created_at": "2026-06-11T08:04:25.168000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 6,
  "principle_text": "Bodyweight maintenance can range from requiring no work at all to being extremely troublesome. For those who maintain their weights without any thought, the only remaining issue is that of body composition.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_080_bodyweight",
      "section_title": "Bodyweight",
      "epub_file": "OEBPS/text00079.html",
      "heading": "Maintaining Weight"
    }
  ],
  "source_section_id": "ow_section_080_bodyweight",
  "summary": "Bodyweight maintenance can range from requiring no work at all to being extremely troublesome. For those who maintain their weights without any thought, the only remaining issue is that of body composition.",
  "title": "Maintaining Weight",
  "topics": [
    "competition",
    "nutrition",
    "position",
    "program_design",
    "receiving_position"
  ],
  "updated_at": "2026-06-11T08:04:25.168000",
  "usage_context": [
    "competition",
    "nutrition",
    "position",
    "program_design",
    "receiving_position",
    "... 2 more"
  ],
  "version": "v1.0.0"
}
```

### 8. Losing Weight

```json
{
  "id": "ow_nutrition_bodyweight_080_002_losing_weight",
  "action_guidance": [
    "Losing weight is achieved by creating a calorie deficit while supporting healthy metabolic activity, largely through the management of relevant hormone levels, intestinal health.",
    "Sudden large calorie deficits will produce systemic fatigue and decreases in strength and stamina, will be psychologically taxing, and will typically result in less weight loss.",
    "From here, we’ll drop this figure and consume the calculated number of calories consistently for 1-2 weeks, evaluate the progress, and readjust if necessary.",
    "First, is bodyweight constant, increasing or decreasing at present?",
    "If bodyweight is constant and we have no time constraints, we may drop the calories by 10-15% or so for 1-2 weeks and monitor weight and performance.",
    "... 1 more"
  ],
  "category": "bodyweight",
  "content_hash": "77d6084645b28628cc3899e82b3aceb82ad6ee70e842c414813ac4c20c143db3",
  "contraindications": [
    "high_fatigue"
  ],
  "created_at": "2026-06-11T08:04:25.168000",
  "expert_validation_status": "pending",
  "knowledge_type": "nutrition_principle",
  "paragraph_count": 9,
  "principle_text": "Losing weight is achieved by creating a calorie deficit while supporting healthy metabolic activity, largely through the management of relevant hormone levels, intestinal health and systemic inflammation. This is done primarily through incremental reductions.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_080_bodyweight",
      "section_title": "Bodyweight",
      "epub_file": "OEBPS/text00079.html",
      "heading": "Losing Weight"
    }
  ],
  "source_section_id": "ow_section_080_bodyweight",
  "summary": "Losing weight is achieved by creating a calorie deficit while supporting healthy metabolic activity, largely through the management of relevant hormone levels, intestinal health and systemic inflammation. This is done primarily through incremental reductions in calorie intake, improvement of food quality, and.",
  "title": "Losing Weight",
  "topics": [
    "competition",
    "fatigue",
    "nutrition",
    "safety",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:25.168000",
  "usage_context": [
    "competition",
    "fatigue",
    "nutrition",
    "recovery",
    "safety",
    "... 1 more"
  ],
  "version": "v1.0.0"
}
```

## `recovery_rules` Samples

Showing `6` of `6` documents.

### 1. Restorative Modalities

```json
{
  "id": "ow_recovery_restoration_recovery_053_001_restorative_modalities",
  "category": "restoration_recovery",
  "content_hash": "371687d9f7370bf5d79a67b0c52e318f6aa490df5284b999a236923ade19cff3",
  "contraindications": [
    "high_fatigue",
    "hip_pain",
    "low_back_pain"
  ],
  "created_at": "2026-06-11T08:04:25.147000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 17,
  "recovery_methods": [
    "There are a number of active restorative modalities that need to be employed by lifters to maximize restoration and training capacity.",
    "Generally, more restorative work should be performed on rest days than on training days, and in the case of multiple daily training sessions, less intense modalities employed.",
    "Less intense modalities include stretching, napping, swimming and local cryotherapy; more intense modalities include massage, hydrotherapy (including cold plunge and hot tub), and.",
    "Contrast Hydrotherapy This is arguably the most effective restorative modality available.",
    "Clinical research is somewhat ambiguous, and although some studies have shown significant improvements in recovery of strength and reduction of DOMS, results in the real world.",
    "... 1 more"
  ],
  "rule_text": "There are a number of active restorative modalities that need to be employed by lifters to maximize restoration and training capacity. Accessibility will vary among lifters, but efforts will need to be made to do as much as is possible financially and with.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_053_restoration_and_recovery",
      "section_title": "Restoration & Recovery",
      "epub_file": "OEBPS/text00052.html",
      "heading": "Restorative Modalities"
    }
  ],
  "source_section_id": "ow_section_053_restoration_and_recovery",
  "summary": "There are a number of active restorative modalities that need to be employed by lifters to maximize restoration and training capacity. Accessibility will vary among lifters, but efforts will need to be made to do as much as is possible financially and with the time available.",
  "title": "Restorative Modalities",
  "topics": [
    "competition",
    "fatigue",
    "loading",
    "mobility",
    "nutrition",
    "press",
    "pull",
    "recovery",
    "... 3 more"
  ],
  "updated_at": "2026-06-11T08:04:25.147000",
  "usage_context": [
    "competition",
    "fatigue",
    "loading",
    "mobility",
    "mobility_limitation",
    "... 9 more"
  ],
  "version": "v1.0.0"
}
```

### 2. Monitoring Recovery

```json
{
  "id": "ow_recovery_restoration_recovery_053_002_monitoring_recovery",
  "category": "restoration_recovery",
  "content_hash": "cf13ea0e874b36530e20cdc19c87921dcbecd91aa0d1e22bb0a0fa498dce251e",
  "created_at": "2026-06-11T08:04:25.149000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 11,
  "recovery_methods": [
    "With such an emphasis on recovery and the need to plan training around it, the question of how to monitor recovery status in some fashion naturally arises.",
    "The classic monitoring of resting heart rate and blood pressure are simple and convenient methods, but appear to have less value for the strength athlete than the endurance.",
    "That is, negative deviations from the athlete’s baseline jump or grip strength appear to most accurately indicate under-recovery.",
    "In any case, objective measurements, while being interesting, are typically unnecessary.",
    "Further, despite any level of accurate correlation between test results and the state of recovery, the actual implementation of the tests creates opportunity for inaccuracy.",
    "... 1 more"
  ],
  "rule_text": "With such an emphasis on recovery and the need to plan training around it, the question of how to monitor recovery status in some fashion naturally arises. The classic monitoring of resting heart rate and blood pressure are simple and convenient methods, but.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_053_restoration_and_recovery",
      "section_title": "Restoration & Recovery",
      "epub_file": "OEBPS/text00052.html",
      "heading": "Monitoring Recovery"
    }
  ],
  "source_section_id": "ow_section_053_restoration_and_recovery",
  "summary": "With such an emphasis on recovery and the need to plan training around it, the question of how to monitor recovery status in some fashion naturally arises. The classic monitoring of resting heart rate and blood pressure are simple and convenient methods, but appear to have less value for the strength athlete than the.",
  "title": "Monitoring Recovery",
  "topics": [
    "balance",
    "fatigue",
    "jump_training",
    "loading",
    "nutrition",
    "position",
    "press",
    "recovery",
    "... 1 more"
  ],
  "updated_at": "2026-06-11T08:04:25.149000",
  "usage_context": [
    "balance",
    "fatigue",
    "jump_training",
    "loading",
    "nutrition",
    "... 5 more"
  ],
  "version": "v1.0.0"
}
```

### 3. Hand Care

```json
{
  "id": "ow_recovery_restoration_recovery_053_003_hand_care",
  "category": "restoration_recovery",
  "content_hash": "5915771b7c333986c25116707c0c4fc540dce0327bfbef1cafb22494945db01d",
  "contraindications": [
    "high_fatigue",
    "low_back_pain",
    "wrist_pain"
  ],
  "created_at": "2026-06-11T08:04:25.150000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 12,
  "recovery_methods": [
    "As the connection of the body to the bar, the hands need to be taken care of well to prevent the disruption of training and competition.",
    "The greater and more consistent prevention efforts are, the less the need for correction will be, and the more consistent training can remain.",
    "Small squares of sandpaper should be kept in the athlete’s training bag for use during training if necessary.",
    "A simple way to make sure it’s consistent is creating a habit of sanding the hands before each training session.",
    "If a callus is large enough or is beginning to separate from the hand, fingernail clippers can be used to trim any loose skin away, and the edge then sanded down to be smooth with.",
    "... 1 more"
  ],
  "rule_text": "Being covered in chalk and rubbing against knurled metal for hours every week will not exactly prepare hands for a modeling career—calluses will be commonplace, and blisters and tears will occur occasionally, or more often with inadequate preventative effort..",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_053_restoration_and_recovery",
      "section_title": "Restoration & Recovery",
      "epub_file": "OEBPS/text00052.html",
      "heading": "Hand Care"
    }
  ],
  "source_section_id": "ow_section_053_restoration_and_recovery",
  "summary": "Being covered in chalk and rubbing against knurled metal for hours every week will not exactly prepare hands for a modeling career—calluses will be commonplace, and blisters and tears will occur occasionally, or more often with inadequate preventative effort. As the connection of the body to the bar, the hands need to.",
  "title": "Hand Care",
  "topics": [
    "clean",
    "competition",
    "fatigue",
    "safety"
  ],
  "updated_at": "2026-06-11T08:04:25.150000",
  "usage_context": [
    "clean",
    "competition",
    "fatigue",
    "pain_or_injury_caution",
    "recovery",
    "... 2 more"
  ],
  "version": "v1.0.0"
}
```

### 4. Injuries

```json
{
  "id": "ow_recovery_restoration_recovery_053_004_injuries",
  "category": "restoration_recovery",
  "content_hash": "a1b294770c191ce2e484a8bbff054193aa9abf21df4f0db7853d981394d29f9d",
  "contraindications": [
    "high_fatigue",
    "low_back_pain"
  ],
  "created_at": "2026-06-11T08:04:25.151000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 5,
  "recovery_methods": [
    "Despite the generally unrecognized low incidence of injury in weightlifting competition, as with all sports and training modalities, injuries are inevitable, particularly as the.",
    "Most can be avoided through intelligent training, programming and restorative methods, but once an injury does occur, its treatment is critical for the athlete’s timely and full.",
    "Competitive athletes are accustomed to training with pain and discomfort and often pride themselves on their abnormally high tolerances.",
    "However admirable in general this may be, there is in fact a threshold after which continued training is no longer respectable, but simply stupid.",
    "The distinction between the type and degree of pain the athlete can train through and a legitimate injury that requires treatment and rest is critical.",
    "... 1 more"
  ],
  "rule_text": "Despite the generally unrecognized low incidence of injury in weightlifting competition, as with all sports and training modalities, injuries are inevitable, particularly as the level of competition increases. Most can be avoided through intelligent training,.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_053_restoration_and_recovery",
      "section_title": "Restoration & Recovery",
      "epub_file": "OEBPS/text00052.html",
      "heading": "Injuries"
    }
  ],
  "source_section_id": "ow_section_053_restoration_and_recovery",
  "summary": "Despite the generally unrecognized low incidence of injury in weightlifting competition, as with all sports and training modalities, injuries are inevitable, particularly as the level of competition increases. Most can be avoided through intelligent training, programming and restorative methods, but once an injury.",
  "title": "Injuries",
  "topics": [
    "competition",
    "fatigue",
    "program_design",
    "recovery",
    "safety"
  ],
  "updated_at": "2026-06-11T08:04:25.151000",
  "usage_context": [
    "advanced_or_heavy_training",
    "competition",
    "fatigue",
    "pain_or_injury_caution",
    "program_design",
    "... 2 more"
  ],
  "version": "v1.0.0"
}
```

### 5. SMR Protocol

```json
{
  "id": "ow_recovery_self_myofascial_release_085_001_smr_protocol",
  "category": "self_myofascial_release",
  "content_hash": "03d290016256f0a21db81630064ee02411e8afc5647c03a8dc57229b78882677",
  "contraindications": [
    "high_fatigue"
  ],
  "created_at": "2026-06-11T08:04:25.153000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 7,
  "recovery_methods": [
    "This aggressive and focused SMR should be performed after training along with, and preceding, any static stretching.",
    "It can and should also be performed on rest days along with any necessary static stretching, but like static stretching, is best preceded by a hot bath or shower, or at least some.",
    "As discussed in the Warming Up chapter, foam rolling with lighter passes and little or no aggressive focus work on specific points is an effective element of training preparation."
  ],
  "rule_text": "For most athletes, foam-rolling will be painful, occasionally excruciatingly so in certain locations. However, the pain produced by the practice will abate to some degree with regular performance, although it’s unlikely any weightlifter will ever achieve.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_085_self_myofascial_release",
      "section_title": "Self-Myofascial Release",
      "epub_file": "OEBPS/text00084.html",
      "heading": "SMR Protocol"
    }
  ],
  "source_section_id": "ow_section_085_self_myofascial_release",
  "summary": "For most athletes, foam-rolling will be painful, occasionally excruciatingly so in certain locations. However, the pain produced by the practice will abate to some degree with regular performance, although it’s unlikely any weightlifter will ever achieve complete clearance of painful areas.",
  "title": "SMR Protocol",
  "topics": [
    "fatigue",
    "first_pull",
    "mobility",
    "position",
    "press",
    "safety"
  ],
  "updated_at": "2026-06-11T08:04:25.153000",
  "usage_context": [
    "fatigue",
    "first_pull",
    "mobility",
    "mobility_limitation",
    "nutrition",
    "... 5 more"
  ],
  "version": "v1.0.0"
}
```

### 6. Thoracic Spine Mobility

```json
{
  "id": "ow_recovery_self_myofascial_release_085_002_thoracic_spine_mobility",
  "category": "self_myofascial_release",
  "content_hash": "b47f7749809d162b87a0ecb7cf659373ea87422977c1d3ac76eed0d880906333",
  "contraindications": [
    "low_back_pain",
    "shoulder_pain"
  ],
  "created_at": "2026-06-11T08:04:25.154000",
  "expert_validation_status": "pending",
  "knowledge_type": "recovery_rule",
  "paragraph_count": 3,
  "recovery_methods": [
    "Although not actually myofascial release, weightlifters will find foam-rolling helpful for improving thoracic spine mobility, both before and after training."
  ],
  "rule_text": "Although not actually myofascial release, weightlifters will find foam-rolling helpful for improving thoracic spine mobility, both before and after training. The upper back is often very immobile and locked into a limited range of motion with exaggerated.",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_085_self_myofascial_release",
      "section_title": "Self-Myofascial Release",
      "epub_file": "OEBPS/text00084.html",
      "heading": "Thoracic Spine Mobility"
    }
  ],
  "source_section_id": "ow_section_085_self_myofascial_release",
  "summary": "Although not actually myofascial release, weightlifters will find foam-rolling helpful for improving thoracic spine mobility, both before and after training. The upper back is often very immobile and locked into a limited range of motion with exaggerated kyphosis.",
  "title": "Thoracic Spine Mobility",
  "topics": [
    "clean",
    "jerk",
    "mobility",
    "overhead",
    "position",
    "receiving_position",
    "second_pull",
    "snatch"
  ],
  "updated_at": "2026-06-11T08:04:25.154000",
  "usage_context": [
    "clean",
    "jerk",
    "mobility",
    "mobility_limitation",
    "overhead",
    "... 4 more"
  ],
  "version": "v1.0.0"
}
```

## `glossary_terms` Samples

Showing `10` of `40` documents.

### 1. Absolute Intensity

```json
{
  "id": "ow_glossary_absolute_intensity",
  "content_hash": "b41444814395dda2878e768b68c0ca9dc958c0bbd7cbd1cd30e41fea908cd18e",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "An objective measure of the difficulty of a lift measured in terms of actual weight (e.g kilograms).",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Absolute Intensity"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Absolute Intensity",
  "topics": [
    "loading"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 2. Anthropometry

```json
{
  "id": "ow_glossary_anthropometry",
  "content_hash": "386a49aaf5920c0ba8ed04bac5410e49f29f0bb193cc8bfd675bf9737411509d",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "Also anthropometrics. The proportions of the human body. See brachiomorph, dolichomorph and mesomorph.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Anthropometry"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Anthropometry",
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 3. Bounce

```json
{
  "id": "ow_glossary_bounce",
  "content_hash": "be9dc405d7ccc6b914e94b16b80da0df6b3c2fce7f2df5b16b3aa7f2bca55eb7",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "The bounce is the use of the elastic rebound at the bottom of the squat or clean to recover from the bottom position more easily and with more speed. It is the combination of three elements: the literal bounce of the upper leg off the lower leg, the stretch-shortening reflex in the muscles of the legs and hips, and the elastic whip of the barbell. The bounce should generally be used in training with the clean and fro...",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Bounce"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Bounce",
  "topics": [
    "clean",
    "mobility",
    "position",
    "squat"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 4. Brachiomorph

```json
{
  "id": "ow_glossary_brachiomorph",
  "content_hash": "29c2bbc60f200d23ba8f9a0e5f7e105ee362fdb4df91d082e173e4c9961fb437",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "An athlete with a relatively long trunk and short limbs.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Brachiomorph"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Brachiomorph",
  "topics": [
    "bracing"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 5. Center of Gravity (COG)

```json
{
  "id": "ow_glossary_center_of_gravity_cog",
  "content_hash": "61f07bcba0882f08576c7cc595d15cb9bbfbcba2abc22011b3436eb8978f82ee",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "For the purposes of weightlifting, center of gravity may be used interchangeably with center of mass . They diverge only when gravity does not act uniformly on an object—in the context of weightlifting, they refer to the same point.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Center of Gravity (COG)"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Center of Gravity (COG)",
  "topics": [
    "balance"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 6. Center of Mass (COM)

```json
{
  "id": "ow_glossary_center_of_mass_com",
  "content_hash": "104998744546f1e6429084ed308b08266bdc90037832784654df9e5aef1f7456",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "The point around which an athlete’s total mass is equally distributed in all directions. An object will be balanced with the base of support vertically under the center of mass. For the purposes of weightlifting, center of mass may be used interchangeably with center of gravity .",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Center of Mass (COM)"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Center of Mass (COM)",
  "topics": [
    "balance"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 7. Center of Pressure (COP)

```json
{
  "id": "ow_glossary_center_of_pressure_cop",
  "content_hash": "f3d3f07e931cba559457e8fc182d92d359c36455f9f311a09ab3caed4326482c",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "The location of an object’s base of support at which the pressure of the object’s weight is centered.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Center of Pressure (COP)"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Center of Pressure (COP)",
  "topics": [
    "balance",
    "press"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 8. Complex

```json
{
  "id": "ow_glossary_complex",
  "content_hash": "00bdf88eca13e18e80bc9d08cbcd15d5a90176352092346662e1a8aab92735ef",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "A complex is the combination of two or more distinct exercises into a series. Complexes can be used for technical reasons or for training elements such as speed, explosiveness or strength.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Complex"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Complex",
  "topics": [
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 9. Concentric

```json
{
  "id": "ow_glossary_concentric",
  "content_hash": "695d36b5a0ca1f06c05c15dad9e3c8216c38feb14ba390e34da0caac3b5ec482",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "The concentric phase of a lift is that during which the acting muscles are contracting. As an example, the concentric phase of the squat is the phase of returning to a standing position from the bottom position.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Concentric"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Concentric",
  "topics": [
    "position",
    "recovery",
    "squat"
  ],
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

### 10. Consistent Minimum

```json
{
  "id": "ow_glossary_consistent_minimum",
  "content_hash": "f5e5e374d8ad43bbe47e841b5ecd7ad4b9742c3de4c4d9e51cf589bee6fdf313",
  "created_at": "2026-06-11T08:04:25.208000",
  "definition": "The minimum weight an athlete is capable of lifting in a given lift in a given period of time when making appropriately heavy or maximal attempts. This is a baseline of ability that measures preparedness.",
  "expert_validation_status": "pending",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_089_glossary",
      "section_title": "Glossary",
      "epub_file": "OEBPS/text00088.html",
      "heading": "Consistent Minimum"
    }
  ],
  "source_section_id": "ow_section_089_glossary",
  "term": "Consistent Minimum",
  "updated_at": "2026-06-11T08:04:25.208000",
  "version": "v1.0.0"
}
```

## `training_principles` Samples

Showing `10` of `56` documents.

### 1. Understanding the Lifts

```json
{
  "id": "ow_principle_foundations_009",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "foundations",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_009_understanding_the_lifts",
      "section_title": "Understanding the Lifts",
      "epub_file": "OEBPS/text00008.html"
    }
  ],
  "source_section_id": "ow_section_009_understanding_the_lifts",
  "title": "Understanding the Lifts",
  "topics": [
    "clean",
    "jerk",
    "jump_training",
    "overhead",
    "power",
    "press",
    "program_design",
    "pull",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 2. Learning & Teaching the Lifts

```json
{
  "id": "ow_principle_coaching_010",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "coaching",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_010_learning_and_teaching_the_lifts",
      "section_title": "Learning & Teaching the Lifts",
      "epub_file": "OEBPS/text00009.html"
    }
  ],
  "source_section_id": "ow_section_010_learning_and_teaching_the_lifts",
  "title": "Learning & Teaching the Lifts",
  "topics": [
    "assessment",
    "clean",
    "competition",
    "error_correction",
    "jerk",
    "masters",
    "mobility",
    "overhead",
    "... 9 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 3. Individual Variation

```json
{
  "id": "ow_principle_individualization_011",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "individualization",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_011_individual_variation",
      "section_title": "Individual Variation",
      "epub_file": "OEBPS/text00010.html"
    }
  ],
  "source_section_id": "ow_section_011_individual_variation",
  "title": "Individual Variation",
  "topics": [
    "clean",
    "competition",
    "jerk",
    "mobility",
    "overhead",
    "press",
    "program_design",
    "pull",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 4. Facility & Equipment

```json
{
  "id": "ow_principle_facility_equipment_012",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "facility_equipment",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_012_facility_and_equipment",
      "section_title": "Facility & Equipment",
      "epub_file": "OEBPS/text00011.html"
    }
  ],
  "source_section_id": "ow_section_012_facility_and_equipment",
  "title": "Facility & Equipment",
  "topics": [
    "clean",
    "competition",
    "deadlift",
    "jerk",
    "jump_training",
    "mobility",
    "overhead",
    "power",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 5. Warming Up

```json
{
  "id": "ow_principle_warmup_013",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "warmup",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_013_warming_up",
      "section_title": "Warming Up",
      "epub_file": "OEBPS/text00012.html"
    }
  ],
  "source_section_id": "ow_section_013_warming_up",
  "title": "Warming Up",
  "topics": [
    "clean",
    "competition",
    "jerk",
    "jump_training",
    "mobility",
    "overhead",
    "power",
    "press",
    "... 5 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 6. Breathing & Trunk Rigidity

```json
{
  "id": "ow_principle_bracing_014",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "bracing",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_014_breathing_and_trunk_rigidity",
      "section_title": "Breathing & Trunk Rigidity",
      "epub_file": "OEBPS/text00013.html"
    }
  ],
  "source_section_id": "ow_section_014_breathing_and_trunk_rigidity",
  "title": "Breathing & Trunk Rigidity",
  "topics": [
    "clean",
    "jerk",
    "press",
    "pull",
    "recovery",
    "snatch",
    "squat"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 7. The Squat

```json
{
  "id": "ow_principle_squat_015",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "squat",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_015_the_squat",
      "section_title": "The Squat",
      "epub_file": "OEBPS/text00014.html"
    }
  ],
  "source_section_id": "ow_section_015_the_squat",
  "title": "The Squat",
  "topics": [
    "clean",
    "error_correction",
    "jerk",
    "jump_training",
    "mobility",
    "overhead",
    "power",
    "press",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 8. Starting Position Principles

```json
{
  "id": "ow_principle_start_position_019",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "start_position",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_019_starting_position_principles",
      "section_title": "Starting Position Principles",
      "epub_file": "OEBPS/text00018.html"
    }
  ],
  "source_section_id": "ow_section_019_starting_position_principles",
  "title": "Starting Position Principles",
  "topics": [
    "clean",
    "competition",
    "error_correction",
    "mobility",
    "power",
    "press",
    "pull",
    "snatch",
    "... 3 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 9. Introduction to the Snatch

```json
{
  "id": "ow_principle_snatch_021",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "snatch",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_021_introduction_to_the_snatch",
      "section_title": "Introduction to the Snatch",
      "epub_file": "OEBPS/text00020.html"
    }
  ],
  "source_section_id": "ow_section_021_introduction_to_the_snatch",
  "title": "Introduction to the Snatch",
  "topics": [
    "clean",
    "jerk",
    "overhead",
    "power",
    "pull",
    "snatch",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

### 10. Learning the Snatch

```json
{
  "id": "ow_principle_snatch_023",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "snatch",
  "expert_validation_status": "pending",
  "knowledge_type": "section_level_training_topic",
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "source_refs": [
    {
      "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
      "section_id": "ow_section_023_learning_the_snatch",
      "section_title": "Learning the Snatch",
      "epub_file": "OEBPS/text00022.html"
    }
  ],
  "source_section_id": "ow_section_023_learning_the_snatch",
  "title": "Learning the Snatch",
  "topics": [
    "clean",
    "competition",
    "jerk",
    "jump_training",
    "masters",
    "mobility",
    "overhead",
    "power",
    "... 9 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "usage": "Use this source section for deeper extraction of coaching rules, progressions, contraindications, and session construction.",
  "version": "v1.0.0"
}
```

## `source_sections` Samples

Showing `10` of `91` documents.

### 1. text00000.html

```json
{
  "id": "ow_section_001_text00000_html",
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00000.html",
  "paragraph_count": 0,
  "section_order": 1,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "text00000.html",
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 0
}
```

### 2. Olympic Weightlifting

```json
{
  "id": "ow_section_002_olympic_weightlifting",
  "content_hash": "646480298b4a5c21b53c0f909a691d4d2f993be1f74d0c077608fad32dcae0cf",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00001.html",
  "paragraph_count": 5,
  "section_order": 2,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Olympic Weightlifting",
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 15
}
```

### 3. © 2016 Greg Everett

```json
{
  "id": "ow_section_003_2016_greg_everett",
  "content_hash": "bb9f5d74b50fcb98ed052d724cb8fdc1a1be974840ef2c6d4b467ec4ae106426",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00002.html",
  "paragraph_count": 7,
  "section_order": 3,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "© 2016 Greg Everett",
  "topics": [
    "nutrition",
    "technique"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 171
}
```

### 4. Contents

```json
{
  "id": "ow_section_004_contents",
  "content_hash": "9e07e33ea73ec40d8fc3213393873f90f194ebdbbdc4c7658667d2761b9b08f9",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00003.html",
  "paragraph_count": 57,
  "section_order": 4,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Contents",
  "topics": [
    "accessory_work",
    "assessment",
    "clean",
    "competition",
    "error_correction",
    "jerk",
    "jump_training",
    "mobility",
    "... 9 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 155
}
```

### 5. Acknowledgments

```json
{
  "id": "ow_section_005_acknowledgments",
  "content_hash": "f01f90adf98491b2a47bf2e228e1f105c6b9ca8b321c2d3771f6be14b976d8fc",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00004.html",
  "paragraph_count": 6,
  "section_order": 5,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Acknowledgments",
  "topics": [
    "competition",
    "strength"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 322
}
```

### 6. Introduction to the Third Edition

```json
{
  "id": "ow_section_006_introduction_to_the_third_edition",
  "content_hash": "5f10bf478d3d9476e7470c96d092ee884f8e2f59ef58ee06460f146e5967dddf",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00005.html",
  "paragraph_count": 5,
  "section_order": 6,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Introduction to the Third Edition",
  "topics": [
    "press",
    "program_design"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 316
}
```

### 7. How to Use This Book

```json
{
  "id": "ow_section_007_how_to_use_this_book",
  "content_hash": "926fddf4b0ee531486cf81a314a0ab23966d402c53c8c772feece43bb9ecfa82",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00006.html",
  "paragraph_count": 8,
  "section_order": 7,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "How to Use This Book",
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 471
}
```

### 8. Foundations

```json
{
  "id": "ow_section_008_foundations",
  "content_hash": "1157606ee47522a84d4f159b91baed74838b3859982e8a6655211031a82bca9b",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "book_structure",
  "epub_file": "OEBPS/text00007.html",
  "paragraph_count": 1,
  "section_order": 8,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Foundations",
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 1
}
```

### 9. Understanding the Lifts

```json
{
  "id": "ow_section_009_understanding_the_lifts",
  "content_hash": "c093ab6ec0a01da5b52a3e9e27bed776d125e7065e81223c36cf5fe450adbde0",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "foundations",
  "epub_file": "OEBPS/text00008.html",
  "paragraph_count": 72,
  "section_order": 9,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Understanding the Lifts",
  "topics": [
    "clean",
    "jerk",
    "jump_training",
    "overhead",
    "power",
    "press",
    "program_design",
    "pull",
    "... 7 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 4021
}
```

### 10. Learning & Teaching the Lifts

```json
{
  "id": "ow_section_010_learning_and_teaching_the_lifts",
  "content_hash": "8efa9c6af58fbc4378bb1707485a64e625d219facc118bf60329ad8ab2864027",
  "created_at": "2026-06-11T08:04:24.508000",
  "domain": "coaching",
  "epub_file": "OEBPS/text00009.html",
  "paragraph_count": 52,
  "section_order": 10,
  "source_book_id": "olympic_weightlifting_complete_guide_3rd_ed",
  "title": "Learning & Teaching the Lifts",
  "topics": [
    "assessment",
    "clean",
    "competition",
    "error_correction",
    "jerk",
    "masters",
    "mobility",
    "overhead",
    "... 9 more"
  ],
  "updated_at": "2026-06-11T08:04:24.508000",
  "word_count": 4648
}
```
