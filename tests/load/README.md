# Run clubs load gate

Run the launch-peak scenario against a staging environment with seeded club and
territory data:

```bash
k6 run \
  -e BASE_URL=https://staging.runlete.app \
  -e ACCESS_TOKEN=replace-with-staging-token \
  -e CLUB_ID=replace-with-seeded-club-uuid \
  -e TILE_X=2938 \
  -e TILE_Y=1969 \
  tests/load/run_clubs.js
```

The gate enforces the platform targets used by the implementation: API p95 below
300 ms, territory-tile p95 below 250 ms, fewer than 1% failed requests, and more
than 99% successful checks. Raise the arrival-rate stages to three times measured
launch peak after staging traffic has established a realistic baseline.
