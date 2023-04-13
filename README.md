### Dependencies
- DuckDB
- Flask

### Start the service

We provide two ways to start our URL-shortner service.

#### With Docker

1. First build the Docker image. `# docker build -t web .`
2. Start the Docker image. `# docker run web`


#### Run directly

We highly recommend to use a virtual environment.

1. First create a virtual environment. `$ python3 -m virtualenv env`
2. Activate the environment. `$ source ./env/bin/activate`
3. Install dependencies. `$ pip3 install duckdb Flask`
3. Start the service. `$ python3 main.py`
