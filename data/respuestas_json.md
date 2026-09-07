# Respuestas y JSON

El objeto respuesta tiene, entre otras cosas: `status_code` (codigo HTTP),
`headers` (diccionario) y el cuerpo, que se puede leer como texto o, si es
JSON, parsearlo directo con un metodo que devuelve un diccionario de Python.

Si el cuerpo no es JSON valido, ese metodo tira una excepcion de parseo, asi
que conviene rodearlo de un try/except si no se esta seguro del formato que
va a devolver el servidor.
