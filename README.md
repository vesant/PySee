# PySee

Simple intranet video surveillance skeleton for a Raspberry Pi 2B and a local Linux server.

## Layout

- `src/pysee/raspberry`: Raspberry Pi side that captures `/dev/video0` and publishes video via WebRTC.
- `src/pysee/server`: Local server that receives the stream and serves the browser viewer.
- `src/pysee/common`: Shared config and WebRTC helpers.

## Run

Install dependencies first:

```bash
pip install -r requirements.txt
```

Start the local server:

```bash
python -m pysee.server.main
```

Start the Raspberry side on the Pi:

```bash
export PYSEE_SERVER_URL=http://<server-ip>:8080
python -m pysee.raspberry.main
```

If you are only developing from Windows for now, set the same variable in your shell before running the script.

## Notes

- The skeleton currently assumes one active USB webcam at `/dev/video0`.
- The server exposes `/api/ingest/offer` for the Raspberry and `/api/viewer/offer` for the browser viewer.
- On a Raspberry Pi 2B you may need to pin dependency versions later if a wheel is unavailable for ARMv7.
