import React from 'react';
import { StyleSheet } from 'react-native';
import MapView, { Polyline } from 'react-native-maps';
import { colors } from '../utils/theme';
import { RoutePoint } from './RunRouteMap';

type Region = RoutePoint & { latitudeDelta: number; longitudeDelta: number };

export function LiveRunMap({
  initialRegion,
  points,
  following,
}: {
  initialRegion: Region;
  points: RoutePoint[];
  following: boolean;
}) {
  return (
    <MapView
      style={StyleSheet.absoluteFill}
      initialRegion={initialRegion}
      showsUserLocation
      followsUserLocation={following}
      showsMyLocationButton={false}
      showsCompass={false}
      showsPointsOfInterest={false}
      toolbarEnabled={false}
    >
      {points.length > 1 && (
        <Polyline coordinates={points} strokeColor={colors.brand} strokeWidth={6} lineCap="round" lineJoin="round" />
      )}
    </MapView>
  );
}
