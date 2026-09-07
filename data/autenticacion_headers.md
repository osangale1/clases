# Autenticacion y headers

Los headers se mandan como un diccionario en el argumento `headers=`. Para
autenticacion basica (usuario y contraseña) hay un argumento `auth=` que
arma el header `Authorization` correspondiente.

Para autenticacion por token (Bearer), lo mas comun es mandar el header a
mano: `{"Authorization": f"Bearer {token}"}`.

Si el servidor requiere un header custom (por ejemplo `X-API-Key`), se
agrega igual que cualquier otro header al diccionario.
