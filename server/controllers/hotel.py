from flask import request, jsonify
from .. import app, hotel_manager


@app.route("/hotel", methods=["get"])
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
    name = request.args.get('name', None)
    destination = request.args.get('destination', None)

    if not (name or destination):
        return 'No search criteria provided.', 400

    hotels = hotel_manager.get_hotels_by_criteria(name, destination)

    hotels = [{
        'link': 'https://app.goflok.com/r/92c3b8c6-7b65-4213-9921-54970a675a3f/hotels/' + str(h.guid),
        'name': h.name,
        'location': h.street_address,
        'id': h.id
    } for h in hotels]

    response = jsonify({
        'hotels': hotels,
        'success': len(hotels) != 0,
    })
    return response