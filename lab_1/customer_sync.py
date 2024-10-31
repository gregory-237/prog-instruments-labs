from dirty import CustomerMatches
from model_objects import Customer, ExternalCustomer, CustomerType


class ConflictException(Exception):
    pass


class CustomerSync:

    def __init__(self, customer_data_access):
        self.customerDataAccess = customer_data_access

    def syncWithDataLayer(self, external_customer):
        customerMatches: CustomerMatches
        if external_customer.isCompany:
            customer_matches = self.loadCompany(external_customer)
        else:
            customer_matches = self.loadPerson(external_customer)

        customer = customer_matches.customer

        if customer is None:
            customer = Customer()
            customer.externalId = external_customer.externalId
            customer.masterExternalId = external_customer.externalId

        self.populate_fields(external_customer, customer)

        created = False
        if customer.internalId is None:
            customer = self.createCustomer(customer)
            created = True
        else:
            self.updateCustomer(customer)

        self.update_contact_info(external_customer, customer)

        if customer_matches.has_duplicates:
            for duplicate in customer_matches.duplicates:
                self.updateDuplicate(external_customer, duplicate)

        self.update_relations(external_customer, customer)
        self.update_preferred_store(external_customer, customer)

        return created

    def update_relations(self, external_customer: ExternalCustomer, customer: Customer):
        consumer_shopping_lists = external_customer.shoppingLists
        for consumerShoppingList in consumer_shopping_lists:
            self.customerDataAccess.updateShoppingList(customer, consumerShoppingList)

    def updateCustomer(self, customer):
        return self.customerDataAccess.updateCustomerRecord(customer)

    def updateDuplicate(self, external_customer: ExternalCustomer, duplicate: Customer):
        if duplicate is None:
            duplicate = Customer()
            duplicate.externalId = external_customer.externalId
            duplicate.masterExternalId = external_customer.externalId

        duplicate.name = external_customer.name

        if duplicate.internalId is None:
            self.createCustomer(duplicate)
        else:
            self.updateCustomer(duplicate)

    @staticmethod
    def update_preferred_store(external_customer: ExternalCustomer, customer: Customer):
        customer.preferredStore = external_customer.preferredStore

    def createCustomer(self, customer) -> Customer:
        return self.customerDataAccess.createCustomerRecord(customer)

    @staticmethod
    def populate_fields(external_customer: ExternalCustomer, customer: Customer):
        customer.name = external_customer.name
        if external_customer.isCompany:
            customer.companyNumber = external_customer.companyNumber
            customer.customerType = CustomerType.COMPANY
        else:
            customer.customerType = CustomerType.PERSON

    @staticmethod
    def update_contact_info(external_customer: ExternalCustomer, customer: Customer):
        customer.address = external_customer.postalAddress

    def loadCompany(self, external_customer) -> CustomerMatches:
        external_id = external_customer.externalId
        company_number = external_customer.companyNumber

        customer_matches = self.customerDataAccess.loadCompanyCustomer(external_id, company_number)

        if customer_matches.customer is not None and CustomerType.COMPANY != customer_matches.customer.customerType:
            raise ConflictException(
                "Existing customer for externalCustomer {externalId} already exists and is not a company")

        if "ExternalId" == customer_matches.matchTerm:
            customer_company_number = customer_matches.customer.company_number
            if company_number != customer_company_number:
                customer_matches.customer.masterExternalId = None
                customer_matches.add_duplicate(customer_matches.customer)
                customer_matches.customer = None
                customer_matches.matchTerm = None

        elif "CompanyNumber" == customer_matches.matchTerm:
            customer_external_id = customer_matches.customer.external_id
            if customer_external_id is not None and external_id != customer_external_id:
                raise ConflictException(
                    f"Existing customer for externalCustomer {company_number} doesn't match external id {external_id} instead found {customer_external_id}")

            customer = customer_matches.customer
            customer.externalId = external_id
            customer.masterExternalId = external_id
            customer_matches.addDuplicate(None)

        return customer_matches

    def loadPerson(self, external_customer):
        external_id = external_customer.externalId

        customer_matches = self.customerDataAccess.loadPersonCustomer(external_id)

        if customer_matches.customer is not None:
            if CustomerType.PERSON != customer_matches.customer.customerType:
                raise ConflictException(
                    f"Existing customer for externalCustomer {external_id} already exists and is not a person")

            if "ExternalId" != customer_matches.matchTerm:
                customer = customer_matches.customer
                customer.externalId = external_id
                customer.masterExternalId = external_id

        return customer_matches
