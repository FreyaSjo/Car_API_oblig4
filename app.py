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
    return jsonify({"message": "Welcome car rental"})

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
        return jsonify({'message': 'car with this ID already exists'}), 409

    with driver.session() as session: # starte session med neo4j
        # lage ny eller merge node med data fra dict
        # ON CREATE = dersom ny lages, legger til c. til laget node
        session.run("""
            MERGE (c:Car {car_id: $car_id})
            ON CREATE SET c.location = $location, c.availability = $availability, c.make = $make, c.model = $model, c.year = $year
            """,car_id=car_id, make=make, model=model, year=year, location=location, availability=availability)

    return jsonify({"message": "Car added successfully"}), 201

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

        return jsonify({'message':'updated car info'}), 200

    else:
        return jsonify({'message':'car not found'}), 404

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

        return jsonify({"message": "Car removed successfully"}), 204

    else:
        return jsonify({'message':'car not found'}), 404

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
    status = data['status']

    exists = find_customer(customer_id)

    if exists:
        return jsonify({'message': 'customer with this ID already exists'}), 409

    with driver.session() as session:
        session.run("""
                MERGE (cus:Customer {customer_id: $customer_id})
                ON CREATE SET cus.name = $name, cus.age = $age, cus.adress = $adress, cus.status = $status
                """, customer_id=customer_id, name=name, age=age, adress=adress, status=status)

    return jsonify({"message": "Customer added successfully"}), 201

@app.route('/customer', methods=['GET']) # view all customer instances
def retrieve_customer():

    with driver.session() as session:
        result = session.run('MATCH (cus:Customer) RETURN cus')

        customers = []

        for record in result:

            customer_node = record['cus']

            customer_data = {
                'customer_id': customer_node['customer_id'],
                'name': customer_node['name'],
                'age': customer_node['age'],
                'adress': customer_node['adress'],
                'status': customer_node['status']
            }

            customers.append(customer_data)

    return jsonify(customers)

@app.route('/customer', methods=['PATCH']) # update customer info
def update_customer():

    data = request.get_json()
    customer_id = data['customer_id']
    name = data['name']
    age = data['age']
    adress = data['adress']
    status = data['status']

    with driver.session() as session:
        result = session.run("""
            MATCH (cus:Customer {customer_id: $customer_id})
            RETURN cus
        """, customer_id=customer_id)

    customer = result.single()

    if customer:
        session.run("""
            MATCH (cus:Customer {customer_id: $customer_id})
            SET cus.name = $name, cus.age = $age, cus.adress = $adress, cus.status = $status
                """, customer_id=customer_id, name=name, age=age, adress=adress, status=status)

        return jsonify({'message':'customer info updated'}), 200

    else:
        return jsonify({'message':'customer not found'}), 404

@app.route('/customer', methods=['DELETE']) # delete customer instance
def remove_customer():

    data = request.get_json()
    customer_id = data['customer_id']

    exists = find_customer(customer_id)

    if exists:
        with driver.session() as session:
            session.run("""
                MATCH (cus:Customer {customer_id: $customer_id})
                DELETE cus
                """, customer_id=customer_id)

        return jsonify({"message": "Customer removed successfully"}), 204

    else:
        return jsonify({'message':'customer not found:('}), 404

# helper function
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
                'adress': customer_node['adress'],
                'status': customer_node['status']
                }

            return customer_data

        else:
            return None



# EMPLOYEES --------------------------------------------------------------------------------------------------

@app.route('/employee', methods=['POST']) # create employee instance
def add_employee():

    data = request.get_json()
    employee_id = data['employee_id']
    name = data['name']
    age = data['age']
    adress = data['adress']
    branch = data['branch']

    exists = find_employee(employee_id)

    if exists:
        return jsonify({'message': 'employee with this ID already exists'}), 409

    with driver.session() as session:
        session.run("""
                MERGE (e:Employee {employee_id: $employee_id})
                ON CREATE SET e.name = $name, e.age = $age, e.adress = $adress, e.branch = $branch
                """, employee_id=employee_id, name=name, age=age, adress=adress, branch=branch)

    return jsonify({"message": "Employee added successfully"}), 201

@app.route('/employee', methods=['GET']) # view all employee instances
def retrieve_employee():

    with driver.session() as session:
        result = session.run('MATCH (e:Employee) RETURN e')

        employees = []

        for record in result:

            employee_node = record['e']

            employee_data = {
                'employee_id': employee_node['employee_id'],
                'name': employee_node['name'],
                'age': employee_node['age'],
                'adress': employee_node['adress'],
                'branch': employee_node['branch']
            }

            employees.append(employee_data)

    return jsonify(employees)

@app.route('/employee', methods=['PATCH']) # update employee info
def update_employee():

    data = request.get_json()
    employee_id = data['employee_id']
    name = data['name']
    age = data['age']
    adress = data['adress']
    branch = data['branch']

    with driver.session() as session:
        result = session.run("""
            MATCH (e:Employee {employee_id: $employee_id})
            RETURN e
        """, employee_id=employee_id)

    employee = result.single()

    if employee:
        session.run("""
            MATCH (e:Employee {employee_id: $employee_id})
            SET e.name = $name, e.age = $age, e.adress = $adress, e.branch = $branch
                """, employee_id=employee_id, name=name, age=age, adress=adress, branch=branch)

        return jsonify({'message':'employee info updated'}), 200

    else:
        return jsonify({'message':'employee not found'}), 404

