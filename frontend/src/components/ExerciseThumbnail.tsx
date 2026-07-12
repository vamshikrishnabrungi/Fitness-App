import React from 'react';
import { Image, ImageSourcePropType, StyleSheet, Text, View, ViewStyle } from 'react-native';

import { EXERCISE_THUMBNAILS } from '../data/exerciseThumbnailMap';
import { colors } from '../utils/theme';

interface ExerciseThumbnailProps {
  name?: string | null;
  size?: number;
  style?: ViewStyle;
}

const normalizeExerciseName = (name?: string | null) =>
  (name || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

export const hasExerciseThumbnail = (name?: string | null) => {
  return Boolean(EXERCISE_THUMBNAILS[normalizeExerciseName(name)]);
};

export function ExerciseThumbnail({ name, size = 64, style }: ExerciseThumbnailProps) {
  const source: ImageSourcePropType | undefined = EXERCISE_THUMBNAILS[normalizeExerciseName(name)];

  return (
    <View style={[styles.wrap, { width: size, height: size, borderRadius: Math.max(12, size * 0.22) }, style]}>
      {source ? (
        <Image source={source} style={styles.image} resizeMode="cover" />
      ) : (
        <View style={styles.pending}>
          <Text style={styles.pendingText}>Image</Text>
          <Text style={styles.pendingText}>pending</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    backgroundColor: '#F6F5F2',
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  pending: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  pendingText: {
    fontSize: 9,
    fontWeight: '800',
    lineHeight: 11,
    color: colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.2,
  },
});
