// Documentacion Swagger de la API (se ve en http://localhost:4000/docs)
// Cada ruta trae un ejemplo listo para usar con el boton "Try it out"

const idParam = (descripcion = 'Id del registro') => ({
    name: 'id', in: 'path', required: true, description: descripcion,
    schema: { type: 'integer', minimum: 1 }
});

const cuerpo = (schema, ejemplo) => ({
    required: true,
    content: { 'application/json': { schema: { $ref: `#/components/schemas/${schema}` }, example: ejemplo } }
});

const lista = (schema) => ({
    description: 'OK',
    content: { 'application/json': { schema: { type: 'object', properties: { data: { type: 'array', items: { $ref: `#/components/schemas/${schema}` } } } } } }
});

const mensaje = (descripcion) => ({
    description: descripcion,
    content: { 'application/json': { schema: { $ref: '#/components/schemas/Mensaje' } } }
});

const creado = {
    description: 'Creado',
    content: { 'application/json': { schema: { $ref: '#/components/schemas/Creado' } } }
};

const error500 = mensaje('Error en la base de datos');

// Genera las 7 rutas (get, getById, post, put, delete, restaurar) de una entidad
function rutasCrud({ tag, base, singular, plural, nombre, nombrePlural, o, schema, request, ejemploPost, ejemploPut }) {
    const S = singular.charAt(0).toUpperCase() + singular.slice(1);
    const P = plural.charAt(0).toUpperCase() + plural.slice(1);
    // o = 'o' para modelo, 'a' para marca y versión (concordancia en los textos)
    return {
        [`/api/${base}/get${P}`]: {
            get: { tags: [tag], summary: `Listar ${nombrePlural} activ${o}s`, responses: { 200: lista(schema), 500: error500 } }
        },
        [`/api/${base}/get${S}ById/{id}`]: {
            get: {
                tags: [tag], summary: `Obtener ${nombre} por id`, parameters: [idParam()],
                responses: { 200: lista(schema), 404: mensaje('No encontrado'), 500: error500 }
            }
        },
        [`/api/${base}/post${S}`]: {
            post: {
                tags: [tag], summary: `Crear ${nombre}`, requestBody: cuerpo(request, ejemploPost),
                responses: { 201: creado, 400: mensaje('Datos incompletos o inválidos'), 404: mensaje('Registro relacionado no encontrado'), 409: mensaje('Ya existe'), 500: error500 }
            }
        },
        [`/api/${base}/put${S}/{id}`]: {
            put: {
                tags: [tag], summary: `Actualizar ${nombre}`, parameters: [idParam()], requestBody: cuerpo(request, ejemploPut),
                responses: { 200: mensaje('Actualizado'), 400: mensaje('Datos incompletos o inválidos'), 404: mensaje('No encontrado'), 409: mensaje('Ya existe'), 500: error500 }
            }
        },
        [`/api/${base}/delete${S}/{id}`]: {
            delete: {
                tags: [tag], summary: `Eliminar ${nombre} (borrado lógico: estado = 0)`, parameters: [idParam()],
                responses: { 200: mensaje('Eliminado'), 404: mensaje('No encontrado'), 409: mensaje('Tiene registros activos que dependen de él'), 500: error500 }
            }
        },
        [`/api/${base}/restaurar${S}/{id}`]: {
            put: {
                tags: [tag], summary: `Restaurar ${nombre} eliminad${o} (estado = 1)`, parameters: [idParam()],
                responses: { 200: mensaje('Restaurado'), 404: mensaje('No encontrado o ya activo'), 500: error500 }
            }
        }
    };
}

const auditoria = {
    estado: { type: 'integer', example: 1 },
    creado: { type: 'string', example: '2026-11-04T22:30:00.000Z' },
    actualizado: { type: 'string', example: '2026-11-04T22:30:00.000Z' }
};

