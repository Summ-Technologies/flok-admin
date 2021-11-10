from sqlalchemy.orm import Session
from hawk_db.lodging import Hotel, HotelToImage, Destination
from hawk_db.common import Image, ImageOrientation

class HotelManager:
    def __init__(self, session: Session, config: dict = {}):
        self.session = session
        self.config = config

    def commit_changes(self):
        self.session.commit()

    def get_hotel_by_id(self, id):
        return self.session.query(Hotel).get(id)

    def get_hotels_by_criteria(self, hotel_name=None, destination_name=None):
        """
        Search for hotels matching possibly partial name or city names (location column of destinations),
        :param hotel_name: str, optional
        :param destination_name: str, optional
        :returns: list, hotel records matching search criteria
        """
        if not (hotel_name or destination_name):
            return []

        q = self.session.query(Hotel)
        if hotel_name:
            hotel_name = '%' + hotel_name.strip('%') + '%'
            q = q.filter(Hotel.name.like(hotel_name))

        if destination_name:
            destination_name = '%' + destination_name.strip('%') + '%'
            destination_ids = self.session.query(Destination)\
                .filter(Destination.location.like(destination_name))\
                .with_entities(Destination.id)\
                .all()
            destination_ids = [x for x, in destination_ids]

            q = q.filter(Hotel.destination_id.in_(destination_ids))

        return q.all()

    def add_image(self, hotel_id: int, image_url: str, alt='', spotlight=False, portrait=False):
        """
        Add image to database and update necessary relations for hotel.
        :param hotel_id: id of hotel to add image to
        :param image_url: url where image is stored
        :param alt: alt text of image
        :param spotlight: whether the new image is the spotlight image
        :param portrait: whether the orientation is portrait or landscape
        :return: boolean, success of operation
        """
        hotel = self.session.query(Hotel).get(hotel_id)
        if not hotel:
            return False

        orientation = ImageOrientation.PORTRAIT if portrait else ImageOrientation.LANDSCAPE
        new_image = Image(image_url=image_url, alt=alt, orientation=orientation)
        self.session.add(new_image)
        self.commit_changes()

        order = self.session.query(HotelToImage).filter(HotelToImage.hotel_id == hotel_id).count()
        hotel_to_image = HotelToImage(hotel_id=hotel.id, image_id=new_image.id, order=order)
        self.session.add(hotel_to_image)
        self.commit_changes()

        if spotlight:
            hotel.spotlight_img_id = new_image.id
            hotel.spotlight_img = new_image
            self.commit_changes()

        return True