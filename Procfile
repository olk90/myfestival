release: chmod u+x install.sh && ./install.sh
web: flask db upgrade; flask translate compile; gunicorn myfestival:app