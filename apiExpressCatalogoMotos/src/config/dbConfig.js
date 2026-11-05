require('dotenv').config({ quiet: true });
// se cargan las variables del archivo .env (usuario, contraseña, host de la bd)

const mysql = require('mysql2');

// En la nube (Aiven) la conexion exige SSL; en XAMPP no
const ssl = process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : undefined;

// Se usa un pool (grupo de conexiones) para que la API no se caiga si la nube
// cierra una conexion inactiva. Se usa igual que createConnection: db.query(sql, params, callback)
const db = process.env.DATABASE_URL
    ? mysql.createPool({
        uri: process.env.DATABASE_URL,
        ssl: ssl
    })
    : mysql.createPool({
        host: process.env.DB_HOST || 'localhost',
        user: process.env.DB_USER || 'root',
        password: process.env.DB_PASSWORD || '',
        database: process.env.DB_NAME || 'catalogo_motos',
        port: process.env.DB_PORT || 3306,
        ssl: ssl
    });

db.getConnection((err, conexion) => {
    if (err) {
        throw err;
    }
    console.log("Conexion MYSQL exitosa");
    conexion.release();
});

module.exports = db;
