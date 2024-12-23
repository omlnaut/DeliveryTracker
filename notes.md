# Key vault setup
Follow https://www.youtube.com/watch?v=Vs3wyFk9upo

# Deployment
Befure running the line below, start the azurite blob service (bottom right shows azurite extension)
OLD: Need to run `func host start` in the terminal, then go "deploy functions" in azure extension (local workspace).
NEW: Click on Workspace -> Functions -> "start debugging ..." in the azure extension.


# EventGrid
- Create topic
- create and deploy function that is triggered by eventgrid
    - connection settings as environment variables in function app
- In azure portal, create subscription to topic with deployed function as endpoint