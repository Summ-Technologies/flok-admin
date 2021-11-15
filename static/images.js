const ADMIN_URL = ''

function getHotel() {
    var urlParams = new URLSearchParams(window.location.search);
    let hotelId = urlParams.get('id');
    $.get(ADMIN_URL + '/api/hotel/' +  hotelId, function(res) {
        if (!res.success) {
            alert('error getting hotel');
            return
        }
        $("#hotel-name").text(res.hotel.name);
        
        $("#images").empty()
        $(`<div class="row"><div class="col-md-6 mx-auto">Spotlight Image:</div></div>`).appendTo(
            "#images"
        )
        $(`<div class="row"><div class="col-md-6 mx-auto"><img src="${res.hotel.spotlight_img}" class="img-fluid my-2" /></div></div>`).appendTo(
            "#images"
        )
        res.hotel.imgs.map((url) => {
            $(`<div class="row"><div class="col-md-6 mx-auto"><img src="${url}" class="img-fluid my-2" /></div></div>`).appendTo(
                "#images"
            )
        })
    })
}

$(document).ready(() => {
    getHotel()
})