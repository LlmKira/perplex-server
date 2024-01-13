# perplex-server

A server that make chatgpt access to the internet.

## Todo

- [ ] Clean up code

## Setup

### Env Setup

```shell
cd perplex-server
cp .env.exp .env
nano .env
```

### Python Setup

```shell
pip install pdm
pdm install
```

### Run

You can run the server with pm2.

```shell
apt install npm
npm install pm2 -g
pm2 start pm2.json
```

## Test Server

Run test/__init__.py to test the server.
