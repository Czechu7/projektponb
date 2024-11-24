#!/bin/bash

for port in {5001..5003}
do
    python app.py --port=$port &
done