# PogScience website

This repository hosts the PogScience website. This project is tailored for the PogScience community, but can be adapted
for every other Twitch streaming group by updating the templates a little.

## Features

Planned features for the first stable version are:

- list of all streamers in the group;
- monitoring of lives from these streamers, real-time, using the Twitch API and Twitch webhooks;
- sync of planned streams, from both Twitch Schedules and Google Calendar (if any);
- display of the live and upcoming streams on the homepage, plus a dedicated page with the full calendar;
- no maintenance when configured, reusing existing sources, so streamers don't have another system to update;
- Twitch login for administrators and streamers, to avoid an extra account;
- press page with statistics and such.

Planned features after the first version are:

- option to raid other streamers with a single click, if logged in;
- group events support: streamers and administrators will be able to create a dedicated webpage for group-wide events,
  in the spirit of [`generations-sorciers.fr`](https://generations-sorciers.fr) (French only), with a description and a
  calendar of streams in the event.

## Installation

We develop this website with Python 3.9+, pipenv, Django, NodeJS 12+, and webpack.

### Development version

A Makefile helps developers to install and run the development environnement locally, on UNIX-like systems. Run `make`
for help.

You need to have globally available Python 3.9 or later, NodeJS 12 or later, pipenv (`pip install pipenv`), and
optionally [ngrok](https://ngrok.com/download) for Twitch EventSub support in development mode. Then:

```shell
$ make install  # Install all dependencies.
$ make run      # Run the server in development mode, and webpack in watch mode,
                # with an HTTPS tunnel for Twitch EventSub support.
```

The port will be printed on the console. It is usually [`localhost:8000`](http://localhost:8000). For the Twitch login
to work (see below), you have to use the `localhost` URL (not `127.0.0.1`). A link to the ngrok control panel, including
handy Twitch EventSub requests log and replay options, is also printed on the console (it is always
[`127.0.0.1:4040`](http://127.0.0.1:4040)).

The HTTPS tunnel should close when you stop the `make run` command with Ctrl+C. If not, use `make stop` to stop every
PogScience background services (only ngrok, currently).

⚠️ **The `make run` command above will open an HTTPS tunnel from your localhost to the internet**, with a
randomized URL that will be displayed at the top of the command output. If you don't want to open such a tunnel, use
`make run-local` instead.

We use [`black`](https://github.com/psf/black) to format the Python code. `make install` above will install a pre-commit
hook to reformat the whole projet at each commit. If it didn't, run `pre-commit install` from within the virtualenv. If
a commit fail because of `black`, commit again. The code formatting was fixed.

### Production deployment

TODO, but: Ansible. 🔥

### Secrets

As it use Google and Twitch APIs, this website needs some secrets to work correctly. You'll have to [create a Twitch
application](https://dev.twitch.tv/console), the callback URL being `http://localhost:8000/complete/twitch/` _exactly_.

If you want to be able to import events from Google Calendar, you also need a Google API Key. On the [Google Cloud
Console](https://console.cloud.google.com):

1. [create a project](https://console.cloud.google.com/projectcreate);
2. in [_API and services_](https://console.cloud.google.com/apis/dashboard), click “Enable API and services” at the top
   left of the page, then lookup for “calendar”, and enable the Google Calendar API; 
3. in [“Identifiers” under _API and services_](https://console.cloud.google.com/apis/credentials), create a new API Key
   (you don't need an  OAuth Client ID for this as we only read public calendars). I recommend restricting the API Key
   to the Google Calendar API only.
   
Now that you have all secrets you need, duplicate the `secrets.example.toml` file, rename it as `secrets.toml`, and
write the secrets in it.

### How to test Twitch EventSub in development

As Twitch need to send requests to your local installation, you'll have to install some sort of port forwarding system
_with HTTPS support_. The simplest option is [ngrok](https://ngrok.io) with a free account. Create an account, configure
the ngrok client as specified by their documentation, then run:

```bash
$ ngrok http 8000
```

(or the correct port if Django assigned another one). Finally, you need to add the ngrok URL to the Django configuration
for Django not to reject requests from this unknown domain. Add the ngrok _domain_ (without `https://`) to the `host`
entry of the `django` section of the `secrets.toml` file.

## Commands

We added a few commands to the Django commands system. Add `--help` for help on each command.

- `./manage.py syncschedules` — Loads scheduled streams from Twitch and Google Calendar. _Every 15 min in production._
- `./manage.py subscribe` — Subscribes not-yet-subscribed streamers to EventSub-based Twitch live updates. _Every 15 min
  in production, to renew Twitch-revoked subscriptions._
- `./manage.py unsubscribe [streamer_twitch_id…]` — Unsubscribes the given (or all, if none given) streamers from
  EventSub-based Twitch live updates.
- `./manage.py synclivestreams` — Updates viewers count and stream preview for every online stream. Does nothing if no
  one is online. _Every 2 min in production._

_Scheduled tasks shall not be executed at the same time in production._
