CREATE OR REPLACE FUNCTION are_labels_v1_valid(jsonb_labels jsonb) RETURNS BOOLEAN AS $$
DECLARE
    element jsonb;
BEGIN
    -- must have 'version' and 'values' properties
    IF NOT (jsonb_labels ? 'version' AND jsonb_labels ? 'values') THEN
        RETURN FALSE;
    END IF;
    -- version must be '1'
    IF jsonb_labels ->> 'version' != '1' THEN
        RETURN FALSE;
    END IF;

    FOR element IN SELECT * FROM jsonb_array_elements(jsonb_labels -> 'values')
    LOOP
        -- must be an object
        IF jsonb_typeof(element) != 'object' THEN
            RETURN FALSE;
        END IF;
        -- must have rel, value, scheme, and creation properties
        IF NOT (element ? 'rel' AND element ? 'value' AND element ? 'scheme' AND element ? 'creation') THEN
            RETURN FALSE;
        END IF;
    END LOOP;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
