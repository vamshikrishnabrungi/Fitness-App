export const RUNNING_EVENTS = [
  { code: 'run_walk', label: 'Run / walk' }, { code: '100m', label: '100 m' },
  { code: '200m', label: '200 m' }, { code: '400m', label: '400 m' },
  { code: '800m', label: '800 m' }, { code: '1500m', label: '1500 m' },
  { code: 'mile', label: 'Mile' }, { code: '5k', label: '5K' },
  { code: '10k', label: '10K' }, { code: 'half_marathon', label: 'Half marathon' },
  { code: 'marathon', label: 'Marathon' }, { code: 'trail', label: 'Trail' },
  { code: 'ultra', label: 'Ultra' },
] as const;

export const RUNNER_GOALS = [
  { code: 'target_race', label: 'Prepare for a race', description: 'Build toward a target event, date, and optional finish time.' },
  { code: 'start_running', label: 'Start running', description: 'Build consistency safely from your current level.' },
  { code: 'run_faster', label: 'Run faster', description: 'Improve speed, pace, and running economy.' },
  { code: 'build_endurance', label: 'Build endurance', description: 'Run farther and recover better.' },
  { code: 'return_to_running', label: 'Return to running', description: 'Resume progressively after time away.' },
  { code: 'general_fitness', label: 'General fitness', description: 'Use running and strength to improve overall fitness.' },
] as const;

export const distanceToMetres = (value: number, unit: 'km' | 'mi') => value * (unit === 'mi' ? 1609.344 : 1000);
