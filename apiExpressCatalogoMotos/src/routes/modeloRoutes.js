const express = require('express')
const router = express.Router();


const modeloController = require('../controllers/modeloController');



router.get('/getModelos', modeloController.getModelos)
router.get('/getModeloById/:id', modeloController.getModeloById)
router.get('/getModelosByMarca/:id', modeloController.getModelosByMarca)
router.post('/postModelo', modeloController.postModelo);
router.put('/putModelo/:id', modeloController.putModelo);
router.put('/restaurarModelo/:id', modeloController.restaurarModelo);


router.delete('/deleteModelo/:id', modeloController.deleteModelo);



module.exports = router;
