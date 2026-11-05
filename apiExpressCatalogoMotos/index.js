require('dotenv').config({ quiet: true });
const express = require('express');
const bodyParser = require('body-parser');
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./src/config/swaggerConfig');

const marcaRoutes = require('./src/routes/marcaRoutes');
const modeloRoutes = require('./src/routes/modeloRoutes');
const versionRoutes = require('./src/routes/versionRoutes');

const app = express();
const port = process.env.PORT || 4000;

app.use(bodyParser.json());

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument, { customSiteTitle: 'Catálogo de motos - API' }));
app.get('/', (req, res) => res.redirect('/docs'));

app.use('/api/marcas', marcaRoutes);
app.use('/api/modelos', modeloRoutes);
app.use('/api/versiones', versionRoutes);


app.listen(port, () => {
    console.log("Servidor iniciado en http://localhost:" + port);
    console.log("Documentacion (Swagger): http://localhost:" + port + "/docs");
});
