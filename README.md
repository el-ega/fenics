![tests](https://github.com/el-ega/fenics/actions/workflows/tests.yml/badge.svg)


fenics
======

fenics es el proyecto detrás de https://el-e.ga,
el sitio de pronósticos deportivos.

Seguí el desarrollo en https://github.com/el-ega/fenics/issues.


Cómo configurar un entorno de desarrollo
----------------------------------------

### Algunas dependencias previas

    $ sudo apt-get install python-virtualenv python3-dev libxml2-dev libxslt-dev libjpeg-dev zlib1g-dev


### Configuración el proyecto

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

Para cargar un torneo desde un archivo JSON versionado:

    (env) $ python manage.py import_tournament fixtures/worldcup_2026.json

También hay una versión en español con los mismos datos:

    (env) $ python manage.py import_tournament fixtures/mundial_2026.json

El archivo puede definir partidos explícitos en `matches` o generar los
partidos de grupos con `generate_group_matches`. En ese caso,
`group_match_schedule` permite agregar `when` y `location` por cruce, y
`group_match_description` permite definir la descripción de cada partido de
grupo.

Para cargar noticias:

    (env) $ python manage.py import_news
