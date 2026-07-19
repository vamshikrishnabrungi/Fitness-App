// Runlete Premium Theme - Nike-inspired
// Generous whitespace, relaxed typography, premium feel

export const colors = {
  // Primary backgrounds
  background: '#FFFFFF',
  surface: '#FFFFFF',
  surfaceSecondary: '#F7F7F7', // Section dividers

  // Text colors
  textPrimary: '#111111',
  textSecondary: '#5E5E63',
  textTertiary: '#7A7A80',
  textDisabled: '#BDBDBD',

  // UI elements
  separator: '#F0F0F0',
  separatorDark: '#E5E5E5',
  border: 'rgba(0,0,0,0.08)',
  borderLight: 'rgba(255,255,255,0.65)',

  // Glass card
  glassBackground: 'rgba(255,255,255,0.98)',
  glassBorder: 'rgba(0,0,0,0.04)',
  glassShadow: 'rgba(0,0,0,0.06)',

  // States - Monochrome
  badgeFilled: '#111111',
  badgeFilledText: '#FFFFFF',
  badgeOutline: '#FFFFFF',
  badgeOutlineBorder: '#E0E0E0',
  badgeOutlineText: '#111111',

  // Progress (default)
  progressFill: '#111111',
  progressTrack: '#F0F0F0',

  // ===== PREMIUM ACCENT COLORS =====

  // Training Load - Emerald Green
  accentGreen: '#2D8A4E',
  accentGreenLight: '#E8F5EC',
  accentGreenBorder: '#B8DFC6',

  // Activity Chart - Blue
  accentBlue: '#4A90D9',
  accentBlueLight: '#EBF3FC',

  // Nutrition Rings - Coral/Orange (Nike-like)
  accentOrange: '#FA5A3D',
  accentOrangeLight: '#FFF0ED',
  accentOrangeBorder: '#F5C4B3',

  // Program Progress - Teal
  accentTeal: '#2AA198',
  accentTealLight: '#E6F5F4',

  // Status Badges
  statusSuccess: '#2D8A4E',
  statusSuccessBg: '#E8F5EC',
  statusWarning: '#E85A4A',
  statusWarningBg: '#FEECEB',
  statusInfo: '#4A90D9',
  statusInfoBg: '#EBF3FC',

  // Goal Icon Backgrounds
  goalWeight: '#FFF0ED',
  goalWorkout: '#FEECEB',
  goalSleep: '#EBF3FC',
  goalWater: '#E6F5F4',

  // Subtle accent (legacy)
  accentSubtle: '#F5F5F5',
  accent: '#111111',

  // ===== BRAND (signature coral — energetic Nike accent on white) =====
  brand: '#FF4E2E',
  brand2: '#FF7A18',
  brandSoft: '#FFEDE7',

  // Bold dark feature card (used sparingly on white for hierarchy)
  featureCard: '#0F0F12',
  featureCard2: '#1C1C1E',

  // Metallic podium medals
  medalGold: ['#FCE08A', '#D19A2C'] as [string, string],
  medalSilver: ['#F1F3F8', '#AEB6C6'] as [string, string],
  medalBronze: ['#F3B375', '#B06B31'] as [string, string],

  // Transparent
  transparent: 'transparent',
};

// Nike-style generous spacing
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,    // Increased from 20
  xxl: 32,   // Increased from 24
  xxxl: 48,  // Increased from 32
  section: 40, // New: section spacing
  page: 24,    // New: page horizontal padding
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  full: 9999,
};

// Nike-style relaxed typography
export const typography = {
  // Headlines - slightly lighter weight
  h1: {
    fontSize: 28,  // Reduced from 32
    fontWeight: '600' as const,  // Reduced from 700
    letterSpacing: -0.3,
    lineHeight: 36,
  },
  h2: {
    fontSize: 22,  // Reduced from 24
    fontWeight: '600' as const,
    letterSpacing: -0.2,
    lineHeight: 30,
  },
  h3: {
    fontSize: 18,  // Reduced from 20
    fontWeight: '600' as const,
    letterSpacing: -0.1,
    lineHeight: 26,
  },
  h4: {
    fontSize: 16,  // Reduced from 17
    fontWeight: '600' as const,
    letterSpacing: 0,
    lineHeight: 24,
  },

  // Body - larger with more line height
  body: {
    fontSize: 16,  // Increased from 15
    fontWeight: '400' as const,
    lineHeight: 26,  // Increased from 22
  },
  bodyMedium: {
    fontSize: 16,
    fontWeight: '500' as const,
    lineHeight: 26,
  },
  bodySemibold: {
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 26,
  },

  // Small text
  caption: {
    fontSize: 14,  // Increased from 13
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  captionMedium: {
    fontSize: 14,
    fontWeight: '500' as const,
    lineHeight: 20,
  },

  // Section labels - now sentence case style
  label: {
    fontSize: 14,  // Increased from 11
    fontWeight: '600' as const,
    letterSpacing: 0,  // Removed wide spacing
    lineHeight: 20,
  },

  // Small labels (for badges)
  labelSmall: {
    fontSize: 11,
    fontWeight: '600' as const,
    letterSpacing: 0.5,
    textTransform: 'uppercase' as const,
    lineHeight: 16,
  },

  // Large display
  display: {
    fontSize: 48,
    fontWeight: '700' as const,
    letterSpacing: -1,
    lineHeight: 56,
  },

  // Stats/Numbers
  stat: {
    fontSize: 28,
    fontWeight: '600' as const,
    letterSpacing: -0.5,
    lineHeight: 34,
  },
};

export const shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.08,
    shadowRadius: 24,
    elevation: 5,
  },
  glass: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 16,
    elevation: 3,
  },
};
