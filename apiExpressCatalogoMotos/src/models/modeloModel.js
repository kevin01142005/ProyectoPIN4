const db = require('../config/dbConfig');
// se llama a la configuracion de la bd

const SELECT_MODELO = `select mo.id, mo.marca_id as marcaId, ma.nombre as nombreMarca, mo.nombre, mo.tipo,
    mo.estado, mo.creado, mo.actualizado
    from modelos mo
    join marcas ma on ma.id = mo.marca_id`;

class modelo {

    getModelos(callback) {
        const sql = `${SELECT_MODELO} where mo.estado = 1 and ma.estado = 1 order by ma.nombre, mo.nombre`;
        db.query(sql, callback);
    }

    getModeloById(id, callback) {
        const sql = `${SELECT_MODELO} where mo.id = ? and mo.estado = 1 and ma.estado = 1`;
        db.query(sql, [id], callback);
    }

    // modelos de una marca (para el desplegable en cascada)
    getModelosByMarca(marcaId, callback) {
        const sql = `${SELECT_MODELO} where mo.marca_id = ? and mo.estado = 1 and ma.estado = 1 order by mo.nombre`;
        db.query(sql, [marcaId], callback);
    }

    // solo inserta si la marca existe y esta activa
    postModelo(marcaId, nombre, tipo, callback) {
        const sql = `insert into modelos(marca_id, nombre, tipo)
            select id, ?, ? from marcas where id = ? and estado = 1`;
        db.query(sql, [nombre, tipo, marcaId], (err, result) => {
            if (err) {
                return callback(err, null);
            }

            // si no se inserto nada es porque la marca no existe
            callback(null, result.affectedRows === 0 ? null : result.insertId);
        });
    }

    putModelo(id, marcaId, nombre, tipo, callback) {
        const sql = `update modelos set marca_id = ?, nombre = ?, tipo = ?
            where id = ? and estado = 1
            and exists (select 1 from marcas where id = ? and estado = 1)`;
        db.query(sql, [marcaId, nombre, tipo, id, marcaId], callback);
    }

    // cuenta las versiones activas del modelo (no se puede eliminar un modelo que las tenga)
    contarVersionesActivas(id, callback) {
        const sql = 'select count(*) as total from versiones where modelo_id = ? and estado = 1';
        db.query(sql, [id], callback);
    }

    // borrado logico: la fila no se borra, solo pasa a estado = 0
    deleteModelo(id, callback) {
        const sql = 'update modelos set estado = 0 where id = ? and estado = 1';
        db.query(sql, [id], callback);
    }

    // solo se restaura si su marca esta activa
    restaurarModelo(id, callback) {
        const sql = `update modelos set estado = 1
            where id = ? and estado = 0
            and exists (select 1 from marcas where marcas.id = modelos.marca_id and marcas.estado = 1)`;
        db.query(sql, [id], callback);
    }
}


module.exports = new modelo();
