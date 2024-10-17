from flask import Flask, jsonify, request
from neo4j import GraphDatabase


app = Flask(__name__) #instansiere flask applikasjon

uri = "bolt://localhost:7687" #setter localhost adresse og kobler til Neo4j
neo4j_user = "neo4j" #navn for neo4j bruker
neo4j_password = "12345678" #passord #lat som at jeg ikke er dum og bare skriver det rett inn

driver = GraphDatabase.driver(uri, auth=(neo4j_user, neo4j_password)) #lage driveren

# funksjon til å lukke driveren etter session er over
def close_driver():
    driver.close()

@app.route('/')
def index():
    return jsonify({"message": "Welcome to dumb rent car thing!!!!"})

# Check Neo4j connection route
@app.route('/check-neo4j', methods=['GET'])
def check_neo4j():
    with driver.session() as session: # Lage session med neo4j, for å hente/endre etc, requests
        result = session.run("RETURN 'Connection successful' AS message") # Cypher query
        record = result.single() # finner første rad (eneste) rad av resultatet (son dict)
        message = record["message"] # finner verdien fra dict key record
        return jsonify({"message": message}) #omgjør til json




# CARS -----------------------------------------------------------------------------

@app.route('/cars', methods=['POST']) # create car instance
def add_car():

    data = request.get_json() # behandle data fra post request, gjør om til dict
    make = data['make'] # sette variabler for data fra post, til python
    model = data['model']
    year = data['year']
    location = data['location']
    availability = data['status']

    with driver.session() as session: # starte session med neo4j
        # lage ny eller merge node med data fra dict
        # ON CREATE = dersom ny lages, legger til c. til laget node
        session.run("""
            MERGE (c:Car {make: $make, model: $model, year: $year})
            ON CREATE SET c.location = $location, c.availability = $availability
            """, make=make, model=model, year=year, location=location, availability=availability)

    return jsonify({"message": "Car added successfully!"}), 201

@app.route('/cars', methods=['GET']) # view all car instances
def retrieve_car():

    with driver.session() as session:
        result = session.run('MATCH (c:Car) RETURN c') # return iterable table of all nodes marked 'car'

        cars = [] # empty list to add result into

        for record in result: # iterate through result item

            car_node = record['c'] # find the next node for car

            car_data = { # extract all data from car node
                'make': car_node['make'],
                'model': car_node['model'],
                'year': car_node['year'],
                'location': car_node['location'],
                'availability': car_node['availability']
            }

            cars.append(car_data) # add all data to list

    return jsonify(cars) # return jsonified data to client


@app.route('/cars', methods=['PATCH'])
def update_car(value,update):
    pass

# helper function
def find_car(make, model, year):

    with driver.session() as session:
        result = session.run("""
                MATCH (c:Car {make: $make, model: $model, year: $year})
                RETURN c
            """, make=make, model=model, year=year)

        car = result.single()

        if car:

            car_node = car['c']

            car_data = {  # extract all data from car node
                'make': car_node['make'],
                'model': car_node['model'],
                'year': car_node['year'],
                'location': car_node['location'],
                'availability': car_node['availability']
                }

            return jsonify(car_data)

        else:
            return jsonify({'error':'car not found'}), 404



# CUSTOMERS --------------------------------------------------------------------------------------------------


# ensure Neo4j driver is closed on app shutdown
@app.teardown_appcontext
def shutdown_session(exception=None):
    close_driver()

# sørge for å kjøre hovedsession, og ikke importerte/andre prosesser
# bruker debug mode
if __name__ == "__main__":
    app.run(debug=True, port=5001) #finner på: http://127.0.0.1:5001/
