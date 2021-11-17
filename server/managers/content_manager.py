import pandas as pd
from google.oauth2 import service_account
from googleapiclient import discovery
from hawk_db.lodging import Destination, DestinationTag, Hotel, HotelTag, LodgingTag
from sqlalchemy.orm import Session, load_only


def setup_sheets_service(creds):
    credentials = service_account.Credentials.from_service_account_file(creds)
    scoped_creds = credentials.with_scopes(
        ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = discovery.build("sheets", "v4", credentials=scoped_creds)
    return service


def rename_sheets_col_for_dest(col_name):
    return (
        col_name.lower()
        .replace(" ", "_")
        .replace("(", "_")
        .replace(")", "")
        .replace("abbr", "abbreviation")
    )


hotel_cols_translations = {
    "name": "name",
    "sub location": "sub_location",
    "price / night": "price_per_night",
    "budget": "price",
    "# rooms": "num_rooms",
    "website": "website_url",
    "street address": "street_address",
    "airport_time": "airport_travel_time",
    "google rating": "rating_google",
    "description": "description",
    "description short": "description_short",
    "tag(flok recommended)": "is_flok_recommended",
    "airport time (mins)": "airport_travel_time",
}


def rename_sheets_col_for_hotel(col_name):
    col_name = col_name.lower()
    if hotel_cols_translations.get(col_name):
        col_name = hotel_cols_translations.get(col_name)
    else:
        col_name = col_name.lower().replace(" ", "_").replace("(", "_").replace(")", "")
    return col_name


class ContentManager:
    SPREADSHEET_ID = "1ZG7GAu38dnpT0Z_Cwd8g_Nun3vACdyvK6FXOYh31nlo"
    HOTEL_SHEET_NAME = "Hotels"
    DESTINATION_SHEET_NAME = "Locations"

    def __init__(self, session: Session, config: dict = {}):
        self.session = session
        self.config = config
        if config.get("GOOGLE_CREDENTIALS_PATH"):
            self.sheets_service = setup_sheets_service(
                config.get("GOOGLE_CREDENTIALS_PATH")
            )

    def commit_changes(self):
        self.session.commit()

    def get_lodging_tags(self, tag_cols):
        """
        Assumes tag_names in db are the same as the parenthesis in google sheet with '_' replacing ' ' and lowercase
        """
        tag_translations = {
            "tag_beach": "🏖️ Beach",
            "tag_urban": "🌆 Urban",
            "tag_mountains": "️⛰ Mountains",
            "tag_practical": "Practical",
            "tag_pool": "🏊 Pool",
            "tag_spa": "🛀 Spa",
            "tag_unique": "Unique",
            "tag_meeting_rooms": "🤝 Meeting rooms",
            # "tag_flok_recommended": "Flok Recommended",
        }

        tags = {}
        for tag_col in tag_cols:
            tags[tag_col] = (
                self.session.query(LodgingTag)
                .filter(LodgingTag.name == tag_translations[tag_col])
                .one()
            )
        return tags

    def update_destinations(self):
        response = (
            self.sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=ContentManager.SPREADSHEET_ID,
                range=f"'{ContentManager.DESTINATION_SHEET_NAME}'",
            )
            .execute()
        )
        sheets_df = pd.DataFrame(response["values"][1:], columns=response["values"][0])
        sheets_df = sheets_df.rename(columns=rename_sheets_col_for_dest)

        query = self.session.query(Destination)
        backend_df = pd.read_sql(query.statement, self.session.get_bind())

        id_cols = ["location", "country"]
        tag_cols = ["tag_mountains", "tag_urban", "tag_beach", "tag_practical"]
        basic_cols = [
            c
            for c in sheets_df.columns
            if not c.startswith("tag_") and c not in id_cols
        ]

        merged = sheets_df.merge(
            backend_df, on=id_cols, how="outer", indicator=True, suffixes=["", "_db"]
        )

        # TODO: remove the and clause in below expression and deal with non-bool tags
        for c in tag_cols:
            merged[c] = merged[c].apply(lambda s: True if s == "TRUE" else False)

        for c in merged.columns:
            merged[c] = merged[c].apply(
                lambda s: None if s != s else s
            )  # x != x checks for NaN values
            merged[c] = merged[c].apply(lambda s: None if s == "" else s)

        lodging_tags = self.get_lodging_tags(tag_cols)
        for idx, row in merged.iterrows():
            # new record case
            if row["location"] == None:
                continue

            if row["_merge"] == "left_only":
                d = Destination(**{c: row[c] for c in basic_cols + id_cols})
                self.session.add(d)
                self.session.flush()
                for i, (c, tag) in enumerate(lodging_tags.items()):
                    if row[c]:
                        dest_tag = DestinationTag(
                            destination_id=d.id, tag_id=tag.id, order=i
                        )
                        self.session.add(dest_tag)
                        self.session.flush()

            # possibly updated record case
            elif row["_merge"] == "both":
                db_record = self.session.query(Destination).get(row["id"])
                n_tags = (
                    self.session.query(DestinationTag)
                    .filter(DestinationTag.destination_id == db_record.id)
                    .count()
                )
                for c in basic_cols:
                    setattr(db_record, c, row[c])
                for c, tag in lodging_tags.items():
                    dest_tag = (
                        self.session.query(DestinationTag)
                        .filter(DestinationTag.destination_id == db_record.id)
                        .filter(DestinationTag.tag_id == tag.id)
                        .one_or_none()
                    )
                    if dest_tag and not row[c]:
                        self.session.delete(dest_tag)
                    elif not dest_tag and row[c]:
                        dest_tag = DestinationTag(
                            destination_id=db_record.id, tag_id=tag.id, order=n_tags
                        )
                        self.session.add(dest_tag)
                        n_tags += 1

            # TODO: what to do here? deleted record case (in db but not in sheets)
            else:
                pass

            self.commit_changes()

        return {}

    def find_dest_by_name(self, name):
        return (
            self.session.query(Destination).filter(Destination.location == name).one()
        )

    def update_hotels(self):
        response = (
            self.sheets_service.spreadsheets()
            .values()
            .get(
                spreadsheetId=ContentManager.SPREADSHEET_ID,
                range=f"'{ContentManager.HOTEL_SHEET_NAME}'",
            )
            .execute()
        )
        sheets_df = pd.DataFrame(response["values"][1:], columns=response["values"][0])
        sheets_df["destination_id"] = sheets_df["Location"].apply(
            lambda name: self.find_dest_by_name(name).id if name else ""
        )
        sheets_df = sheets_df.drop(columns=["Location"])
        sheets_df = sheets_df.rename(columns=rename_sheets_col_for_hotel)
        query = self.session.query(Hotel)
        backend_df = pd.read_sql(query.statement, self.session.get_bind())

        id_cols = ["name", "destination_id"]
        tag_cols = [
            "tag_pool",
            "tag_beach",
            "tag_spa",
            "tag_unique",
            "tag_meeting_rooms",
            # "tag_flok_recommended",
        ]
        basic_cols = list(
            filter(lambda val: val not in id_cols, hotel_cols_translations.values())
        )

        merged = sheets_df.merge(
            backend_df, on=id_cols, how="outer", indicator=True, suffixes=["", "_db"]
        )

        merged["price_per_night"] = merged["price_per_night"].apply(
            lambda p: float(p.replace(",", "")) if p else p
        )
        merged["num_rooms"] = merged["num_rooms"].apply(
            lambda p: float(p.replace(",", "")) if p else p
        )

        for c in tag_cols + ["is_flok_recommended"]:
            merged[c] = merged[c].apply(lambda s: True if s == "TRUE" else False)

        for c in merged.columns:
            merged[c] = merged[c].apply(
                lambda s: None if s != s else s
            )  # x != x checks for NaN values
            merged[c] = merged[c].apply(lambda s: None if s == "" else s)

        lodging_tags = self.get_lodging_tags(tag_cols)
        for idx, row in merged.iterrows():

            if row["name"] == None:
                continue

            # new record case
            if row["_merge"] == "left_only":
                new_hotel = Hotel(**{c: row[c] for c in basic_cols + id_cols})
                self.session.add(new_hotel)
                self.session.flush()
                for i, (c, tag) in enumerate(lodging_tags.items()):
                    if row[c]:
                        hotel_tag = HotelTag(
                            hotel_id=new_hotel.id, tag_id=tag.id, order=i
                        )
                        self.session.add(hotel_tag)
                self.session.flush()

            # possibly updated record case
            elif row["_merge"] == "both":
                db_record = self.session.query(Hotel).get(row["id"])
                for c in basic_cols:
                    setattr(db_record, c, row[c])
                n_tags = (
                    self.session.query(HotelTag)
                    .filter(HotelTag.hotel_id == db_record.id)
                    .count()
                )
                for c, tag in lodging_tags.items():
                    hotel_tag = (
                        self.session.query(HotelTag)
                        .filter(HotelTag.hotel_id == db_record.id)
                        .filter(HotelTag.tag_id == tag.id)
                        .one_or_none()
                    )
                    if hotel_tag and not row[c]:
                        self.session.delete(hotel_tag)
                    elif not hotel_tag and row[c]:
                        hotel_tag = HotelTag(
                            hotel_id=db_record.id, tag_id=tag.id, order=n_tags
                        )
                        self.session.add(hotel_tag)
                        n_tags += 1
                self.session.flush()
        self.commit_changes()
        return {}
