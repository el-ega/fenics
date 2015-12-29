fenics
======

fenics es el proyecto detrás de https://el-ega.com.ar,
el sitio de pronósticos deportivos.


Cómo levantar un entorno de desarrollo
--------------------------------------

    $ git clone git@github.com:el-ega/fenics
    $ cd fenics
    $ virtualenv env
    $ source env/bin/activate
    (env) $ pip install -r requirements.txt
    (env) $ python manage.py migrate
    (env) $ python manage.py loaddata fixtures/sample_data.json
    (env) $ python manage.py runserver


Para cargar partidos/resultados del torneo actual:

    (env) $ python manage.py update_matches

Para cargar noticias:

    (env) $ python manage.py import_news
