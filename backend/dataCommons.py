import datacommons_client.client as dc
import os
import dotenv

api_key = os.getenv("DATA_COMMONS_KEY")
client = dc.DataCommonsClient(api_key)

# Fact-checking a claim about US home ownership trends
df = client.observations_dataframe(
    variable_dcids=["Count_HousingUnit_OwnerOccupied"],
    entity_dcids=["country/USA"],
    date=""
)

# Sorting by date to see the trend
print(df.sort_values(by='date'))