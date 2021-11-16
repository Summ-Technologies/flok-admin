from flask import jsonify, request

from .. import app, db
from ..managers.hotel_manager import *
from ..managers.content_manager import *

hotel_manager = HotelManager(db.session, app.config)
content_manager = ContentManager(db.session, app.config)


@app.route('/api/update_destinations', methods=['GET'])
def update_destinations():
    return content_manager.update_destinations()


@app.route("/api/destinations", methods=["get"])
def destinations():
    """
    get all available destinations
    returns -
    {
        destinations: [
            {
                name: name of destinations
                id: id of destination
            }
            , ...
        ]
    }
    """
    return jsonify(
        {
            "destinations": list(
                map(
                    lambda dest: {
                        "name": f"{dest.location}, {dest.country_abbreviation}",
                        "id": dest.id,
                    },
                    db.session.query(Destination).all(),
                )
            )
        }
    )


@app.route("/api/hotel", methods=["get"])
def hotel():
    """
    find all matching hotels by name, destination, or both.
    query args -
        - name: str, possibly partial name of hotel to find matches for.
        - destination: full name of location (city) to find all hotels for.
    returns -
    {
        hotels: [
            {
                link: link to page showing hotel info
                name: name of hotel
                id: id of hotel
                location: street address of hotel
            }, ...
        ]
        success: boolean, whether the query was good or not
    """
    name = request.args.get("name", None)
    destination = request.args.get("destination", None)

    if not (name or destination):
        return "No search criteria provided.", 400

    hotels = hotel_manager.get_hotels_by_criteria(name, destination)

    hotels = [
        {
            "link": "https://app.goflok.com/r/92c3b8c6-7b65-4213-9921-54970a675a3f/hotels/"
            + str(h.guid),
            "name": h.name,
            "location": h.street_address,
            "id": h.id,
        }
        for h in hotels
    ]

    response = jsonify(
        {
            "hotels": hotels,
            "success": len(hotels) != 0,
        }
    )
    return response


@app.route("/api/hotel/<int:id>", methods=["get"])
def hotel_by_id(id):
    """
    get hotel by id
    """
    hotel = hotel_manager.get_hotel_by_id(id)
    if hotel:
        hotel = {
            "link": "https://app.goflok.com/r/92c3b8c6-7b65-4213-9921-54970a675a3f/hotels/"
            + str(hotel.guid),
            "name": hotel.name,
            "location": hotel.street_address,
            "id": hotel.id,
            "imgs": list(map(lambda img: img.image_url, hotel.imgs)),
            "spotlight_img": hotel.spotlight_img.image_url,
        }
    return jsonify({"hotel": hotel, "success": hotel != None})
