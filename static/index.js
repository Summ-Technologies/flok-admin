const ADMIN_URL = ''
let HOTEL_ID = '';
let HOTELS = [];

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

function setHotelOptions(hotels) {
    const select = $('#hotel-select');
    select.empty();
    select.append('<option value="">Choose Here</option>');
    hotels.map((hotel, i) => select.append(`<option value=${i}>${hotel.name} | ${hotel.location}</option>`));
}

function selectHotel(e) {
    const hotel = HOTELS[$('#hotel-select').val()]
    HOTEL_ID = hotel.id;
    $('#hotel-link').attr('href', hotel.link);
    $('.img-msg').each(function() {$(this).html('')});
}

function addImageInput(e) {
    const numInputs = $('.img-input').length
    $(`<div class="img-input">
        URL: <input name="url-${numInputs}" type="url"/>
        Alt text (optional): <input name="alt-${numInputs}" type="text" />
        Spotlight?<input name="spotlight-${numInputs}" type="checkbox"/>
        <div class="img-msg" id="img-${numInputs}-msg"></div>
    </div>`).appendTo('#image-inputs');
}

function uploadImages(e) {
    const data = $('#image-inputs').serializeArray();
    const numInputs = $('.img-input').length
    console.log(numInputs);
    const reqBody = {
        imgs: Array.from({length: numInputs}, () => ({url: '', alt: ''})),
        hotel_id: HOTEL_ID
    };
    console.log(reqBody);

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
    });

    reqBody.imgs = reqBody.imgs.filter(obj => obj.url != '');

    $.ajax({
        url: ADMIN_URL + '/api/images',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(reqBody),
        success: function(res) {
            Object.keys(res).map(img_id => {
                const msg = $('img-' + img_id + '-msg');
                msg.css('visibility', 'visible')
                if (res[img_id] === true) {
                    msg.text('success');
                }
                else {
                    msg.text('failure');
                }
            });
        }
    });
}