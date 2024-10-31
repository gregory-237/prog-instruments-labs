from model_objects import Customer, ShoppingList, CustomerType, Address


class CustomerMatches:
    def __init__(self):
        self.matchTerm = None
        self.customer = None
        self.duplicates = []

    def has_duplicates(self):
        return self.duplicates

    def add_duplicate(self, duplicate):
        self.duplicates.append(duplicate)


class CustomerDataAccess:
    def __init__(self, db):
        self.customerDataLayer = CustomerDataLayer(db)

    def load_company_customer(self, externalId, companyNumber):
        matches = CustomerMatches()
        matchByExternalId: Customer = self.customerDataLayer.find_by_external_id(externalId)
        if matchByExternalId is not None:
            matches.customer = matchByExternalId
            matches.matchTerm = "ExternalId"
            matchByMasterId: Customer = self.customerDataLayer.find_by_master_external_id(externalId)
            if matchByMasterId is not None:
                matches.add_duplicate(matchByMasterId)
        else:
            matchByCompanyNumber: Customer = self.customerDataLayer.find_by_company_number(companyNumber)
            if matchByCompanyNumber is not None:
                matches.customer = matchByCompanyNumber
                matches.matchTerm = "CompanyNumber"

        return matches

    def load_person_customer(self, externalId):
        matches = CustomerMatches()
        matchByPersonalNumber: Customer = self.customerDataLayer.find_by_external_id(externalId)
        matches.customer = matchByPersonalNumber
        if matchByPersonalNumber is not None:
            matches.matchTerm = "ExternalId"
        return matches

    def update_customer_record(self, customer):
        self.customerDataLayer.update_customer_record(customer)

    def create_customer_record(self, customer):
        return self.customerDataLayer.create_customer_record(customer)

    def update_shopping_list(self, customer: Customer, shoppingList: ShoppingList):
        customer.add_shopping_list(shoppingList)
        self.customerDataLayer.update_shopping_list(shoppingList)
        self.customerDataLayer.update_customer_record(customer)


class CustomerDataLayer:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def find_by_external_id(self, externalId):
        self.cursor.execute(
            'SELECT internalId, externalId, masterExternalId, name, customerType, companyNumber FROM customers WHERE externalId=?',
            (externalId,))
        customer = self.customer_from_sql_select_fields(self.cursor.fetchone())
        return customer

    def find_address_id(self, customer):
        self.cursor.execute('SELECT addressId FROM customers WHERE internalId=?', (customer.internalId,))
        (addressId,) = self.cursor.fetchone()
        if addressId:
            return int(addressId)
        return None

    def customer_from_sql_select_fields(self, fields):
        if not fields:
            return None

        customer = Customer(internalId=fields[0], externalId=fields[1], masterExternalId=fields[2], name=fields[3],
                        customerType=CustomerType(fields[4]), companyNumber=fields[5])
        addressId = self.find_address_id(customer)
        if addressId:
            self.cursor.execute('SELECT street, city, postalCode FROM addresses WHERE addressId=?',
                                          (addressId, ))
            addresses = self.cursor.fetchone()
            if addresses:
                (street, city, postalCode) = addresses
                address = Address(street, city, postalCode)
                customer.address = address
        self.cursor.execute('SELECT shoppinglistId FROM customer_shoppinglists WHERE customerId=?', (customer.internalId,))
        shoppinglists = self.cursor.fetchall()
        for sl in shoppinglists:
            self.cursor.execute('SELECT products FROM shoppinglists WHERE shoppinglistId=?', (sl[0],))
            products_as_str = self.cursor.fetchone()
            products = products_as_str[0].split(", ")
            customer.add_shopping_list(ShoppingList(products))
        return customer

    def find_by_master_external_id(self, masterExternalId):
        self.cursor.execute(
            'SELECT internalId, externalId, masterExternalId, name, customerType, companyNumber FROM customers WHERE masterExternalId=?',
            (masterExternalId,))
        return self.customer_from_sql_select_fields(self.cursor.fetchone())

    def find_by_company_number(self, companyNumber):
        self.cursor.execute(
            'SELECT internalId, externalId, masterExternalId, name, customerType, companyNumber FROM customers WHERE companyNumber=?',
            (companyNumber,))
        return self.customer_from_sql_select_fields(self.cursor.fetchone())

    def create_customer_record(self, customer):
        customer.internalId = self.next_id("customers")
        self.cursor.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?);', (
        customer.internalId, customer.externalId, customer.masterExternalId, customer.name, customer.customerType.value,
        customer.companyNumber, None))
        if customer.address:
            addressId = self.next_id("addresses")
            self.cursor.execute('INSERT INTO addresses VALUES (?, ?, ?, ?)', (
                addressId, customer.address.street, customer.address.city, customer.address.postalCode))
            self.cursor.execute('UPDATE customers set addressId=? WHERE internalId=?', (addressId, customer.internalId))

        if customer.shoppingLists:
            for sl in customer.shoppingLists:
                data = ", ".join(sl)
                self.cursor.execute('SELECT shoppinglistId FROM shoppinglists WHERE products=?', (data,))
                shoppinglistId = self.cursor.fetchone()
                if not shoppinglistId:
                    shoppinglistId = self.next_id("shoppinglists")
                    self.cursor.execute('INSERT INTO shoppinglists VALUES (?, ?)', (shoppinglistId, data))
                self.cursor.execute('INSERT INTO customer_shoppinglists VALUES (?, ?)', (customer.internalId, shoppinglistId))
        self.conn.commit()
        return customer

    def next_id(self, tablename):
        self.cursor.execute(f'SELECT MAX(ROWID) AS max_id FROM {tablename};')
        (id,) = self.cursor.fetchone()
        if id:
            return int(id) + 1
        else:
            return 1

    def update_customer_record(self, customer):
        self.cursor.execute(
            'Update customers set externalId=?, masterExternalId=?, name=?, customerType=?, companyNumber=? WHERE internalId=?',
            (customer.externalId, customer.masterExternalId, customer.name, customer.customerType.value,
                customer.companyNumber, customer.internalId))
        if customer.address:
            addressId = self.find_address_id(customer)
            if not addressId:
                addressId = self.next_id("addresses")
                self.cursor.execute('INSERT INTO addresses VALUES (?, ?, ?, ?)', (addressId, customer.address.street, customer.address.city, customer.address.postalCode))
                self.cursor.execute('UPDATE customers set addressId=? WHERE internalId=?', (addressId, customer.internalId))

        self.cursor.execute('DELETE FROM customer_shoppinglists WHERE customerId=?', (customer.internalId,))
        if customer.shoppingLists:
            for sl in customer.shoppingLists:
                products = ", ".join(sl.products)
                self.cursor.execute('SELECT shoppinglistId FROM shoppinglists WHERE products=?', (products,))
                shoppinglistIds = self.cursor.fetchone()
                if shoppinglistIds is not None:
                    (shoppinglistId,) = shoppinglistIds
                    self.cursor.execute('INSERT INTO customer_shoppinglists VALUES (?, ?)',
                                        (customer.internalId, shoppinglistId))
                else:
                    shoppinglistId = self.next_id("shoppinglists")
                    self.cursor.execute('INSERT INTO shoppinglists VALUES (?, ?)', (shoppinglistId, products))
                    self.cursor.execute('INSERT INTO customer_shoppinglists VALUES (?, ?)', (customer.internalId, shoppinglistId))

        self.conn.commit()

    def update_shopping_list(self, shoppingList):
        pass