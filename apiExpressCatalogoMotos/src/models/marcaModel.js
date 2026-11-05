const db = require('../config/dbConfig');
// se llama a la configuracion de la bd

const CAMPOS = 'id, nombre, pais_origen as paisOrigen, estado, creado, actualizado';

class marca {

    getMarcas(callback) {
        const sql = `select ${CAMPOS} from marcas where estado = 1 order by nombre`;
        db.query(sql, callback);
    }

    getMarcaById(id, callback) {
        const sql = `select ${CAMPOS} from marcas where id = ? and estado = 1`;
        db.query(sql, [id], callback);
    }

    postMarca(nombre, paisOrigen, callback) {
        const sql = 'insert into marcas(nombre, pais_origen) values (?, ?)';
        db.query(sql, [nombre, paisOrigen], (err, result) => {
            if (err) {
                return callback(err, null);
            }

            callback(null, result.insertId);
        });
    }

    putMarca(id, nombre, paisOrigen, callback) {
        const sql = 'update marcas set nombre = ?, pais_origen = ? where id = ? and estado = 1';
        db.query(sql, [nombre, paisOrigen, id], callback);
    }

    // cuenta los modelos activos de la marca (no se puede eliminar una marca que los tenga)
    contarModelosActivos(id, callback) {
        const sql = 'select count(*) as total from modelos where marca_id = ? and estado = 1';
        db.query(sql, [id], callback);
    }

    // borrado logico: la fila no se borra, solo pasa a estado = 0
    deleteMarca(id, callback) {
        const sql = 'update marcas set estado = 0 where id = ? and estado = 1';
        db.query(sql, [id], callback);
    }

    restaurarMarca(id, callback) {
        const sql = 'update marcas set estado = 1 where id = ? and estado = 0';
        db.query(sql, [id], callback);
    }
}


module.exports = new marca();
