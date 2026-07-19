"""Seed the starter game board: ~12 curated Hyderabad running corridors with geometry.

Geometry is approximate (hand-placed) for dev — real OSM polylines come later. The engine
works regardless; these just give a recognizable, fair board to play on.
"""
import uuid
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
import territory  # local module

# name, stars(value 1-5), polyline [[lat,lng], ...]
CORRIDORS = [
    ("Necklace Road", 5, [[17.4360, 78.4735], [17.4305, 78.4762], [17.4245, 78.4755], [17.4200, 78.4720]]),
    ("Tank Bund", 4, [[17.4185, 78.4718], [17.4245, 78.4700], [17.4305, 78.4690], [17.4355, 78.4700]]),
    ("Hussain Sagar Loop", 5, [[17.4360, 78.4735], [17.4305, 78.4762], [17.4245, 78.4755], [17.4200, 78.4720],
                               [17.4245, 78.4700], [17.4305, 78.4690], [17.4360, 78.4715], [17.4360, 78.4735]]),
    ("KBR Park Loop", 5, [[17.4170, 78.4180], [17.4210, 78.4205], [17.4225, 78.4255], [17.4185, 78.4275],
                          [17.4140, 78.4245], [17.4150, 78.4195], [17.4170, 78.4180]]),
    ("Durgam Cheruvu Trail", 4, [[17.4320, 78.3880], [17.4352, 78.3910], [17.4335, 78.3950], [17.4292, 78.3930]]),
    ("Gachibowli Stadium Loop", 3, [[17.4450, 78.3480], [17.4480, 78.3510], [17.4460, 78.3552], [17.4420, 78.3530], [17.4450, 78.3480]]),
    ("Botanical Garden Loop", 3, [[17.4630, 78.3350], [17.4660, 78.3378], [17.4642, 78.3418], [17.4602, 78.3392], [17.4630, 78.3350]]),
    ("Jubilee Hills Road 36", 4, [[17.4300, 78.4080], [17.4332, 78.4120], [17.4360, 78.4155]]),
    ("Banjara Hills Road 12", 3, [[17.4120, 78.4350], [17.4150, 78.4400], [17.4182, 78.4442]]),
    ("Sanjeevaiah Park", 3, [[17.4400, 78.4750], [17.4432, 78.4782], [17.4410, 78.4820]]),
    ("ORR Cyber Stretch", 2, [[17.4700, 78.3600], [17.4750, 78.3700], [17.4782, 78.3800]]),
    ("Nizam Loop, Golconda", 4, [[17.3830, 78.4010], [17.3862, 78.4042], [17.3845, 78.4082], [17.3805, 78.4056], [17.3830, 78.4010]]),
]


def main():
    env = {}
    for l in Path(__file__).with_name('.env').read_text().splitlines():
        if '=' in l and not l.startswith('#'):
            k, v = l.split('=', 1); env[k.strip()] = v.strip().strip('"').strip("'")
    db = MongoClient(env['MONGO_URL'])[env['DB_NAME']]
    db.corridors.delete_many({})
    db.corridor_influence.delete_many({})
    now = datetime.utcnow()
    for name, stars, geo in CORRIDORS:
        pts = [(p[0], p[1]) for p in geo]
        segs = territory.split_into_segments(pts, seg_len_m=150)
        db.corridors.insert_one({
            'id': str(uuid.uuid4()),
            'name': name,
            'city': 'Hyderabad',
            'country': 'India',
            'value': stars,
            'geometry': geo,
            'segments': [[[round(x, 6), round(y, 6)] for (x, y) in s] for s in segs],
            'segment_count': len(segs),
            'length_km': round(territory.polyline_length_m(pts) / 1000, 2),
            'created_at': now,
        })
        print(f"  {name:26s} {stars}★  {len(segs)} segments  {round(territory.polyline_length_m(pts)/1000,2)} km")
    print(f"\nseeded {len(CORRIDORS)} corridors in Hyderabad")


if __name__ == '__main__':
    main()
