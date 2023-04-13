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

### Run the demo

We provided a source file `demo.py` for testing and demonstracting.

To run the demo:

1. Change `demo.py`. Especially `addr` and number of URLs to generate
2. Start the service
3. Run. `python3 demo.py`
