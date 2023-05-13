# Intro
El proyecto consiste en implementar una base de datos no relacional (NoSQL), que almacene la información de los movimientos sísmicos que estan ocurriendo en tiempo real y que se encuentran en constante ingesta a los servidores de los organismos geofísicos de USA, Japón y Chile. De esta forma mediante un proceso de extracción de información a través de la interacción directa con las APIs, vamos haciendo consultas iteradas en ciclos de **60 segundos** y posteriormente realizando la limpieza la información para su posterior carga en una plataforma **DBaaS (DataBase as a Service)**. De esta forma se cierra el pipeline de data-engineering.

# Arquitectura
<a href="https://lh3.googleusercontent.com/drive-viewer/AFGJ81qlE-u9qQl5L2Kdb4gLaQNaGXFj35sLhpBLULCoqA3IlCamq8PJypnfLq_i9UMOUZC1Yo6ZHAQQLiVHmZBMNO3crjutZw=s1600?source=screenshot.guru"> <img src="https://lh3.googleusercontent.com/drive-viewer/AFGJ81qlE-u9qQl5L2Kdb4gLaQNaGXFj35sLhpBLULCoqA3IlCamq8PJypnfLq_i9UMOUZC1Yo6ZHAQQLiVHmZBMNO3crjutZw=s1600" /> </a>

# Esquema de almacenamiento en MongoDB Atlas
```json
{
    'id'        :   'Id asignado por MongoDB',
    'time'      :   'fecha y hora del sismo',
    'latitude'  :   'latitud',
    'longitude' :   'longitud',
    'depth'     :   'profundidad',
    'mag'       :   'magnitud',
    'place'     :   'epicentro',
    'country'   :   'país'
}
```

# Microservicio Railway
A través de este microservicio desplegado en Railway como container docker, se ejecuta el fichero **app.py** en intervalos de tiempo prefijados por el fichero con permisos de ejecución **cronworker.sh** del sistema base ubuntu sobre el cual se ejecuta el container, de esta forma se mantiene el proceso iterativo.

**`Ventajas`**
+ Alta disponibilidad (Mediante orquestación con Kubernetes | paralelización en servidores on-premise)
+ Costo
+ CI/CD
+ Escalabilidad (Puede ejecutarse en instancias de AWS, Azure o GCP)

**`Desventajas`**
+ Complejidad en el mantenimiento

**`Comandos de ejecución (Requiere variable de entorno para acceso a MongoDB Atlas)`**
```bash
docker build -t sismology .
```
```bash
docker run --name sismic-logger sismology
```

# Google Cloud Platform (GCP)
Mediante GCP se utiliza **Cloud Functions** para ejecutar directamente el código **cloud-function.py** que realiza todo el proceso de extracción, transformación y carga de los datos hacia MongoDB Atlas, especificando las dependencias necesarias en **requirements.txt** para finalmente asignarle el servicio **Cloud Scheduler** encargado de ejecutar la función descrita a intervalos de tiempo definidos.

**`Ventajas`**
+ Escalabilidad
+ Alta disponibilidad
+ Administración automática del servidor
+ Integración con otros servicios de Google Cloud
+ Monitoreo y registro

**`Desventajas`**
+ Costo

