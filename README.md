# top-pages-checker
A python script that checks top pages in google analytics once per day

## Setup
This expects that you are working in a Unix-like shell and have `git` and `python3` installed 
```sh
git clone https://github.com/rootandrebound/top-pages-checker.git
cd top-pages-checker
python3 -m venv .venv
source .venv/bin/activate
cp example.env .env
# edit your environmental variables
```