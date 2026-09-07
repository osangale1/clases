# Peticiones GET y POST

Para pedir un recurso se usa una peticion GET, pasando la URL como primer
argumento. La respuesta trae el codigo de estado, los headers y el cuerpo.

Para mandar datos (por ejemplo un formulario o un JSON) se usa POST. Si el
cuerpo es JSON, conviene pasarlo con el parametro `json=` en vez de armar el
string a mano, asi la libreria pone el header `Content-Type: application/json`
automaticamente.

Los parametros de query string se pueden pasar como diccionario con el
argumento `params=`, sin tener que armar el `?clave=valor` manualmente.
