const API_URL = 'https://yourid.execute-api.eu-west-1.amazonaws.com/workshop'
const API_KEY = 'youruniqueAPIkey'
mapboxgl.accessToken = 'pk.yourmapboxAPItoken';

let map;
let images = ['./img/ForLease.png', './img/Agreed.png']

$(document).ready(function () {

    // Map constructor
    map = new mapboxgl.Map({
        container: 'map', // container ID
        style: 'mapbox://styles/mapbox/outdoors-v11', // style URL
        center: [-73.935242, 40.730610], // starting position [lng, lat]
        zoom: 11 // starting zoom
    });

    // On map move, refresh data using cache
    map.on('moveend', () => {
        // Get coords of the center of map view  
        const { lng, lat } = map.getCenter();
        // Refresh map with new properties
        populate(lng, lat);
    });

    // On map load, populate initial properties
    map.on('load', () => {
        const { lng, lat } = map.getCenter();

        populate(lng, lat)
    });

    // Initiate propery carousel    
    $('.center-slick').slick({
        centerMode: true,
        centerPadding: '40px',
        slidesToShow: 9,
        slidesToScroll: 3,
        responsive: [
            {
                breakpoint: 768,
                settings: {
                    arrows: false,
                    centerMode: true,
                    centerPadding: '20px',
                    slidesToShow: 3,
                    slidesToScroll: 1,
                }
            },
            {
                breakpoint: 480,
                settings: {
                    arrows: false,
                    centerMode: true,
                    centerPadding: '10px',
                    slidesToShow: 1,
                }
            }
        ]
    });


    // Click Events
    // 
    // Edit Property Button Click
    $('body').on('click', '#edit', function (e) {
        // Get property details
        let prop = JSON.parse(decodeURIComponent($('#edit').data('property')));
        // Create edit form
        addFormValues(prop)
    })

    // Save Changes 
    $('body').on('click', '#save', function (e) {
        let prop = JSON.parse(decodeURIComponent($('#edit').data('property')));
        submitEdit(prop)
    })

    // Move Selected Property to Centre of Carousel
    $('.center-slick').on('click', '.slick-slide', function (e) {
        e.stopPropagation();
        var index = $(this).data("slick-index");
        if ($('.center-slick').slick('slickCurrentSlide') !== index) {
            $('.center-slick').slick('slickGoTo', index);
        }
    });

    // Add PopUp for Selected Property  
    $('.center-slick').on('afterChange', async function () {

        let lng = $('.slick-center').data('lng');
        let lat = $('.slick-center').data('lat');
        let key = JSON.parse(decodeURIComponent($('.slick-center').data('property')));
        let imageKey = $('.slick-center').data('img');
        // Get Details from Redis
        let property = await getPropertyDetail(key)
        // Show PopIp
        addPopUp(lng, lat, addDesc(property, imageKey))

    });
})

// Add PopUp
function addPopUp(lng, lat, desc) {

    $('.mapboxgl-popup').remove();
    new mapboxgl.Popup({ anchor: 'left' })
        .setLngLat([parseFloat(lng), parseFloat(lat)])
        .setHTML(desc)
        .addTo(map);
}

// Search Properties in Radius (Hard Coded Radius of 10)
async function fetchData(lon, lat) {

    try {
        let data = { "lat": lat, "lon": lon, "radius": 10 }
        const resp = await fetch(API_URL + "/property-search", {
            method: "POST",
            headers: { 'Content-Type': 'application/json', 'X-Api-Key': API_KEY }, // API Key for API Gateway
            body: JSON.stringify(data),
        })

        if (!resp.ok) {
            throw new Error(`Error! status: ${resp.status}`);
        }

        return await resp.json()

    } catch (err) {
        console.log(err)
    }

}

// Get Details of Property
async function getPropertyDetail(key) {
    try {

        const resp = await fetch(API_URL + "/property-detail", {
            method: "POST",
            headers: { 'Content-Type': 'application/json', 'X-Api-Key': API_KEY }, // API Key for API Gateway
            body: JSON.stringify({ 'property_key': key }),
        })

        if (!resp.ok) {
            throw new Error(`Error! status: ${resp.status}`);
        }

        return await resp.json()

    } catch (err) {
        console.log(err)
    }
}

