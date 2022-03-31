
from .. import immudb_service, docker_services_each

def test_create_tables(immudb_service):
    immudb_service.login()
    immudb_service.createTables()
    immudb_service.logout()
