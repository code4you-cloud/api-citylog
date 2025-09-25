#!/bin/bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 3000 --reload --log-level debug
# standard
# uvicorn main:app --reload
