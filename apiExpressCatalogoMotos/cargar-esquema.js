require('dotenv').config({ quiet: true });
const fs = require('fs');
const path = require('path');
const mysql = require('mysql2/promise');

async function main() {
  const uri = process.env.DATABASE_URL;
  if (!uri) {
    console.error('Falta DATABASE_URL en el archivo .env');
    process.exit(1);
  }
  const archivo = path.join(__dirname, 'database', 'esquema_mysql.sql');
  const sql = fs
    .readFileSync(archivo, 'utf8')
    .split('\n')
    .filter((linea) => !/^\s*(create database|use\s)/i.test(linea))
    .join('\n');
  const conexion = await mysql.createConnection({
    uri,
    ssl: process.env.DB_SSL === 'true' ? { rejectUnauthorized: false } : undefined,
    multipleStatements: true,
  });
  await conexion.query(sql);
  for (const tabla of ['marcas', 'modelos', 'versiones']) {
    const [filas] = await conexion.query('SELECT COUNT(*) AS total FROM ' + tabla);
    console.log(tabla + ': ' + filas[0].total + ' registros');
  }
  await conexion.end();
  console.log('Esquema cargado correctamente');
}

main().catch((error) => {
  console.error('No se pudo cargar el esquema:', error.message);
  process.exit(1);
});