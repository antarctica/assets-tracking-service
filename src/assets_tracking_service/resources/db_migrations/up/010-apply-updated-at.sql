CREATE OR REPLACE TRIGGER asset_updated_at_trigger
  BEFORE INSERT OR UPDATE
  ON public.asset
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();

CREATE OR REPLACE TRIGGER position_updated_at_trigger
  BEFORE INSERT OR UPDATE
  ON public.position
  FOR EACH ROW
  EXECUTE FUNCTION set_updated_at();
