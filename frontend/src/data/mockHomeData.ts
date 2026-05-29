/**
 * Mock Data Layer for Home Cards
 * Single source file - replace with real API calls later
 */

// Strain Data
export const mockStrainData = {
    today: 12.4,
    status: 'moderate' as const, // low | moderate | high
    weeklyAvg: 14.2,
    safeZone: { min: 10, max: 18 },
    history: [
        { day: 'Mon', value: 15.2 },
        { day: 'Tue', value: 12.8 },
        { day: 'Wed', value: 18.4 },
        { day: 'Thu', value: 8.2 },
        { day: 'Fri', value: 14.6 },
        { day: 'Sat', value: 16.1 },
        { day: 'Sun', value: 12.4 },
    ],
    breakdown: [
        { type: 'Workouts', minutes: 45, load: 8.2 },
        { type: 'Runs', minutes: 32, load: 4.2 },
    ],
};

// Recovery Data
export const mockRecoveryData = {
    score: 68,
    status: 'moderate' as const,
    sleep: { value: 7.5, quality: 'Good' },
    hrv: { value: 45, unit: 'ms', trend: 'up' as const },
    rhr: { value: 58, unit: 'bpm', trend: 'stable' as const },
};

// Biology Data
export const mockBiologyData = {
    leanMass: { value: 62.4, unit: 'kg', trend: 'stable' as const },
    bodyFat: { value: 18.2, unit: '%', trend: 'down' as const },
    weight: { value: 76.2, unit: 'kg' },
    status: 'stable' as const, // stable | trending_up | needs_update
    insight: 'Lean mass stable · Body fat trending down',
    lastUpdated: '2 days ago',
};

// Quick Log Data
export const mockQuickLogData = {
    logged: false,
    lastLogTime: null as string | null,
    mood: null as number | null,
    energy: null as 'low' | 'moderate' | 'high' | null,
    stress: null as 'low' | 'moderate' | 'high' | null,
};

// Type exports
export type StrainData = typeof mockStrainData;
export type RecoveryData = typeof mockRecoveryData;
export type BiologyData = typeof mockBiologyData;
export type QuickLogData = typeof mockQuickLogData;
