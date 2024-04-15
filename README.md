# Pixelframe: Multiplayer canvas

## r/Place for hackers and computer scientists

#### Pixelframe is a rewrite of the [Pixelflut Project](https://github.com/defnull/pixelflut), compatible with Python 3.

I wanted to use the Pixelflut project for a university project, but I found out that it was written in Python 2, which is heavily outdated, so I created this.

## Features

Since this is a rewrite of the entire original project, I also added some features the old one has not.

### Display

PyGame isn't exactly a new feature, but its optional now (Web Service coming soon). The new base of this project is Pillow. Also, you can display a stats bar for connection details and basic stats of the canvas when using in public.

### Website (Coming Soon)

Can display the current canvas

### API (Coming Soon)

Based on FastAPI, can update pixels and also hosting the [Website](#website-coming-soon)

### Interactive Sockets

Like the old version, this project uses sockets to communicate with the players. You can set pixels, get pixel colors and even view stats for the whole canvas. New features are a timeout for the connection and a cooldown for spam protection.

### Config

A config for creating templates and sharing them, made easy.


## Usage: The Pixelflut Protocol

PixelFrame uses the base of the Pixelflut Protocol for its commands. Therefore, the basic commands are the same:

* `HELP`: Returns a short introductional help text.
* `SIZE`: Returns the size of the visible canvas in pixel as `SIZE <w> <h>`.
* `PX <x> <y>`: Return the current color of a pixel as `PX <x> <y> <rrggbbaa>`.
* `PX <x> <y> <rrggbb(aa)>`: Draw a single pixel at position (x, y) with the specified hex color code.
  If the color code contains an alpha channel value, it is blended with the current color of the pixel.
* `STATS`: Returns the pixel color distribution of the canvas (except black) ordered by pixel frequency.

Example:

    $ echo "SIZE" | nc pixelflut.example.com 1234
    > SIZE 1920 1080
    $ echo "PX 100 200" | nc pixelflut.example.com 1234
    > PX 100 200 f6a8c3
    $ echo "PX 710 80 fbba97" | nc pixelflut.example.com 1234
    > PX Success
    $ echo "PX 711 80 fbba97" | nc pixelflut.example.com 1234
    > You are on cooldown for 21 milliseconds

Anyway, due to a rewrite of the connection handler with a specific timeout, multiple commands seperated by `\n` are **not** supported. But the server will answer to invalid commands, even if you are on cooldown.

## Server
### Installation

```shell
cd pixelframe
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Starting

```shell
python3 [-c configfile] pixelframe.py
```

### Contribution

If you want to improve this repository, feel free to contribute. \
Please comment your changes properly and run the following script before committing:

```shell
python3 -m black .
python3 -m isort .
```

## Credits

* [Pixelflut](https://github.com/defnull/pixelflut) - A lot of inspiration and code snippets
* [Leon](https://git.leon.wtf/leon/pixelflut) - The `STATS` command
* [LyonsType](./Misc/OFL.txt) - The font `LT Superior Mono`