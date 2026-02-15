import datacommons_client.client as dc
import os
import dotenv

api_key = os.getenv("DATA_COMMONS_KEY")
client = dc.DataCommonsClient(api_key)


df = client.observations_dataframe(
    variable_dcids=["Count_HousingUnit_OwnerOccupied"],
    entity_dcids=["country/USA"],
    date=""
)


print(df.sort_values(by='date'))