---
from: "op://Infrastructure/qmhl6un36h3gxnjzlqtkahgqqy/PSQL connection string"
to: "postgresql://[username]:[password]@[host]/[database]"

exclude:
- meta_migration
- nvs_l06_lookup
- spatial_ref_sys
- record
- layer

schemas:
- public
