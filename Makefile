install:
	python -m pip install -r ./requirements.txt

run:
	honcho -e .env run python ./main.py