const base = arguments[0].parentElement
return document.querySelectorAll("#map > div.leaflet-pane.leaflet-map-pane > div.leaflet-pane.leaflet-overlay-pane > svg > g > path")[(([...base.parentElement.children].indexOf(base) - 1) / 2)]