const SVG_NS = "http://www.w3.org/2000/svg";

// A local equirectangular overview; no remote map tiles or API key required.
function project([longitude, latitude]) {
  return [50 + (longitude - 80) * 103, 22 + (30.55 - latitude) * 92];
}

function svgElement(tag, attributes) {
  const element = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function geometryPath(geometry) {
  const polygons = geometry.type === "Polygon" ? [geometry.coordinates] : geometry.coordinates;
  return polygons.flatMap(polygon => polygon.map(ring => ring.map((coordinate, index) => {
    const [x, y] = project(coordinate);
    return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ") + " Z")).join(" ");
}

export default function ({ parentElement, data, setTriggerValue }) {
  const root = parentElement?.querySelector(".explore-card")
    || parentElement?.querySelector(".station-picker")
    || parentElement;
  if (!root) return;

  const points = root.querySelector("[data-stations]");
  const mobile = root.querySelector(".mobile-stations");
  const provinces = root.querySelector("[data-provinces]");
  const colors = ["#dee5f7", "#dbeaf6", "#e8e1f3", "#d9ece7", "#e8ecd4", "#e0e9dd", "#f0e7d9"];

  if (provinces && data?.provinces) {
    provinces.replaceChildren();
    data.provinces.forEach((province, index) => provinces.append(svgElement("path", {
      d: geometryPath(province.geometry), fill: colors[index % colors.length], stroke: "#fff", "stroke-width": 1.5,
    })));
  }

  const boundaryEl = root.querySelector("[data-boundary]");
  if (boundaryEl && data?.boundary) boundaryEl.setAttribute("d", geometryPath(data.boundary));

  const selectedEl = root.querySelector("[data-selected]");
  if (selectedEl && data?.selected) selectedEl.textContent = data.selected;

  const countEl = root.querySelector("[data-count]");
  if (countEl && data?.stations) countEl.textContent = `${data.stations.length} stations`;

  if (points) points.replaceChildren();
  if (mobile) mobile.replaceChildren();

  function choose(name) {
    const sel = root.querySelector("[data-selected]");
    if (sel) sel.textContent = name;
    root.querySelectorAll("[data-station]").forEach(element => {
      element.setAttribute("aria-pressed", String(element.dataset.station === name));
    });
    setTriggerValue("station", name);
  }

  if (data?.stations) {
    data.stations.forEach(station => {
      const [x, y] = project(station.coordinates);
      const [dx, dy] = station.label_offset;
      const selected = station.name === data.selected;
      const marker = svgElement("g", {
        class: "station", transform: `translate(${x},${y})`,
        role: "button", tabindex: "0", "aria-label": `Select ${station.name}`,
        "aria-pressed": String(selected), "data-station": station.name,
      });
      const labelWidth = station.name.length * 11;
      const left = Math.min(-20, dx < 0 ? dx - labelWidth : dx);
      const right = Math.max(20, dx < 0 ? dx : dx + labelWidth);
      const top = Math.min(-20, dy - 20);
      const bottom = Math.max(20, dy + 6);
      marker.append(
        svgElement("rect", { class: "hit-area", x: left, y: top, width: right - left, height: bottom - top }),
        svgElement("circle", { class: "halo", r: 14 }),
        svgElement("circle", { class: "pin", r: 6 }),
      );
      const label = svgElement("text", {
        x: dx, y: dy, class: "city-label", "text-anchor": dx < 0 ? "end" : "start",
      });
      label.textContent = station.name;
      marker.append(label);
      marker.onclick = () => choose(station.name);
      marker.onkeydown = event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          choose(station.name);
        }
      };
      if (points) points.append(marker);

      if (mobile) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = station.name;
        button.dataset.station = station.name;
        button.setAttribute("aria-pressed", String(selected));
        button.onclick = () => choose(station.name);
        mobile.append(button);
      }
    });
  }

  const search = root.querySelector('input[type="search"]');
  if (search) {
    if (root.dataset.selected !== data.selected) {
      search.value = "";
      root.dataset.selected = data.selected;
    }
    function filterStations() {
      const query = search.value.trim().toLowerCase();
      let count = 0;
      root.querySelectorAll("[data-station]").forEach(element => {
        const visible = element.dataset.station.toLowerCase().includes(query);
        element.toggleAttribute("hidden", !visible);
        if (visible && element.tagName.toLowerCase() === "g") count++;
      });
      if (countEl) countEl.textContent = `${count} ${count === 1 ? "station" : "stations"}`;
      const noResults = root.querySelector(".no-results");
      if (noResults) noResults.hidden = count > 0;
    }
    search.oninput = filterStations;
    filterStations();
  }

  let zoom = Number(root.dataset.zoom || 1);
  function applyZoom() {
    const mapLayer = root.querySelector("[data-map-layer]");
    if (!mapLayer) return;
    const station = data?.stations?.find(item => item.name === data.selected);
    const [x, y] = station ? project(station.coordinates) : [480, 225];
    mapLayer.setAttribute("transform", zoom === 1 ? "" : `translate(480 225) scale(${zoom}) translate(${-x} ${-y})`);
    root.dataset.zoom = zoom;
    const zoomIn = root.querySelector('[data-zoom="in"]');
    if (zoomIn) zoomIn.disabled = zoom >= 2.5;
    const zoomOut = root.querySelector('[data-zoom="out"]');
    if (zoomOut) zoomOut.disabled = zoom <= 1;
  }
  root.querySelectorAll("[data-zoom]").forEach(button => {
    button.onclick = () => {
      zoom = button.dataset.zoom === "reset" ? 1 : Math.max(1, Math.min(2.5, zoom + (button.dataset.zoom === "in" ? 0.5 : -0.5)));
      applyZoom();
    };
  });
  applyZoom();
}
