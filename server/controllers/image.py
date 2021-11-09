import boto3 as boto3
from botocore.exceptions import ClientError
from .. import app, hotel_manager
from PIL import Image
import requests
from io import BytesIO
from flask import request, jsonify
import uuid


@app.route('/images', methods=['POST'])
def add_images():
    """
    upload images from url to s3 bucket and save to database with correct hotel relations.
    request data structure -
    {
        spotlight_idx: int. index within list of images of new spotlight image. optional
        hotel_id: int. id of the hotel to add images to. required
        imgs: [
            {
                id: int, id of image for frontend use. required
                url: str. url of image to download. required
                alt: str. alt text for image. optional
            }, ...
        ]. required
    }
    returns -
    {
        <image-id>: boolean, map of whether each image url was uploaded successfully or not
    }
    """
    SPOTLIGHT_SIZE = (400, 400)
    GALLERY_SIZE = (1000, 1000)

    app.logger.info('fuck this')

    data = request.get_json(force=True)

    spotlight_idx = data.get('spotlight_idx', -1)

    hotel_id = data.get('hotel_id', None)
    if hotel_id is None:
        return "No Hotel ID provided", 400
    hotel = hotel_manager.get_hotel_by_id(hotel_id)
    
    successes = {}
    for i, img_obj in enumerate(data.get('imgs', [])):
        url = img_obj.get('url', '')
        alt = img_obj.get('alt', '')
        img_id = img_obj.get('id', -1)

        if img_id == -1 or not url:
            return 'Each image must have an id.', 400
        if not url:
            return 'Each image must have a url.', 400

        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
        except:
            successes[img_id] = False
            continue

        if img_id == spotlight_idx:
            img = resize_img(img, SPOTLIGHT_SIZE)
        else:
            img = resize_img(img, GALLERY_SIZE)

        s3_url = upload_img(img, url, hotel.name)
        if not s3_url:
            successes[img_id] = False
            continue

        w, h = img.size
        successes[img_id] = hotel_manager.add_image(hotel_id, s3_url, alt, spotlight_idx == i, h >= w)

    response = jsonify(successes)
    return response


def resize_img(img, dims):
    """
    resizes image to less than or equal to dims, and maintains its aspect ratio by cropping after resizing one dimension when necessary.
    Parameters - 
    img - PIL.Image
    dims - (w, h)
    Returns - 
    PIL.Image
    >>> img = Image.open(BytesIO(requests.get('https://jacob-hanson.com/static/media/collage.a72a9f48.jpg').content))
    >>> new = resize_img(img, (400, 400))
    >>> new.size[0] <= 400 and new.size[1] <= 400
    True
    >>> new.save('resize_test.jpg')
    """
    ow, oh = img.size
    tw, th = dims
    format = img.format

    if ow <= tw and oh <= th:
        return img
    elif oh <= ow:
        img = img.resize((tw, int(oh * tw / ow)))
    else:
        img = img.resize((int(ow * th / oh), th))

    img.format = format
    return img


def upload_img(img, orig_url, hotel_name):
    """
    uploads img to s3 bucket and returns new url.
    >>> url = 'https://jacob-hanson.com/static/media/collage.a72a9f48.jpg'
    >>> img = Image.open(BytesIO(requests.get(url).content))
    >>> s3_url = upload_img(img, url, 'TEST')
    >>> s3_url != False
    True
    """
    bucket = "flok-b32d43c"
    uuid_str = str(uuid.uuid4())[0:8]
    ext = orig_url.split('.')[-1]
    obj_name = f'hotels-test/{hotel_name.strip().replace(" ", "-").lower()}/{uuid_str}.{ext}'
    s3_client = boto3.client('s3')

    in_mem_img = BytesIO()
    img.save(in_mem_img, format=img.format)
    in_mem_img.seek(0)

    try:
        s3_client.upload_fileobj(in_mem_img, bucket, obj_name, ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        return False
    return f'https://{bucket}.s3.amazonaws.com/{obj_name}'