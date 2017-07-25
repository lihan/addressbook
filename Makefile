install:
	pip install -r requirements/production.txt

run:
	make install
	dev_appserver.py .

test:
	make install
	python -m unittest discover addressbook

deploy:
	gcloud app deploy

browse:
	gcloud app browse
