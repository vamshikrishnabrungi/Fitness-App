import React from 'react';
import { StyleSheet, View } from 'react-native';
import MapView, { Marker, Polyline } from 'react-native-maps';
import { colors } from '../utils/theme';

export type RoutePoint = { latitude: number; longitude: number };

const regionFor = (points: RoutePoint[]) => {
  const latitudes = points.map((point) => point.latitude);
  const longitudes = points.map((point) => point.longitude);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  return {
    latitude: (minLatitude + maxLatitude) / 2,
    longitude: (minLongitude + maxLongitude) / 2,
    latitudeDelta: Math.max(0.004, (maxLatitude - minLatitude) * 1.8),
    longitudeDelta: Math.max(0.004, (maxLongitude - minLongitude) * 1.8),
  };
};

export function RunRouteMap({ points }: { points: RoutePoint[] }) {
  return (
    <MapView
      style={StyleSheet.absoluteFill}
      initialRegion={regionFor(points)}
      scrollEnabled={false}
      zoomEnabled={false}
      pitchEnabled={false}
      rotateEnabled={false}
      showsPointsOfInterest={false}
      showsCompass={false}
      toolbarEnabled={false}
    >
      <Polyline coordinates={points} strokeColor={colors.brand} strokeWidth={5} lineCap="round" lineJoin="round" />
      <Marker coordinate={points[0]} anchor={{ x: 0.5, y: 0.5 }}>
        <View style={[styles.pin, styles.start]} />
      </Marker>
      <Marker coordinate={points[points.length - 1]} anchor={{ x: 0.5, y: 0.5 }}>
        <View style={[styles.pin, styles.end]} />
      </Marker>
    </MapView>
  );
}

const styles = StyleSheet.create({
  pin: {
    width: 14,
    height: 14,
    borderRadius: 7,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  start: { backgroundColor: '#22C55E' },
  end: { backgroundColor: colors.brand },
});