// Add description for icon popup
function addDesc(property, imgKey) {
    return `<div class="card" style="width: 16rem;">
    <div class="row h-50">
        <div class="col h-50">
                <img style="opacity: 0.7;"
                    src=${images[imgKey]}
                    class="card-img-top img-fluid" alt="...">
                <div class="card-footer border-success">
                    <i class="fa-regular fa-square-full fa-lg"></i> 1200sqft |
                    <i class="fa-solid fa-bath fa-lg"></i> ${property.bathrooms} |
                    <i class="fa-solid fa-bed fa-lg"></i> ${property.bedrooms} |
                    <i class="fa-solid fa-car fa-lg"></i> 2
                </div>
        </div>
    </div>
    <div class="card-body">
        <h5 class="card-title">${property.agency}</h5>
        <p class="card-text">${property.address}</p>
        <div class="card-text text-end"><h5>$${property.price} <small>/m</small></h5></div>
        <div class="text-center mt-3"><button type="button" id="edit" class="btn btn-primary" data-property=${encodeURIComponent(JSON.stringify(property))} data-bs-toggle="modal" data-bs-target="#modal">
        Edit Property
      </button></div>
    </div>
</div>`
}

// Carousel Card
function addCarouselData(city, address, key, latitude, longitude) {

    let image = Math.round(Math.random());
    return `<div class="col" data-property=${encodeURIComponent(JSON.stringify(key))} data-img=${image} data-lng=${longitude} data-lat=${latitude} data-desc=${JSON.stringify(address)}>
    <div class="card bg-dark text-white">
        <img src=${images[image]}
            class="card-img-top img-responsive" alt="...">
        <div class="card-body">
            <h6 class="card-title">${address}</h6>
            <p class="card-text"><small class="text-muted">Last updated ${Math.floor(Math.random() * 10) + 1} mins ago</small></p>
        </div>
    </div>
</div>`
}

// Add key/values to form for editing property
function addFormValues(property) {
    $('.form-inner').empty()
    let innerForm = ""

    for (const [key, value] of Object.entries(property)) {
        if (key != "pk" && key != "sk") {
            innerForm += `<div class="mb-3">
            <label for="${key}" class="form-label">${key}</label>
            <input type="text" class="form-control" id="${key}" placeholder="${value}">
          </div>`
        }
    }
    $('.form-inner').append(innerForm);

}

// Submit updated property to DynamoDB
async function submitEdit(property) {
    let values = {}

    Object.keys(property).forEach(key => {
        let value = $(`#${key}`).val();
        if (value != "" && value != undefined)
            values[key] = value
    })

    let obj = {
        keys: {
            "pk": property.pk,
            "sk": property.sk
        },
        data: values
    }

    fetch(API_URL + "/property-update", {
        method: "POST",
        headers: { 'Content-Type': 'application/json', 'X-Api-Key': API_KEY },
        body: JSON.stringify(obj),
    }).then(res => {
        $('#modal').modal('hide');
    }).catch(err => {
        alert(err)
    })
}

// Place marker and popups on map
async function populate(lng, lat) {

    // Remove if exists for data refresh
    if (map.getLayer("places"))
        map.removeLayer("places");

    if (map.getSource('places'))
        map.removeSource('places')

    let features = [];
    data = await fetchData(lng, lat);

    $('.center-slick').slick('removeSlide', null, null, true);

    // Loop the results and create source for Mapbox map
    data.forEach((property, i) => {
        features.push({
            'type': 'Feature',
            'id': i,
            'properties': {
                'description': property[0],
                'icon': 'castle-15'
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [property[2][0], property[2][1]]
            }
        })
        // Parse Redis Property Key to Add Detail to Carousel
        let [agencyId, agentId, city, address] = property[0].split('#')

        $('.center-slick').slick('slickAdd', addCarouselData(city, address, property[0], property[2][1], property[2][0]))
    })



    map.addSource('places', {
        'type': 'geojson',
        'data': {
            'type': 'FeatureCollection',
            'features': features
        }
    });
    // Add a layer showing the places.
    map.addLayer({
        'id': 'places',
        'type': 'circle',
        'source': 'places',
        'paint': {
            'circle-radius': 10,
            'circle-color': '#FF0000'
        }
    });

    // When a click event occurs on a feature in the places layer, open a popup at the
    // location of the feature, with description HTML from its properties.
    map.on('click', 'places', (e) => {
        // Change carousel which will invoke popup and map change
        const index = e.features[0].id;
        $('.center-slick').slick('slickGoTo', index);
    });

    // Change the cursor to a pointer when the mouse is over the places layer.
    map.on('mouseenter', 'places', () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    // Change it back to a pointer when it leaves.
    map.on('mouseleave', 'places', () => {
        map.getCanvas().style.cursor = '';
    });
}
