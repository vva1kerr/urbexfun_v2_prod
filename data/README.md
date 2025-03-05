Database Structure and Relations:

Table: states
-------------
Columns:
  state_id (INTEGER) [PK]
  state_name (VARCHAR(100))
  state_abbrev (CHAR(2))

========================================
Table: sqlite_sequence
----------------------
Columns:
  name ()
  seq ()

========================================
Table: cities
-------------
Columns:
  city_id (INTEGER) [PK]
  city_name (VARCHAR(100))
  state_id (INTEGER)
  population_2024 (INTEGER)
  population_2020 (INTEGER)
  annual_change (DECIMAL(10, 4))
  density_per_mile2 (DECIMAL(10, 2))
  area_mile2 (DECIMAL(10, 2))

Foreign Keys:
  state_id -> states(state_id)

========================================
Table: lat_long_coords
----------------------
Columns:
  coordinate_id (INTEGER) [PK]
  city_id (INTEGER)
  latitude (DECIMAL(10, 6))
  longitude (DECIMAL(10, 6))

Foreign Keys:
  city_id -> cities(city_id)

========================================
Table: zip_codes
----------------
Columns:
  zip_id (INTEGER) [PK]
  zip_code (CHAR(5))
  city_id (INTEGER)

Foreign Keys:
  city_id -> cities(city_id)

========================================
Table: ip_addresses
-------------------
Columns:
  ip_id (INTEGER) [PK]
  ip_address (VARCHAR(45))
  city_id (INTEGER)

Foreign Keys:
  city_id -> cities(city_id)

========================================