# retail-erp-simulator
This an auxillary project to a data pipeline project found on https://github.com/gontay/retail-erp-dbt-datapipeline The tables are hosted on databricks.
This project simulates operational systems and generates transactions to an OLTP Database.
It includes best practices like including temporal data (time based metadata) for each row via columns "created_at" and "updated_at".
 
## Prequisites
This simulator requires you have the following installed:
- PostgreSQL
- Python

## Getting Started
To get started, follow these steps:

1. Clone the repository
``` 
git clone https://github.com/<your_username>/retail-erp-simulator.git
```

2. Install the required dependencies

``` 
pip install -r requirements
```

4. Create and add the following variables in your .env

local PostgreSQL Server:
```
DBURL = <database url>
DBNAME = <database name>
PG_USER = <postgresSQL username>
PG_PASSWORD = <postgreSQL password>
```
cloud based PostgreSQL server:
```
DBURL = <cloud based database connection String>
```
Supabase S3 Bucket environment:
```
SUPABASE_URL = <SUPABASE Project URL>
SUPABASE_BUCKET = <SUPABASE Bucket Name>
SUPABASE_SERVICE_ROLE_KEY= <SUPABASE Service Role Key>
```

3. Run the application
```
uvicorn run:app --reload
```

4. Add data into your database at "http://localhost:8000/seed/"


## Changelog
- ver 0.0 added initial development
- ver 1 basic seeding application.
