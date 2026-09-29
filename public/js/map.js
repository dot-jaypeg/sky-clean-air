/* Service-area map. The builder embeds the pins as JSON in
   <script type="application/json" id="map-data"> and marks the map
   container with [data-area-map]. Pins are dots colored by status:
   active (sky), launching (teal ring), coming-soon (gray). */
(function () {
  'use strict';
  var el = document.querySelector('[data-area-map]');
  var dataEl = document.getElementById('map-data');
  if (!el || !dataEl || !window.L) return;
  var cfg = JSON.parse(dataEl.textContent);

  var map = L.map(el, { scrollWheelZoom: false, zoomControl: true, attributionControl: true, zoomSnap: 0.25 });
  L.tileLayer(cfg.tiles.url, { attribution: cfg.tiles.attribution, maxZoom: 16 }).addTo(map);

  var STYLE = {
    active: { radius: 6, color: '#0f1f33', weight: 1.5, fillColor: '#2addea', fillOpacity: 0.95 },
    launching: { radius: 7, color: '#ffffff', weight: 2, fillColor: '#0e7f95', fillOpacity: 1 },
    'coming-soon': { radius: 6, color: '#5c6a78', weight: 1.5, fillColor: '#c9d3db', fillOpacity: 0.9, dashArray: '2 2' },
    current: { radius: 10, color: '#060c14', weight: 3, fillColor: '#2addea', fillOpacity: 1 }
  };

  var layers = {};
  var all = [];
  cfg.pins.forEach(function (p) {
    var style = STYLE[p.current ? 'current' : p.status] || STYLE.active;
    var m = L.circleMarker([p.lat, p.lng], style);
    var label = '<strong>' + p.name + '</strong><br><span>' + p.region + (p.status === 'coming-soon' ? ' · Coming soon' : '') + '</span>';
    if (p.href) label += '<br><a href="' + p.href + '">View ' + p.name + ' &rarr;</a>';
    m.bindPopup(label);
    m.bindTooltip(p.name, { direction: 'top', offset: [0, -6] });
    m.addTo(map);
    (layers[p.regionSlug] = layers[p.regionSlug] || []).push(m);
    all.push(m);
  });

  function fit(markers, pad) {
    if (!markers.length) return;
    map.fitBounds(L.featureGroup(markers).getBounds(), { padding: [pad || 16, pad || 16], maxZoom: cfg.maxZoom || 13 });
  }
  if (cfg.center) map.setView(cfg.center, cfg.zoom || 12);
  else fit(all);

  // Region filter buttons (hub page)
  document.querySelectorAll('[data-map-region]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('[data-map-region]').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      var r = btn.getAttribute('data-map-region');
      fit(r === 'all' ? all : (layers[r] || []));
    });
  });

  // Enable scroll-zoom only after the user interacts with the map.
  map.once('focus click', function () { map.scrollWheelZoom.enable(); });
})();