@app.route('/employee', methods=['DELETE']) # delete employee instance
def remove_employee():

    data = request.get_json()
    employee_id = data['employee_id']

    exists = find_employee(employee_id)

    if exists:
        with driver.session() as session:
            session.run("""
                MATCH (e:Employee {employee_id: $employee_id})
                DELETE e
                """, employee_id=employee_id)

        return jsonify({"message": "employee removed successfully"}), 204

    else:
        return jsonify({'message':'employee not found'}), 404

# helper function
def find_employee(employee_id): #find specific employee

    with driver.session() as session:
        result = session.run("""
                MATCH (e:Employee {employee_id: $employee_id})
                RETURN e
            """, employee_id=employee_id)

        employee = result.single()

        if employee:

            employee_node = employee['e']

            employee_data = {
                'employee_id': employee_node['employee_id'],
                'name': employee_node['name'],
                'age': employee_node['age'],
                'adress': employee_node['adress'],
                'branch': employee_node['branch']
            }

            return employee_data

        else:
            return None


# INTERACTION ------------------------------------------------------------------------------------------------

@app.route('/order_car', methods=['GET','PATCH']) #order car
def order_car():

    data = request.get_json()
    customer_id = data['customer_id']
    car_id = data['car_id']

    car_exist = find_car(car_id)
    customer_exist = find_customer(customer_id)

    if not car_exist:
        return jsonify({'message':'car not found'}), 404

    if car_exist['availability'].lower() != 'available':
        return jsonify({'message':'car not available for rental'}), 409

    if not customer_exist:
        return jsonify({'message':'customer not found'}), 404

    if customer_exist['status'] != 'available':
        return jsonify({'message':'customer already rents a car'}), 409


    rented = 'rents car '+str(car_id)
    rented_by = 'rented by customer '+str(customer_id)

    with driver.session() as session:
        session.run("""
            MATCH (cus:Customer {customer_id: $customer_id})
            SET cus.status=$status
        """, customer_id=customer_id, status=rented)

        session.run("""
            MATCH (c:Car {car_id: $car_id})
            SET c.availability=$availability
        """, car_id=car_id, availability=rented_by)

    return jsonify({'message':'car '+ str(car_id)+' rented by customer '+ str(customer_id)+' successfully'}), 200

@app.route('/return_car', methods=['GET', 'PATCH']) #return car
def return_car():

    data = request.get_json()
    car_id = data['car_id']
    customer_id = data['customer_id']
    state = data['state']

    car_exist = find_car(car_id)
    customer_exist = find_customer(customer_id)

    if not car_exist:
        return jsonify({'message':'car not found'}), 404

    if car_exist['availability'].lower() == 'available':
        return jsonify({'message':'car not rented'}), 409

    if not customer_exist:
        return jsonify({'message':'customer not found'}), 404

    if customer_exist['status'].lower() == 'available':
        return jsonify({'message':'customer not registered to a car'}), 409

    if state.lower() != 'ok':
        state = 'damaged'
        status = 'barred'
    else:
        state = 'available'
        status = 'available'

    with driver.session() as session:
        session.run("""
            MATCH (c:Car {car_id: $car_id})
            SET c.availability = $availability
        """,car_id = car_id, availability = state)

        session.run("""
            MATCH (cus:Customer {customer_id: $customer_id})
            SET cus.status = $status
        """, customer_id = customer_id, status = status)

    return jsonify({'message':'car '+str(car_id)+' returned by customer '+str(customer_id)}), 200

@app.route('/cancel_car_order', methods=['GET', 'PATCH']) #cancel order
def cancel_car():

    data = request.get_json()
    car_id = data['car_id']
    customer_id = data['customer_id']

    car_exist = find_car(car_id)
    customer_exist = find_customer(customer_id)

    if not car_exist:
        return jsonify({'message': 'car not real!!!'}), 404

    if car_exist['availability'].lower() == 'available':
        return jsonify({'message': 'car not rented'}), 409

    if not customer_exist:
        return jsonify({'message': 'customer not found'}), 404

    if customer_exist['status'].lower() == 'available':
        return jsonify({'message': 'customer not registered to a car'}), 409

    rent = 'available'
    with driver.session() as session:
        session.run("""
            MATCH (c:Car {car_id: $car_id})
            SET c.availability = $availability
        """, car_id = car_id, availability = rent)

        session.run("""
            MATCH (cus:Customer {customer_id: $customer_id})
            SET cus.status = $status
        """,customer_id = customer_id, status = rent)

    return jsonify({'message': 'car '+str(car_id)+' successfully cancelled by customer '+str(customer_id)}), 200

# SYSTEM -----------------------------------------------------------------------------------------------------
# ensure Neo4j driver is closed on app shutdown
@app.teardown_appcontext
def shutdown_session(exception=None):
    close_driver()

# sørge for å kjøre hovedsession, og ikke importerte/andre prosesser
# bruker debug mode
if __name__ == "__main__":
    app.run(debug=True, port=5001) #finner på: http://127.0.0.1:5001/
