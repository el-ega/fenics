[![Stories in Ready](https://badge.waffle.io/el-ega/fenics.svg?label=ready&title=ToDo)](http://waffle.io/el-ega/fenics) 

fenics
======

fenics es el proyecto detrás de https://el-ega.com.ar,
el sitio de pronósticos deportivos.

Seguí el desarrollo en https://waffle.io/el-ega/fenics.

Cómo levantar un entorno de desarrollo
--------------------------------------

### Algunas dependencias previas

    $ sudo apt-get install python-virtualenv python3-dev libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev


### Levantando el proyecto

    $ git clone git@github.com:el-ega/fenics
    $ cd fenics
    $ virtualenv -p python3 --system-site-packages env
    $ source env/bin/activate
    (env) $ pip install -r requirements.txt
    (env) $ python manage.py migrate
    (env) $ python manage.py loaddata fixtures/sample_data.json
    (env) $ python manage.py runserver

Acceder a través del browser en http://localhost:8000/


### Cargando información

Opcionalmente, crear un super usuario para administrar el sitio:

    (env) $ python manage.py createsuperuser

Para cargar partidos/resultados del torneo actual:

    (env) $ python manage.py update_matches

Para cargar noticias:

    (env) $ python manage.py import_news
