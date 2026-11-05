const versionModel = require('../models/versionModel')
// se realiza llamado al modelo

const ANIO_MAXIMO = new Date().getFullYear() + 1;

// revisa que anio y cilindraje sean numeros enteros dentro de un rango valido
function datosInvalidos(modeloId, anio, cilindraje) {
    if (!modeloId || anio === undefined || cilindraje === undefined) {
        return 'modeloId, anio y cilindraje son obligatorios';
    }
    if (!Number.isInteger(Number(anio)) || anio < 1950 || anio > ANIO_MAXIMO) {
        return `anio debe ser un número entero entre 1950 y ${ANIO_MAXIMO}`;
    }
    if (!Number.isInteger(Number(cilindraje)) || cilindraje < 1 || cilindraje > 3000) {
        return 'cilindraje debe ser un número entero entre 1 y 3000';
    }
    return null;
}

module.exports = {

    getVersiones: (req, res) => {
        versionModel.getVersiones((err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    getVersionById: (req, res) => {
        const { id } = req.params;
        versionModel.getVersionById(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            if (result.length === 0) {
                res.status(404).json({ message: 'Versión no encontrada' });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    getVersionesByModelo: (req, res) => {
        const { id } = req.params;
        versionModel.getVersionesByModelo(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    postVersion: (req, res) => {
        const { modeloId, anio, cilindraje } = req.body || {};

        const error = datosInvalidos(modeloId, anio, cilindraje);
        if (error) {
            res.status(400).json({ message: error });
            return;
        }

        versionModel.postVersion(modeloId, anio, cilindraje, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe una versión con ese modelo, año y cilindraje' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            if (result === null) {
                res.status(404).json({ message: 'Modelo no encontrado' });
                return;
            }
            res.status(201).json({ message: 'Versión creada correctamente', data: { idInsertado: result } });
        })
    },


    putVersion: (req, res) => {
        const { id } = req.params;
        const { modeloId, anio, cilindraje } = req.body || {};

        const error = datosInvalidos(modeloId, anio, cilindraje);
        if (error) {
            res.status(400).json({ message: error });
            return;
        }

        versionModel.putVersion(id, modeloId, anio, cilindraje, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe una versión con ese modelo, año y cilindraje' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Versión o Modelo No Encontrado' });
                return;
            }
            res.status(200).json({ message: 'Versión actualizada correctamente' });
        })
    },


    deleteVersion: (req, res) => {

        const { id } = req.params;

        versionModel.deleteVersion(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Versión No Encontrada' });
                return;
            }

            res.status(200).json({ message: 'Versión eliminada correctamente' });

        })
    },


    restaurarVersion: (req, res) => {
        const { id } = req.params;

        versionModel.restaurarVersion(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Versión No Encontrada, ya está activa o su modelo está inactivo' });
                return;
            }

            res.status(200).json({ message: 'Versión restaurada correctamente' });
        })
    }

}
