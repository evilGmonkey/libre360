var locMark;
function loadTable()
{
    $(function () {
      $('#table').bootstrapTable({
      });
    });
}

function fetchdevices(){
    $.getJSON(
        "_cameras",
        function(data){
            $('#table').bootstrapTable("load",
            data
            );
        }
    );
    if(cam_summary.ready == cam_summary.required) {
        console.log("Enough cameras online, enabling Play button")
        document.getElementById("play-btn").disabled = false
    }
    else {
        console.log("Not enough cameras online, disabling Play button")
        document.getElementById("play-btn").disabled = true
    }
    locMark.setLatLng({lng: cam_summary["lon"], lat: cam_summary["lat"]});
}

loadTable();
setInterval(fetchdevices, 2000);
jQuery(function() {
    jQuery('#service').change(function() {
        this.form.submit();
    });
});

/*
lastBaseMsg = new Object();
numOfRepetition = 0;

$(document).ready(function () {

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });
    //console.log("main.js Asking for service status");
    //socket.emit("get services status");

    //Ask server for starting rtkrcv or we won't have any data
    socket.emit("start base");

    socket.on('disconnect', function(){
        console.log('disconnected');
    });

    chart = new Chart();
        chart.create();

    $(window).resize(function() {
        if(window.location.hash == ''){
            chart.resize();
        }
    });

    var msg_status = {
            "lat" : "0",
            "lon" : "0",
            "height": "0"
            //"solution status": status,
            //"positioning mode": mode
        };

    updateCoordinateGrid(msg_status)

    // ####################### MAP ####################################################
*/
$(document).ready(function () {

    var map = L.map('map').setView({lon: 0, lat: 0}, 2);

    var osmLayer = L.tileLayer('https://osm.vtech.fr/hot/{z}/{x}/{y}.png?uuid=2fc148f4-7018-4fd0-ac34-6b626cdc97a1', {
        maxZoom: 20,
        attribution: '&copy; <a href="https://openstreetmap.org/copyright" target="_blank">OpenStreetMap contributors</a> ' +
            '| <a href="https://cloud.empreintedigitale.fr" target="_blank">Empreinte digitale</a>',
        tileSize: 256,

    });

//    if (maptiler_key.length > 0) {
//    var aerialLayer = L.tileLayer('https://api.maptiler.com/maps/hybrid/{z}/{x}/{y}.jpg?key=' + maptiler_key,{
//        tileSize: 512,
//        zoomOffset: -1,
//        minZoom: 1,
//        maxZoom: 20,
//        attribution: '<a href="https://www.maptiler.com/copyright/" target="_blank">© MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank">© OpenStreetMap contributors</a>',
//        crossOrigin: true
//      });
//    };

    var baseMaps = {
        "OpenStreetMap": osmLayer
    };

//    if (typeof(aerialLayer) !== 'undefined') {
//        baseMaps["Aerial_Hybrid"] = aerialLayer;
//    };
//    console.log("basemap après if" + baseMaps);
//    console.log
    L.control.layers(baseMaps).addTo(map);
    osmLayer.addTo(map);

    // Add Base station crosshair
    var crossIcon = L.icon({
        iconUrl: '/static/images/iconmonstr-crosshair-6-64.png',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
            });


    //the baseCoordinates variable comes from status.html
//    var baseMark = L.marker(baseCoordinates, {icon: crossIcon, zIndexOffset: 0}).addTo(map);

    // Add realtime localisation marker
    locMark = L.marker({lng: 0, lat: 0}, {icon: crossIcon, zIndexOffset: 0}).addTo(map);

    // Move map view with marker location
    locMark.addEventListener("move", function() {
        const reduceBounds = map.getBounds().pad(-0.4);
        if (reduceBounds.contains(locMark.getLatLng()) != true) {
            console.log("location marker is outside the bound, moving the map");
            map.flyTo(locMark.getLatLng(), 20);
        }
    });
    // make LineString of currently covered trajectory in project
    $.getJSON(
        "_proj_locs",
        function(data){
            L.geoJson(data, {
              style: function(feature) {
                return {
                  stroke: true,
                  color: "red",
                  weight: 5
                };
              },
            }).addTo(map);
        }
    );
//}

});

/*
    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast rover", function(msg) {
            //Tell the server we are still here
            socket.emit("on graph");

            console.groupCollapsed('Rover satellite msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            chart.roverUpdate(msg);
    });

    socket.on("satellite broadcast base", function(msg) {
        // check if the browser tab and app tab are active

        console.groupCollapsed('Base satellite msg received:');
            for (var k in msg)
                console.log(k + ':' + msg[k]);
        console.groupEnd();

        chart.baseUpdate(msg);
    });

    // ####################### HANDLE COORDINATE MESSAGES #######################

    socket.on("coordinate broadcast", function(msg) {
        // check if the browser tab and app tab

        console.groupCollapsed('Coordinate msg received:');
            for (var k in msg)
                console.log(k + ':' + msg[k]);
        console.groupEnd();

        updateCoordinateGrid(msg);

        //update map marker position
        // TODO refactoring with the same instructions in graph.js
        var coordinates = (typeof(msg['pos llh single (deg,m) rover']) == 'undefined') ? '000' : msg['pos llh single (deg,m) rover'].split(',');

        var lat_value = coordinates[0].substring(0, 11) + Array(11 - coordinates[0].substring(0, 11).length + 1).join(" ");
        var lon_value = coordinates[1].substring(0, 11) + Array(11 - coordinates[1].substring(0, 11).length + 1).join(" ");

        locMark.setLatLng({lng: Number(lon_value), lat: Number(lat_value)});
    });

    socket.on("current config rover", function(msg) {
        showRover(msg);
    });

    socket.on("current config base", function(msg) {
        showBase(msg);
    });
});
*/
