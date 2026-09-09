export const RUNNING_EVENTS = [
  { code: 'run_walk', label: 'Run / walk' }, { code: '100m', label: '100 m' },
  { code: '200m', label: '200 m' }, { code: '400m', label: '400 m' },
  { code: '800m', label: '800 m' }, { code: '1500m', label: '1500 m' },
  { code: 'mile', label: 'Mile' }, { code: '5k', label: '5K' },
  { code: '10k', label: '10K' }, { code: 'half_marathon', label: 'Half marathon' },
  { code: 'marathon', label: 'Marathon' }, { code: 'trail', label: 'Trail' },
] as const;

export const RUNNER_GOALS = [
  { code: 'target_race', label: 'Prepare for a race', description: 'Train for a target event, date, and optional finish time.', icon: 'flag-outline' },
  { code: 'start_running', label: 'Build consistency', description: 'Start, restart, or make running a regular habit.', icon: 'calendar-outline' },
  { code: 'run_faster', label: 'Run faster', description: 'Improve speed, pace, and running economy.', icon: 'speedometer-outline' },
  { code: 'build_endurance', label: 'Run farther', description: 'Build endurance for longer, stronger runs.', icon: 'trending-up-outline' },
] as const;

export const distanceToMetres = (value: number, unit: 'km' | 'mi') => value * (unit === 'mi' ? 1609.344 : 1000);