const swaggerDocument = {
    openapi: '3.0.3',
    info: {
        title: 'API de catálogo de motos',
        version: '1.0.0',
        description: 'Servicio auxiliar (Node.js + Express + MySQL) con marcas, modelos y versiones de motos. ' +
            'La API principal (FastAPI) consulta **GET /api/versiones/getVersionById/{id}** para validar la moto compatible con un producto.\n\n' +
            'Orden para insertar datos: **marca → modelo → versión** (usa el `idInsertado` de cada respuesta en la siguiente).'
    },
    servers: [{ url: '/' }],
    tags: [{ name: 'Marcas' }, { name: 'Modelos' }, { name: 'Versiones' }],
    paths: {
        ...rutasCrud({
            tag: 'Marcas', base: 'marcas', singular: 'marca', plural: 'marcas', nombre: 'marca', nombrePlural: 'marcas', o: 'a', schema: 'Marca', request: 'MarcaRequest',
            ejemploPost: { nombre: 'Royal Enfield', paisOrigen: 'India' },
            ejemploPut: { nombre: 'Yamaha', paisOrigen: 'Japón' }
        }),
        ...rutasCrud({
            tag: 'Modelos', base: 'modelos', singular: 'modelo', plural: 'modelos', nombre: 'modelo', nombrePlural: 'modelos', o: 'o', schema: 'Modelo', request: 'ModeloRequest',
            ejemploPost: { marcaId: 1, nombre: 'YZF-R15', tipo: 'Deportiva' },
            ejemploPut: { marcaId: 1, nombre: 'FZ 150', tipo: 'Naked' }
        }),
        '/api/modelos/getModelosByMarca/{id}': {
            get: {
                tags: ['Modelos'], summary: 'Modelos de una marca (desplegable en cascada)', parameters: [idParam('Id de la marca')],
                responses: { 200: lista('Modelo'), 500: error500 }
            }
        },
        ...rutasCrud({
            tag: 'Versiones', base: 'versiones', singular: 'version', plural: 'versiones', nombre: 'versión', nombrePlural: 'versiones', o: 'a', schema: 'Version', request: 'VersionRequest',
            ejemploPost: { modeloId: 1, anio: 2025, cilindraje: 149 },
            ejemploPut: { modeloId: 1, anio: 2020, cilindraje: 149 }
        }),
        '/api/versiones/getVersionesByModelo/{id}': {
            get: {
                tags: ['Versiones'], summary: 'Versiones de un modelo (desplegable en cascada)', parameters: [idParam('Id del modelo')],
                responses: { 200: lista('Version'), 500: error500 }
            }
        }
    },
    components: {
        schemas: {
            Marca: {
                type: 'object',
                properties: { id: { type: 'integer', example: 1 }, nombre: { type: 'string', example: 'Yamaha' }, paisOrigen: { type: 'string', example: 'Japón' }, ...auditoria }
            },
            MarcaRequest: {
                type: 'object', required: ['nombre'],
                properties: { nombre: { type: 'string', maxLength: 100 }, paisOrigen: { type: 'string', maxLength: 100 } }
            },
            Modelo: {
                type: 'object',
                properties: {
                    id: { type: 'integer', example: 1 }, marcaId: { type: 'integer', example: 1 }, nombreMarca: { type: 'string', example: 'Yamaha' },
                    nombre: { type: 'string', example: 'FZ 150' }, tipo: { type: 'string', example: 'Naked' }, ...auditoria
                }
            },
            ModeloRequest: {
                type: 'object', required: ['marcaId', 'nombre'],
                properties: { marcaId: { type: 'integer' }, nombre: { type: 'string', maxLength: 100 }, tipo: { type: 'string', maxLength: 50 } }
            },
            Version: {
                type: 'object',
                properties: {
                    id: { type: 'integer', example: 2 }, modeloId: { type: 'integer', example: 1 }, nombreModelo: { type: 'string', example: 'FZ 150' },
                    marcaId: { type: 'integer', example: 1 }, nombreMarca: { type: 'string', example: 'Yamaha' },
                    anio: { type: 'integer', example: 2022 }, cilindraje: { type: 'integer', example: 149 },
                    descripcion: { type: 'string', example: 'Yamaha FZ 150 2022' }, ...auditoria
                }
            },
            VersionRequest: {
                type: 'object', required: ['modeloId', 'anio', 'cilindraje'],
                properties: {
                    modeloId: { type: 'integer' },
                    anio: { type: 'integer', minimum: 1950, description: 'Entre 1950 y el año siguiente al actual' },
                    cilindraje: { type: 'integer', minimum: 1, maximum: 3000 }
                }
            },
            Creado: {
                type: 'object',
                properties: { message: { type: 'string', example: 'Registro creado correctamente' }, data: { type: 'object', properties: { idInsertado: { type: 'integer', example: 9 } } } }
            },
            Mensaje: {
                type: 'object',
                properties: { message: { type: 'string', example: 'Registro no encontrado' }, error: { type: 'string', description: 'Solo en errores 500' } }
            }
        }
    }
};

module.exports = swaggerDocument;
