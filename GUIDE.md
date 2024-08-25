# PixelFrame Guide
Here you can find a basic guide of how to use PixelFrame. \
All shown commands/requests and responses are only examples of how the server COULD behave.

# Contents

- [Webinterface](#api-endpoints)
- [Sockets](#sockets-todo)

# API Endpoints
This contains only a few simple examples of how to use the API, for better explanation go to `http://<host>:<port>/docs` for an interactive documentation. Made possible with OpenAPI and FastAPI. There you can also see the standard status codes for the endpoints.

## `/`
### Get the webinterface of the canvas
<details>
<summary>Details</summary>

### Request:

```shell
curl -X 'GET' \
  'http://<host>:<port>/' \
  -H 'accept: text/html'
```

### Response:

```html
<!DOCTYPE html>
<html lang="en">
    <head>
      ...
    </head>
    <body>
      ...
    </body>
</html>
```

> **Note:** The API will redirect to `http://<host>:<port>/web/index.html`

</details>


## `/canvas/`
### Get an image of the current canvas
<details>
<summary>Details</summary>

### Request:

```shell
curl -X 'GET' \
  'http://<host>:<port>/canvas/' \
  -H 'accept: image/webp' \
  -o "canvas.webp"
```

### Response:

WebP Image (saved as "canvas.webp")

</details>


## `/canvas/size`
### Get the size of the canvas
<details>
<summary>Details</summary>

### Request:

```shell
curl -X 'GET' \
  'http://<host>:<port>/canvas/size' \
  -H 'accept: application/json'
```

### Response:

```json lines
{
  "x": 1920,
  "y": 1080
}
```

</details>


## `/canvas/pps`
### Get the amount of pixels a user can place per second
<details>
<summary>Details</summary>

### Request:

```shell
curl -X 'GET' \
  'http://<host>:<port>/canvas/pps' \
  -H 'accept: application/json'
```

### Response:

```json
30
```

</details>


## `/canvas/pixel`
### Get or put a pixel on the canvas
<details>
<summary>GET</summary>

### Request:

```shell
curl -X 'GET' \
  'http://<host>:<port>/canvas/pixel?x=150&y=200' \
  -H 'accept: application/json'
```

### Response:

```json
"70b62c"
```

</details>

<details>
<summary>PUT</summary>

### Request:

```shell
curl -X 'PUT' \
  'http://<host>:<port>/canvas/pixel?x=150&y=200&color=70b62c' \
  -H 'accept: application/json'
```

### Response:

```json
null
```

</details>




# Sockets TODO
Here you can find a few examples for the commands provided by the sockets. Send `HELP` and you'll get all commands available

* `HELP`: Returns a short introductional help text.
* `SIZE`: Returns the size of the visible canvas in pixel as `SIZE <w> <h>`.
* `PX <x> <y>`: Return the current color of a pixel as `PX <x> <y> <rrggbbaa>`.
* `PX <x> <y> <rrggbb(aa)>`: Draw a single pixel at position (x, y) with the specified hex color code.
  If the color code contains an alpha channel value, it is blended with the current color of the pixel.
* `STATS`: Returns the pixel color distribution of the canvas (except black) ordered by pixel frequency.
* `EXIT`: Just like the SSH-command `exit`, disconnect from the server

Example:

    $ echo "SIZE" | nc <host> <port>
    > SIZE 1920 1080
    $ echo "PX 100 200" | nc <host> <port>
    > PX 100 200 f6a8c3
    $ echo "PX 710 80 fbba97" | nc <host> <port>
    > PX Success
    $ echo "PX 711 80 fbba97" | nc <host> <port>
    > You are on cooldown for 21 milliseconds

Anyway, due to a rewrite of the connection handler with a specific timeout, multiple commands seperated by `\n` are **not** supported. But the server will answer to invalid commands, even if you are on cooldown.