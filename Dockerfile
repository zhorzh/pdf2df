from jupyter/minimal-notebook

# install dev tools
user root
run apt-get update --fix-missing
run apt-get install -y default-jre
run apt-get install -y ranger
run apt-get remove cmdtest
run apt-get install -y curl

# install python dependencies
user root
copy ./requirements.txt /srv/requirements.txt
workdir /srv
run pip install -r requirements.txt

# run jupyter
user jovyan
workdir /home/jovyan
env JUPYTER_ENABLE_LAB=1
env JUPYTER_TOKEN=123
expose 8888
