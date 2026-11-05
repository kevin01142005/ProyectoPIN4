const db = require('../config/dbConfig');
// se llama a la configuracion de la bd

const SELECT_VERSION = `select v.id, v.modelo_id as modeloId, mo.nombre as nombreModelo,
    ma.id as marcaId, ma.nombre as nombreMarca, v.anio, v.cilindraje,
    concat(ma.nombre, ' ', mo.nombre, ' ', v.anio) as descripcion,
    v.estado, v.creado, v.actualizado
    from versiones v
    join modelos mo on mo.id = v.modelo_id
    join marcas ma on ma.id = mo.marca_id`;

const ACTIVAS = 'v.estado = 1 and mo.estado = 1 and ma.estado = 1';

class version {

    getVersiones(callback) {
        const sql = `${SELECT_VERSION} where ${ACTIVAS} order by ma.nombre, mo.nombre, v.anio, v.cilindraje`;
        db.query(sql, callback);
    }

    // la API principal (FastAPI) usa este metodo para validar la moto compatible con un producto
    getVersionById(id, callback) {
        const sql = `${SELECT_VERSION} where v.id = ? and ${ACTIVAS}`;
        db.query(sql, [id], callback);
    }

    // versiones de un modelo (para el desplegable en cascada)
    getVersionesByModelo(modeloId, callback) {
        const sql = `${SELECT_VERSION} where v.modelo_id = ? and ${ACTIVAS} order by v.anio, v.cilindraje`;
        db.query(sql, [modeloId], callback);
    }

    // solo inserta si el modelo (y su marca) existen y estan activos
    postVersion(modeloId, anio, cilindraje, callback) {
        const sql = `insert into versiones(modelo_id, anio, cilindraje)
            select mo.id, ?, ? from modelos mo
            join marcas ma on ma.id = mo.marca_id
            where mo.id = ? and mo.estado = 1 and ma.estado = 1`;
        db.query(sql, [anio, cilindraje, modeloId], (err, result) => {
            if (err) {
                return callback(err, null);
            }

            // si no se inserto nada es porque el modelo no existe
            callback(null, result.affectedRows === 0 ? null : result.insertId);
        });
    }

    putVersion(id, modeloId, anio, cilindraje, callback) {
        const sql = `update versiones set modelo_id = ?, anio = ?, cilindraje = ?
            where id = ? and estado = 1
            and exists (select 1 from modelos mo join marcas ma on ma.id = mo.marca_id
                        where mo.id = ? and mo.estado = 1 and ma.estado = 1)`;
        db.query(sql, [modeloId, anio, cilindraje, id, modeloId], callback);
    }

    // borrado logico: la fila no se borra, solo pasa a estado = 0
    deleteVersion(id, callback) {
        const sql = 'update versiones set estado = 0 where id = ? and estado = 1';
        db.query(sql, [id], callback);
    }

    // solo se restaura si su modelo esta activo
    restaurarVersion(id, callback) {
        const sql = `update versiones set estado = 1
            where id = ? and estado = 0
            and exists (select 1 from modelos where modelos.id = versiones.modelo_id and modelos.estado = 1)`;
        db.query(sql, [id], callback);
    }
}


module.exports = new version();
