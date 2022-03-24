import random, json, argparse

from faker import Faker

# Get Args
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--items", help="Number of properties", nargs='?', const=100, default=100, type=int)
args = parser.parse_args()

class Property:

    def __init__(self, fake):
        self.property_id = fake.uuid4()
        self.address = fake.street_address()
        self.city = fake.city()
        self.latitude = fake.coordinate(center=40.730610, radius=1.10)
        self.longitude = fake.coordinate(center=-73.935242, radius=1.10)
        self.description = "This is a sample text description of the property."
        self.bathrooms = random.randint(1, 5)
        self.bedrooms = random.randint(1, 8)
        self.pet_friendly = fake.boolean()
        self.price = round(random.uniform(800.00, 2000.00), 2)
        self.agency = fake.company()
        self.agency_id = fake.ssn()
        self.agent_id = fake.ssn()
        self.agent_name = fake.name()
        self.agent_email = fake.email()
        self.agent_phone = fake.phone_number()
        self.agent_address = fake.address()

    

    def property_status(self):
        return random.choice(["for rent", "coming soon", "under lease"])

    def lease_type(self):
        return random.choice(["1 Year", "2 Year", "3 Year"])

    def get_json(self):
        p = {
            "property_id": self.property_id,
            "address": self.address,
            "city": self.city,
            "description": self.description,
            "bathrooms": self.bathrooms if self.bedrooms > self.bathrooms else self.bedrooms,
            "bedrooms": self.bedrooms,
            "pet_friendly": self.pet_friendly,
            "property_status": self.property_status(),
            "price": self.price,
            "lease_type": self.lease_type(),
            
            "latitude": str(self.latitude),
            "longitude": str(self.longitude),

            "agency": self.agency,
            "agency_id": self.agency_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_email": self.agent_email,
            "agent_phone": self.agent_phone,
            "agent_address": self.agent_address,

            "pk": self.agency_id + "#" + self.agent_id, 
            "sk": self.city + "#" + self.address

        }
        return p


def input_data(x):
    properties = []
    fake = Faker()
    for i in range(0, x):
        property = Property(fake)
        properties.append(property.get_json())
        
    with open('properties.json','w') as f:
        json.dump(properties ,f)

def main():
    input_data(args.items)

main()
