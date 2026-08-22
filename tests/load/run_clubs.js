import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = (__ENV.BASE_URL || '').replace(/\/$/, '');
const token = __ENV.ACCESS_TOKEN || '';
const clubId = __ENV.CLUB_ID || '';

if (!baseUrl || !token || !clubId) {
  throw new Error('BASE_URL, ACCESS_TOKEN, and CLUB_ID are required');
}

export const options = {
  scenarios: {
    launch_peak: {
      executor: 'ramping-arrival-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 100,
      maxVUs: 600,
      stages: [
        { target: 50, duration: '2m' },
        { target: 150, duration: '5m' },
        { target: 0, duration: '1m' },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{kind:api}': ['p(95)<300'],
    'http_req_duration{kind:tile}': ['p(95)<250'],
    checks: ['rate>0.99'],
  },
};

const headers = { Authorization: `Bearer ${token}` };

export default function () {
  const club = http.get(`${baseUrl}/api/v1/clubs/${clubId}`, {
    headers,
    tags: { kind: 'api' },
  });
  check(club, { 'club detail is available': (response) => response.status === 200 });

  const leaderboard = http.get(
    `${baseUrl}/api/v1/clubs/${clubId}/leaderboards?period=week&metric=distance`,
    { headers, tags: { kind: 'api' } },
  );
  check(leaderboard, {
    'leaderboard is available': (response) => response.status === 200,
  });

  const session = http.post(
    `${baseUrl}/api/v1/territory/tile-session`,
    JSON.stringify({ layer: 'club', club_id: clubId }),
    {
      headers: { ...headers, 'Content-Type': 'application/json' },
      tags: { kind: 'api' },
    },
  );
  check(session, { 'tile session is issued': (response) => response.status === 200 });
  if (session.status === 200) {
    const template = session.json('tile_url');
    const tileUrl = template
      .replace('{z}', '12')
      .replace('{x}', __ENV.TILE_X || '2938')
      .replace('{y}', __ENV.TILE_Y || '1969');
    const tile = http.get(tileUrl, { tags: { kind: 'tile' } });
    check(tile, { 'territory tile is available': (response) => response.status === 200 });
  }

  sleep(0.2);
}

