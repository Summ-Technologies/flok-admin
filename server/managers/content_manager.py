from google.oauth2 import service_account
from googleapiclient import discovery
from hawk_db.lodging import Destination, Hotel, LodgingTag, HotelTag, DestinationTag
from sqlalchemy.orm import Session
import pandas as pd


def setup_sheets_service():
    credentials = service_account.Credentials.from_service_account_file('google_credentials.json')
    scoped_creds = credentials.with_scopes(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    service = discovery.build("sheets", "v4", credentials=scoped_creds)
    return service


def rename_sheets_col_for_dest(col_name):
    return col_name.lower().replace(' ', '_').replace('(', '_').replace(')', '').replace('abbr', 'abbreviation')


class ContentManager:
    SPREADSHEET_ID = '1ZG7GAu38dnpT0Z_Cwd8g_Nun3vACdyvK6FXOYh31nlo'
    HOTEL_SHEET_NAME = 'Hotels'
    DESTINATION_SHEET_NAME = 'Locations'

    def __init__(self, session: Session, config: dict = {}):
        self.session = session
        self.config = config
        self.sheets_service = setup_sheets_service()

    def commit_changes(self):
        self.session.commit()

    def get_lodging_tags(self, tag_names):
        """
        Assumes tag_names in db are the same as the parenthesis in google sheet with '_' replacing ' ' and lowercase
        """
        return self.session.query(LodgingTag).filter(LodgingTag.name.in_(tag_names)).all()

    def update_destinations(self):
        response = self.sheets_service.spreadsheets().values().get(spreadsheetId=ContentManager.SPREADSHEET_ID,
                                        range=f"'{ContentManager.DESTINATION_SHEET_NAME}'").execute()
        sheets_df = pd.DataFrame(response['values'][1:], columns=response['values'][0])
        sheets_df = sheets_df.rename(columns=rename_sheets_col_for_dest)

        query = self.session.query(Destination)
        backend_df = pd.read_sql(query.statement, self.session.get_bind())

        id_cols = ['location', 'country']
        merged = sheets_df.merge(backend_df, on=id_cols, how='outer', indicator=True, suffixes=['', '_db'])

        basic_cols = [c for c in sheets_df.columns if not c.startswith('tag_') and c not in id_cols]
        # TODO: remove the and clause in below expression and deal with non-bool tags
        tag_cols = [c for c in sheets_df.columns if c.startswith('tag_') and (sheets_df[c][0] == 'TRUE' or sheets_df[c][0] == 'FALSE')]
        for c in tag_cols:
            merged[c] = merged[c].apply(lambda s: True if s == 'TRUE' else False)

        lodging_tags = self.get_lodging_tags([t[4:] for t in tag_cols])
        for idx, row in merged.iterrows():
            # new record case
            if row['_merge'] == 'left_only':
                d = Destination(**{c: row[c] for c in basic_cols + id_cols})
                self.session.add(d)
                self.commit_changes()
                for i, (c, tag) in enumerate(zip(tag_cols, lodging_tags)):
                    if row[c]:
                        dest_tag = DestinationTag(d.id, tag_id=tag.id, order=i)
                        self.session.add(dest_tag)
                self.commit_changes()

            # possibly updated record case
            elif row['_merge'] == 'both':
                db_record = self.session.query(Destination).get(row['id'])
                n_tags = self.session.query(DestinationTag).filter(DestinationTag.destination_id == db_record.id).count()
                for c in basic_cols:
                    setattr(db_record, c, row[c])
                for c, tag in zip(tag_cols, lodging_tags):
                    dest_tag = self.session.query(DestinationTag).get((db_record.id, tag.id))
                    if dest_tag and not row[c]:
                        self.session.delete(dest_tag)
                    elif not dest_tag and row[c]:
                        dest_tag = DestinationTag(destination_id=db_record.id, tag_id=tag.id, order=n_tags)
                        self.session.add(dest_tag)
                        n_tags += 1
                self.commit_changes()

            #TODO: what to do here? deleted record case (in db but not in sheets)
            else:
                pass

        return {}

    def find_dest_by_name(self, name):
        return self.session.query(Destination).filter(Destination.location == name).first()

    def update_hotels(self):
        response = self.sheets_service.spreadsheets().values().get(spreadsheetId=ContentManager.SPREADSHEET_ID,
                                        range=f"'{ContentManager.HOTEL_SHEET_NAME}'").execute()
        sheets_df = pd.DataFrame(response['values'][1:], columns=response['values'][0])
        sheets_df['destination_id'] = sheets_df['Location'].apply(lambda name: self.find_dest_by_name(name).id)
        sheets_df = sheets_df.drop(columns=['Location'])
        sheets_df = sheets_df.rename(columns={

        })

        query = self.session.query(Hotel)
        backend_df = pd.read_sql(query.statement, self.session.get_bind())

        id_cols = ['name', 'destination_id']
        merged = sheets_df.merge(backend_df, on=id_cols, how='outer', indicator=True, suffixes=['', '_db'])

