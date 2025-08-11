from rolepermissions.roles import AbstractUserRole

class Administrator(AbstractUserRole):
    available_permissions = {
        "create_tickets":True,
        "delete_tickets":True,
        "create_client_companies":True,
        ...
        }

class Bookkeeper(AbstractUserRole):
    available_permissions = {
        "create_tickets":False,
        "delete_tickets":False,
        "create_client_companies":False,
        ...
        }

class LeadTechnician(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
        }

class Technician(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
        }

class Subcontractor(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
        }

class Sales(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
        }

class ServiceManager(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
    }

class Scheduler(AbstractUserRole):
    available_permissions = {
        "create_tickets":True
    }