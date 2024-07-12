DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'ddm_point'
    ) THEN
        CREATE TYPE ddm_point AS (x TEXT, y TEXT);
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION geom_as_ddm(geom GEOMETRY)
    RETURNS ddm_point
    IMMUTABLE
    PARALLEL SAFE
AS $$
DECLARE
    lon FLOAT;
    lat FLOAT;
    lon_degree FLOAT;
    lon_minutes FLOAT;
    lon_sign TEXT;
    lat_degree FLOAT;
    lat_minutes FLOAT;
    lat_sign TEXT;
    x TEXT;
    y TEXT;
BEGIN
    lon := ST_X(geom);
    lat := ST_Y(geom);

    SELECT FLOOR(ABS(lon)), FLOOR(ABS(lat))
    INTO lon_degree, lat_degree;

    SELECT ((ABS(lon) - lon_degree) * 60.0), ((ABS(lat) - lat_degree) * 60.0)
    INTO lon_minutes, lat_minutes;

    IF lon >= 0 THEN
        lon_sign := 'E';
    ELSE
        lon_sign := 'W';
    END IF;

    IF lat >= 0 THEN
        lat_sign := 'N';
    ELSE
        lat_sign := 'S';
    END IF;

    x := CONCAT(CAST(lon_degree AS TEXT), '° ', TO_CHAR(lon_minutes, 'FM999999.999999'), ''' ', lon_sign);
    y := CONCAT(CAST(lat_degree AS TEXT), '° ', TO_CHAR(lat_minutes, 'FM999999.999999'), ''' ', lat_sign);

    RETURN (x, y);
END;
$$ LANGUAGE plpgsql;
