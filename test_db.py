from database import get_connection
try:
    c=get_connection(); print('PostgreSQL connection successful!'); c.close()
except Exception as e:
    print('PostgreSQL connection failed!'); print(e)
