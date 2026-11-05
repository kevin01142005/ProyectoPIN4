const express = require('express')
const router = express.Router();


const versionController = require('../controllers/versionController');



router.get('/getVersiones', versionController.getVersiones)
router.get('/getVersionById/:id', versionController.getVersionById)
router.get('/getVersionesByModelo/:id', versionController.getVersionesByModelo)
router.post('/postVersion', versionController.postVersion);
router.put('/putVersion/:id', versionController.putVersion);
router.put('/restaurarVersion/:id', versionController.restaurarVersion);


router.delete('/deleteVersion/:id', versionController.deleteVersion);



module.exports = router;
