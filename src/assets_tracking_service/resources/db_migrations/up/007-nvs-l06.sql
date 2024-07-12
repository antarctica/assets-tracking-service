CREATE TABLE IF NOT EXISTS nvs_l06_lookup
(
    code TEXT PRIMARY KEY,
    label TEXT NOT NULL UNIQUE
);

INSERT INTO nvs_l06_lookup (code, label)
VALUES
    ('0', 'UNKNOWN'),
    ('15', 'LAND/ONSHORE VEHICLE'),
    ('31', 'RESEARCH VESSEL'),
    ('62', 'AEROPLANE')
ON CONFLICT (code)
DO NOTHING;
;
