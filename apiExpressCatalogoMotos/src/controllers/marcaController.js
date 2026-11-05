const marcaModel = require('../models/marcaModel')
// se realiza llamado al modelo

module.exports = {

    getMarcas: (req, res) => {
        marcaModel.getMarcas((err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    getMarcaById: (req, res) => {
        const { id } = req.params;
        marcaModel.getMarcaById(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }

            if (result.length === 0) {
                res.status(404).json({ message: 'Marca no encontrada' });
                return;
            }

            res.status(200).json({ data: result });

        });
    },


    postMarca: (req, res) => {
        const { nombre, paisOrigen } = req.body || {};

        if (!nombre) {
            res.status(400).json({ message: 'El nombre de la marca es obligatorio' });
            return;
        }

        marcaModel.postMarca(nombre, paisOrigen || null, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe una marca con ese nombre' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            res.status(201).json({ message: 'Marca creada correctamente', data: { idInsertado: result } });
        })
    },


    putMarca: (req, res) => {
        const { id } = req.params;
        const { nombre, paisOrigen } = req.body || {};

        if (!nombre) {
            res.status(400).json({ message: 'El nombre de la marca es obligatorio' });
            return;
        }

        marcaModel.putMarca(id, nombre, paisOrigen || null, (err, result) => {
            if (err) {
                if (err.code === 'ER_DUP_ENTRY') {
                    res.status(409).json({ message: 'Ya existe una marca con ese nombre' });
                    return;
                }
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Marca No Encontrada' });
                return;
            }
            res.status(200).json({ message: 'Marca actualizada correctamente' });
        })
    },


    deleteMarca: (req, res) => {

        const { id } = req.params;

        marcaModel.contarModelosActivos(id, (err, conteo) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (conteo[0].total > 0) {
                res.status(409).json({ message: 'No se puede eliminar la marca porque tiene modelos activos' });
                return;
            }

            marcaModel.deleteMarca(id, (err, result) => {
                if (err) {
                    res.status(500).json({ error: err.message });
                    return;
                }
                if (result.affectedRows === 0) {
                    res.status(404).json({ message: 'Marca No Encontrada' });
                    return;
                }

                res.status(200).json({ message: 'Marca eliminada correctamente' });

            })
        })
    },


    restaurarMarca: (req, res) => {
        const { id } = req.params;

        marcaModel.restaurarMarca(id, (err, result) => {
            if (err) {
                res.status(500).json({ error: err.message });
                return;
            }
            if (result.affectedRows === 0) {
                res.status(404).json({ message: 'Marca No Encontrada o ya está activa' });
                return;
            }

            res.status(200).json({ message: 'Marca restaurada correctamente' });
        })
    }

}
