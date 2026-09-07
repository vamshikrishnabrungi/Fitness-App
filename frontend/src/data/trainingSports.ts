export type SportScopeOption = {
  code: string;
  label: string;
  eventCode?: string;
  roleCode?: string;
  disciplineCode?: string;
  formatCode?: string;
};

export type TrainingSport = {
  code: string;
  label: string;
  scopeLabel: string;
  scopes: SportScopeOption[];
};

const options = (values: string[], field: 'eventCode' | 'roleCode' | 'formatCode'): SportScopeOption[] =>
  values.map(code => ({ code, label: code.replaceAll('_', ' '), [field]: code }));

export const TRAINING_SPORTS: TrainingSport[] = [
  { code: 'badminton', label: 'Badminton', scopeLabel: 'Format', scopes: options(['singles', 'doubles'], 'formatCode') },
  { code: 'basketball', label: 'Basketball', scopeLabel: 'Role', scopes: options(['guard', 'wing', 'big'], 'roleCode') },
  { code: 'boxing', label: 'Boxing', scopeLabel: 'Format', scopes: options(['amateur', 'professional'], 'formatCode') },
  { code: 'cricket', label: 'Cricket', scopeLabel: 'Role', scopes: options(['batter', 'pace_bowler', 'spin_bowler', 'wicketkeeper', 'all_rounder'], 'roleCode') },
  { code: 'cycling', label: 'Cycling', scopeLabel: 'Event', scopes: options(['fitness_endurance', 'road_endurance', 'sprint', 'time_trial'], 'eventCode') },
  { code: 'football', label: 'Football', scopeLabel: 'Role', scopes: options(['goalkeeper', 'central_defender', 'fullback_wingback', 'central_midfielder', 'winger', 'striker'], 'roleCode') },
  { code: 'mma', label: 'MMA', scopeLabel: 'Format', scopes: options(['three_round', 'five_round'], 'formatCode') },
  { code: 'running', label: 'Running', scopeLabel: 'Event', scopes: options(['100m', '200m', '400m', '5k', '10k', 'half_marathon', 'marathon', 'run_walk'], 'eventCode') },
  {
    code: 'swimming',
    label: 'Swimming',
    scopeLabel: 'Event and stroke',
    scopes: ['sprint', 'middle_distance', 'distance'].flatMap(eventCode =>
      ['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'individual_medley'].map(disciplineCode => ({
        code: `${eventCode}:${disciplineCode}`,
        label: `${eventCode.replaceAll('_', ' ')} · ${disciplineCode.replaceAll('_', ' ')}`,
        eventCode,
        disciplineCode,
      }))
    ),
  },
  { code: 'tennis', label: 'Tennis', scopeLabel: 'Format', scopes: options(['singles', 'doubles'], 'formatCode') },
  { code: 'volleyball', label: 'Volleyball', scopeLabel: 'Role', scopes: options(['setter', 'outside_hitter', 'middle_blocker', 'opposite', 'libero'], 'roleCode') },
];

export const trainingSport = (labelOrCode: string) => {
  const value = labelOrCode.toLowerCase();
  return TRAINING_SPORTS.find(sport => sport.code === value || sport.label.toLowerCase() === value);
};
