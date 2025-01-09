#!/bin/bash

for port in {5001..5006}
do
    python run_app.py --port=$port &
done