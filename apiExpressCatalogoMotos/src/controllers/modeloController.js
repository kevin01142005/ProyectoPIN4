const modeloModel = require('../models/modeloModel')
// se realiza llamado al modelo

module.exports = {

    getModelos: (req, res) => {
        modeloModel.getModelos((err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    getModeloById: (req, res) => {
        const { id } = req.params;
        modeloModel.getModeloById(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            if (result.length === 0) {
                res.status(404).json({ message: 'Modelo no encontrado' });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    getModelosByMarca: (req, res) => {
        const { id } = req.params;
        modeloModel.getModelosByMarca(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    postModelo: (req, res) => {
        const { marcaId, nombre, tipo } = req.body || {};

        if (!marcaId || !nombre) {
            res.status(400).json({ message: 'marcaId y nombre son obligatorios' });
            return;
        }

        modeloModel.postModelo(marcaId, nombre, tipo || null, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe un modelo con ese nombre en la marca' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            if (result === null) {
                res.status(404).json({ message: 'Marca no encontrada' });
                return;
            }
            res.status(201).json({ message: 'Modelo creado correctamente', data: { idInsertado: result } });
        })
    },


    putModelo: (req, res) => {
        const { id } = req.params;
        const { marcaId, nombre, tipo } = req.body || {};

        if (!marcaId || !nombre) {
            res.status(400).json({ message: 'marcaId y nombre son obligatorios' });
            return;
        }

        modeloModel.putModelo(id, marcaId, nombre, tipo || null, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe un modelo con ese nombre en la marca' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Modelo o Marca No Encontrado' });
                return;
            }
            res.status(200).json({ message: 'Modelo actualizado correctamente' });
        })
    },


    deleteModelo: (req, res) => {

        const { id } = req.params;

        modeloModel.contarVersionesActivas(id, (err, conteo) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (conteo[0].total > 0) {
                res.status(409).json({ message: 'No se puede eliminar el modelo porque tiene versiones activas' });
                return;
            }

            modeloModel.deleteModelo(id, (err, result) => {
                if (err) {
                    res.status(500).json({ error: err.message });
                    return;
                }
                if (result.affectedRows === 0) {
                    res.status(404).json({ message: 'Modelo No Encontrado' });
                    return;
                }

                res.status(200).json({ message: 'Modelo eliminado correctamente' });

            })
        })
    },


    restaurarModelo: (req, res) => {
        const { id } = req.params;

        modeloModel.restaurarModelo(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Modelo No Encontrado, ya está activo o su marca está inactiva' });
                return;
            }

            res.status(200).json({ message: 'Modelo restaurado correctamente' });
        })
    }

}
