# Map sources

The country and seven province outlines follow the post-May-2020 Nepal map, including its northwestern extension, as requested. They are derived from `nepali-geo-pro-max`'s province GeoJSON; its build script identifies the underlying updated district boundaries as Acesmndr/nepal-geojson. This presentation follows Nepal's map and does not imply international agreement on disputed boundaries.

- https://github.com/l3lackcurtains/nepali-geo-pro-max/blob/main/src/geo/provinces.geo.ts
- https://github.com/l3lackcurtains/nepali-geo-pro-max/blob/main/scripts/build-geo.cjs
- https://github.com/Acesmndr/nepal-geojson
- Government map reference: https://www.dos.gov.np/nepal-map/

The package is MIT licensed; its copyright notice is included in NEPALI-GEO-LICENSE.txt. The generated data header also lists HDX cod-ab-npl under CC BY 4.0. The map credits the dataset provider and CC BY 4.0. The province polygons were simplified for screen display and merged to obtain the national outline.

Eight city coordinates are extracted from Natural Earth's 1:10m populated places layer, which is public domain:

- https://www.naturalearthdata.com/about/terms-of-use/
- https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_10m_populated_places.geojson

Three additional city coordinates come from GeoNames, licensed under CC BY 4.0:

- Bharatpur: https://www.geonames.org/1283613/
- Janakpur: https://www.geonames.org/1283318/
- Surkhet (represented by Birendranagar city): https://www.geonames.org/6254843/
- Attribution and license: https://www.geonames.org/export/ and https://creativecommons.org/licenses/by/4.0/

Downloaded 2026-09-18. City names are aligned to the fitted model's labels, and label offsets are adjusted for legibility. Locations represent city centers, not verified meteorological station sites. The map uses a simplified equirectangular overview projection. No external tiles, API keys, or network requests are needed at runtime.
