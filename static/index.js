const ADMIN_URL = '';
let HOTEL_ID = '';
let HOTELS = [];
let DESTINATIONS = [];

function findHotels(e) {
    const data = $('#hotel-finder').serialize();
    $.get(ADMIN_URL + '/api/hotel?' + data, function(res) {
        if (!res.success) {
            alert('Could not find hotel, please try again');
            $('#hotel-finder')[0].reset();
            $('#add-images').css('visibility', 'hidden');
            setHotelOptions([]);
            HOTELS = [];
            return;
        }
        HOTELS = res.hotels;
        setHotelOptions(res.hotels);
        $('#add-images').css('visibility', 'visible');
    });
    return false;
}

function findDestinations(e) {
    $.get(ADMIN_URL + "/api/destinations", function (res) {
        const destinations = $("#hotel-location-input")
        destinations.empty()
        destinations.append('<option value="">Choose Destination</option>');
        DESTINATIONS = res.destinations;
        DESTINATIONS.sort(function (a, b) {
            return a.location < b.location
        })
        DESTINATIONS.map((val) => destinations.append(`<option value="${val.id}">${val.name}</option>`));
    })
}

function setHotelOptions(hotels) {
    const select = $('#hotel-select');
    select.empty();
    select.append('<option value="">Choose Here</option>');
    hotels.map((hotel, i) => select.append(`<option value=${i}>${hotel.name} | ${hotel.location}</option>`));
}

function selectHotel(e) {
    const hotel = HOTELS[$('#hotel-select').val()]
    HOTEL_ID = hotel.id;
    $('#hotel-link').attr('href', `/images.html?id=${hotel.id}`);
    $('.img-msg').each(function() {$(this).html('')});
}

function addImageInput(e) {
    const numInputs = $('.img-input').length
    $(`<div class="img-input py-2 border-bottom">
        <div class="d-flex flex-wrap justify-content-center row-gutters">
        <div>
        URL: <input name="url-${numInputs}" type="url"/>
        </div>
        <div>
        Alt text (optional): <input name="alt-${numInputs}" type="text" />
        </div>
        <div>
        Tag: 
        <select name="tag-${numInputs}">
            <option value="MISCELLANEOUS" selected>Misc.</option>
            <option value="MEETING_SPACE">Meeting space</option>
            <option value="HOTEL_ROOMS">Hotel rooms</option>
            <option value="BUILDING_EXTERIOR">Building exterior</option>
            <option value="OUTDOOR_SPACES">Hotel outdoor (landscape, etc.)</option>
            <option value="INTERIOR_COMMON_SPACES">Hotel common space (interior)</option>
            <option value="DINING_SPACE">Dining space</option>
            <option value="HOTEL_POOL">Pool</option>
            <option value="HOTEL_SPA">Spa</option>
            <option value="HOTEL_GYM">Gym</option>
        </select>
        </div>
        <div>
        Spotlight?<input name="spotlight-0" type="checkbox" class="mx-1"/>
        </div>
        </div>
        <div class="img-msg" id="img-${numInputs}-msg"></div>
    </div>`).appendTo('#image-inputs');
}

function clearImages() {
    const imgInputs = $('#image-inputs')
    imgInputs.empty()
    $(`<div class="img-input py-2 border-bottom">
        <div class="d-flex flex-wrap justify-content-center row-gutters">
        <div>
        URL: <input name="url-0" type="url"/>
        </div>
        <div>
        Alt text (optional): <input name="alt-0" type="text" />
        </div>
        <div>
        Tag: 
        <select name="tag-0">
            <option value="MISCELLANEOUS" selected>Misc.</option>
            <option value="MEETING_SPACE">Meeting space</option>
            <option value="HOTEL_ROOMS">Hotel rooms</option>
            <option value="BUILDING_EXTERIOR">Building exterior</option>
            <option value="OUTDOOR_SPACES">Hotel outdoor (landscape, etc.)</option>
            <option value="INTERIOR_COMMON_SPACES">Hotel common space (interior)</option>
            <option value="DINING_SPACE">Dining space</option>
            <option value="HOTEL_POOL">Pool</option>
            <option value="HOTEL_SPA">Spa</option>
            <option value="HOTEL_GYM">Gym</option>
        </select>
        </div>
        <div>
        Spotlight?<input name="spotlight-0" type="checkbox" class="mx-1"/>
        </div>
        </div>
        <div class="img-msg" id="img-0-msg"></div>`).appendTo('#image-inputs');
}

function uploadImages(e) {
    const data = $('#image-inputs').serializeArray();
    const numInputs = $('.img-input').length
    console.log(numInputs);
    const reqBody = {
        imgs: Array.from({length: numInputs}, () => ({url: '', alt: '', tag: ''})),
        hotel_id: HOTEL_ID
    };

    data.forEach(next => {
        const img_info = {};
        const idx = parseInt(next.name.substr(-1));
        reqBody.imgs[idx].id = idx;

        if (next.name.startsWith('url')) {
            reqBody.imgs[idx].url = next.value;
        }
        else if (next.name.startsWith('alt')) {
            reqBody.imgs[idx].alt = next.value;
        }
        else if (next.name.startsWith('spotlight') && next.value === 'on') {
            reqBody.spotlight_idx = idx;
        }
        else if (next.name.startsWith('tag')) {
            reqBody.imgs[idx].tag = next.value;
        }
    });

    reqBody.imgs = reqBody.imgs.filter(obj => obj.url != '');
    setLoading(true)
    $.ajax({
        url: ADMIN_URL + '/api/images',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(reqBody),
        success: function(res) {
            setLoading(false)
            Object.keys(res).map(img_id => {
                const msg = $('#img-' + img_id + '-msg');
                msg.css('visibility', 'visible')
                if (res[img_id] === true) {
                    msg.text('success');
                }
                else {
                    msg.text('failure');
                }
            });
        },
        error: function(res) {
            setLoading(false)
            alert('there was an error uploading the images')
        }
    });
}

function setLoading(isLoading) {
    let button = $("#upload-btn")
    if (isLoading) {
        button.attr('disabled', 'disabled')
        button.html('<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>')
    } else {
        button.removeAttr('disabled')
        button.html('Upload')
    }
}

$(document).ready(() => {
    findDestinations()
})