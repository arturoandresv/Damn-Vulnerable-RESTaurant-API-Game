import base64

import requests
from apis.menu import schemas
from db.models import MenuItem, OrderItem
from fastapi import HTTPException
from urllib.parse import urlparse


def _image_url_to_base64(image_url: str):
    parsed_url = urlparse(image_url)
    domain = parsed_url.hostname or ""

    # solo admitir 'localhost'
    allowed_domains = ["localhost", "127.0.0.1"]
    if domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="Invalid image URL domain")
    
    # admitir solo extensiones de imagen especificas
    allowed_extensions = [".jpg", ".jpeg", ".png"]
    if not parsed_url.path.lower().endswith(tuple(allowed_extensions)):
        raise HTTPException(status_code=400, detail="Invalid imagetype")

    response = requests.get(image_url, stream=True)
    content_type = response.hearders.get("content-type", "")

    # asegurar que el contenido es una imagen
    if not content_type.startswith("image"):
        raise HTTPException(status_code=400, detail="URL does not point to an image")
    
    encoded_image = base64.b64encode(response.content).decode()
    return encoded_image


def create_menu_item(
    db,
    menu_item: schemas.MenuItemCreate,
):
    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)
    db_item = MenuItem(**menu_item_dict)

    if image_url:
        db_item.image_base64 = _image_url_to_base64(image_url)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_menu_item(
    db,
    item_id: int,
    menu_item: schemas.MenuItemCreate,
):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    menu_item_dict = menu_item.dict()
    image_url = menu_item_dict.pop("image_url", None)

    for key, value in menu_item_dict.items():
        setattr(db_item, key, value)

    if image_url:
        db_item.image_base64 = _image_url_to_base64(image_url)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_menu_item(db, item_id: int):
    existing_order_item = (
        db.query(OrderItem).filter(OrderItem.menu_item_id == item_id).first()
    )
    if existing_order_item is not None:
        raise HTTPException(
            status_code=409,
            detail="You can not delete this menu item, it is associated with existing orders.",
        )

    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    db.delete(db_item)
    db.commit()
