# Runlete mobile application

Expo Router app for recording/processing runs, activities, verified territory,
clubs, leaderboards, challenges, races, achievements, notifications, governance,
and moderation appeals.

## Local setup

```bash
npm install
cp .env.example .env
npx expo start
```

The native map and background recorder require a development build; Expo Go
cannot exercise all native behavior:

```bash
npx expo run:ios
npx expo run:android
```

Required build/runtime variables:

```text
EXPO_PUBLIC_BACKEND_URL=https://api.runlete.example
EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN=pk...
RNMAPBOX_MAPS_DOWNLOAD_TOKEN=sk...
```

The public Mapbox token is intentionally embedded in the mobile app and must be
restricted to Runlete's bundle/application IDs. The secret SDK download token is
for dependency/build-time access only and belongs in EAS/CI secrets.

Production push requires APNs and FCM credentials configured for the EAS project.
Apple Health and Health Connect synchronization also require native entitlements,
user consent and a signed development/release build; the app never reports either
source as connected until the SQL integration connection is active.
Do not place APNs keys, service-account JSON, backend secrets, or AWS credentials
in `EXPO_PUBLIC_*` variables.

## Generated contracts and checks

The source API contract is the backend `openapi.json`; do not create a second
handwritten backend model set:

```bash
npm run generate:api
npm run typecheck
npm run lint
npx expo export --platform web
```

Native release acceptance must also cover weak GPS, urban drift, backgrounding,
termination recovery, airplane mode, upload interruption, privacy zones,
Mapbox MVT interaction, dynamic text, and screen readers on physical iOS and
Android devices.
