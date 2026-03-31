# retail-erp-simulator
A simulation for operational systems to simulate transactions to an OLTP Database.

## Prequisites
Postgres SQL
Python

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

3. Run the application
```
uvicorn run:app --reload
```

4. Add data into your database at "http://localhost:8000/seed/"


## Changelog
- ver 0.0 added initial development
- ver 1 basic seeding application.
