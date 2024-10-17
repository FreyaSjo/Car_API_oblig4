from flask import Flask, jsonify, request
from neo4j import GraphDatabase


# SYSTEM -----------------------------------------------------------------------------------------------------
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
    car_id = data['car_id']
    make = data['make'] # sette variabler for data fra post, til python
    model = data['model']
    year = data['year']
    location = data['location']
    availability = data['availability']

    exists = find_car(car_id)

    if exists:
        return jsonify({'message': 'denne finnes allerede, tulling :l'}), 200

    with driver.session() as session: # starte session med neo4j
        # lage ny eller merge node med data fra dict
        # ON CREATE = dersom ny lages, legger til c. til laget node
        session.run("""
            MERGE (c:Car {car_id: $car_id})
            ON CREATE SET c.location = $location, c.availability = $availability, c.make = $make, c.model = $model, c.year = $year
            """,car_id=car_id, make=make, model=model, year=year, location=location, availability=availability)

    return jsonify({"message": "Car added successfully!"}), 201

@app.route('/cars', methods=['GET']) # view all car instances
def retrieve_car():

    with driver.session() as session:
        result = session.run('MATCH (c:Car) RETURN c') # return iterable table of all nodes marked 'car'

        cars = [] # empty list to add result into

        for record in result: # iterate through result item

            car_node = record['c'] # find the next node for car

            car_data = { # extract all data from car node
                'car_id': car_node['car_id'],
                'make': car_node['make'],
                'model': car_node['model'],
                'year': car_node['year'],
                'location': car_node['location'],
                'availability': car_node['availability']
            }

            cars.append(car_data) # add all data to list

    return jsonify(cars) # return jsonified data to client

@app.route('/cars', methods=['PATCH']) # update car info
def update_car():

    data = request.get_json()
    car_id = data['car_id']
    make = data['make']
    model = data['model']
    year = data['year']
    location = data['location']
    availability = data['availability']

    with driver.session() as session:
        result = session.run("""
            MATCH (c:Car {car_id: $car_id})
            RETURN c
        """, car_id=car_id)

    car = result.single()

    if car:
        session.run("""
            MATCH (c:Car {car_id: $car_id})
            SET c.location = $location, c.availability = $availability, c.make = $make, c.model = $model, c.year = $year
        """, car_id=car_id, make=make, model=model, year=year, availability=availability, location=location)

        return jsonify({'message':'car new:)'}), 200

    else:
        return jsonify({'message':'no car!!!!!:o'}), 404

@app.route('/cars', methods=['DELETE']) # delete car instance
def remove_car():

    data = request.get_json()
    car_id = data['car_id']

    exists = find_car(car_id)

    if exists:
        with driver.session() as session:
            session.run("""
                MATCH (c:Car {car_id: $car_id})
                DELETE c
                """, car_id=car_id)

        return jsonify({"message": "Car removed successfully!"}), 204

    else:
        return jsonify({'message':'no car bby:('}), 404

# helper function
def find_car(car_id): #find specific car

    with driver.session() as session:
        result = session.run("""
                MATCH (c:Car {car_id: $car_id})
                RETURN c
            """, car_id=car_id)

        car = result.single()

        if car:

            car_node = car['c']

            car_data = {  # extract all data from car node
                'car_id': car_node['car_id'],
                'make': car_node['make'],
                'model': car_node['model'],
                'year': car_node['year'],
                'location': car_node['location'],
                'availability': car_node['availability']
                }

            return car_data

        else:
            return None



# CUSTOMERS --------------------------------------------------------------------------------------------------

@app.route('/customer', methods=['POST']) # create customer instance
def add_customer():

    data = request.get_json()
    customer_id = data['customer_id']
    name = data['name']
    age = data['age']
    adress = data['adress']

    exists = find_customer(customer_id)

    if exists:
        return jsonify({'message': 'denne finnes allerede, tulling :l'}), 200

    with driver.session() as session:
        session.run("""
                MERGE (cus:Customer {customer_id: $customer_id})
                ON CREATE SET c.name = $name, c.age = $age, c.adress = $adress
                """, customer_id=customer_id, name=name, age=age, adress=adress)

    return jsonify({"message": "Customer added successfully!"}), 201



def find_customer(customer_id): #find specific customer

    with driver.session() as session:
        result = session.run("""
                MATCH (cus:Customer {customer_id: $customer_id})
                RETURN cus
            """, customer_id=customer_id)

        customer = result.single()

        if customer:

            customer_node = customer['cus']

            customer_data = {  # extract all data from car node
                'customer_id': customer_node['customer_id'],
                'name': customer_node['name'],
                'age': customer_node['age'],
                'adress': customer_node['adress']
                }

            return customer_data

        else:
            return None


# SYSTEM -----------------------------------------------------------------------------------------------------
# ensure Neo4j driver is closed on app shutdown
@app.teardown_appcontext
def shutdown_session(exception=None):
    close_driver()

# sørge for å kjøre hovedsession, og ikke importerte/andre prosesser
# bruker debug mode
if __name__ == "__main__":
    app.run(debug=True, port=5001) #finner på: http://127.0.0.1:5001/
