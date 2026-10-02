# Monsoon interface

## References

- Apple Weather: https://support.apple.com/guide/iphone/check-the-weather-iph1ac0b35f/26/ios/26
- Apple information hierarchy: https://developer.apple.com/design/human-interface-guidelines/widgets
- Software Mind weather dashboard: https://dribbble.com/shots/24367006-Weather-App-Dashboard
- Arshiya Heshmatipour weather dashboard: https://dribbble.com/shots/25261571-Weather-App-Dashboard
- Orix Creative precipitation and map study: https://dribbble.com/shots/27447337-Weather-App-UI-Mobile-Map-Precipitation-Dashboard
- Taste skill discovered on skills.sh: https://www.skills.sh/leonxlnx/taste-skill/design-taste-frontend

## Design choices

The interface is a forecast tool, not a marketing page. Station, date, measurements, and the result are the main content. The map is an optional station selector. Measurements remain grouped into four tabs. Example values and the 3 PM Nepal cutoff are explained beside the inputs. Forecast results always show the station and forecast date; changing observations makes the result stale rather than leaving an old probability visible.

The previous design used oversized condensed typography, green backgrounds, numbered labels, and slogan copy. These are replaced with the native Apple system font stack, neutral silver surfaces, graphite text, a single muted blue accent, sentence-case headings, and functional copy. Radius scale: 7 px segmented selection, 10 px inputs/buttons, 18 px forecast panel. Motion is limited to click feedback and probability updates. Design variance 4, motion intensity 3, density 5; the product workflow takes priority over marketing-page conventions in the Taste skill.

## Assets

`himalayan-sky.webp` was created with the built-in imagegen tool and optimized as a local WebP. It is decorative illustration, not a camera image of the selected station or a representation of current conditions.

Final generation prompt:

> Use case: photorealistic-natural. Asset type: scenic background for a Nepal rainfall web application, not a UI mockup. Create a wide landscape photograph of distant Himalayan mountain ridges under a spacious cloudy sky, slate blue mountains, silver-white atmospheric cloud layers, muted cool gray-blue palette. Mountains occupy only bottom third, calm open clouded sky fills upper two thirds. Soft natural overcast daylight, sophisticated realistic editorial landscape photography, delicate atmospheric depth. No green scenery, no neon, no dramatic glow, no people, no text, no logos. Landscape 3:2 composition.

Cloud, sun, and rain icons are from Tabler Icons (MIT), with a consistent muted blue stroke. See TABLER-ICONS-LICENSE.txt. The existing Nepal map attribution remains in MAP-SOURCES.md.

## Appearance and readability

The interface uses a fixed white appearance, including when the operating system is in dark mode. Typography uses -apple-system and BlinkMacSystemFont, resolving to the native San Francisco font on supported Apple devices, with Helvetica Neue and sans-serif fallbacks. Supporting text has a 14 px minimum, readings use 16 px, and captions have full opacity. Narrow screens stack input columns rather than shrinking their labels.
