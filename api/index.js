const express = require("express");
const mysql = require("mysql2/promise");
const cors = require("cors");

const app = express();
const port = 8000; // Port untuk API baru, bisa diubah

app.use(cors());
app.use(express.json());

// Konfigurasi koneksi database dari DATABASE_URL di main.py
const dbConfig = {
  host: "127.0.0.1",
  user: "jti_acr_bas",
  password: "JTI_j0h@r10",
  database: "jti-new2",
  port: 3306,
};

// Membuat connection pool
const pool = mysql.createPool(dbConfig);

// Middleware untuk error handling
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Endpoint untuk mendapatkan semua chillers
app.get(
  "/chillers",
  asyncHandler(async (req, res) => {
    const [rows] = await pool.query("SELECT * FROM chillers");
    res.json(rows);
  })
);

// Endpoint untuk mendapatkan satu chiller berdasarkan ID
app.get(
  "/chillers/:chiller_id",
  asyncHandler(async (req, res) => {
    const { chiller_id } = req.params;
    const [rows] = await pool.query("SELECT * FROM chillers WHERE id = ?", [
      chiller_id,
    ]);
    if (rows.length === 0) {
      return res.status(404).json({ detail: "Chiller not found" });
    }
    res.json(rows[0]);
  })
);

// Endpoint untuk mendapatkan data real-time (terbaru) dari satu chiller
app.get(
  "/chillers/:chiller_id/latest_data",
  asyncHandler(async (req, res) => {
    const { chiller_id } = req.params;
    const sql = `
        SELECT * 
        FROM chiller_datas 
        WHERE chiller_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    `;
    const [rows] = await pool.query(sql, [chiller_id]);
    if (rows.length === 0) {
      return res
        .status(404)
        .json({ detail: "Chiller data not found for this ID" });
    }
    res.json(rows[0]);
  })
);

// Endpoint untuk mendapatkan data historis chiller dengan rentang waktu
app.get(
  "/chillers/:chiller_id/history",
  asyncHandler(async (req, res) => {
    const { chiller_id } = req.params;
    const { start_date, end_date } = req.query;

    let sql = "SELECT * FROM chiller_datas WHERE chiller_id = ?";
    const params = [chiller_id];

    if (start_date) {
      sql += " AND timestamp >= ?";
      params.push(start_date);
    }
    if (end_date) {
      sql += " AND timestamp <= ?";
      params.push(end_date);
    }

    sql += " ORDER BY timestamp ASC";

    const [rows] = await pool.query(sql, params);

    if (rows.length === 0) {
      return res
        .status(404)
        .json({
          detail: "No chiller data found for this ID in the given time range",
        });
    }
    res.json(rows);
  })
);

// Endpoint untuk mendapatkan data terbaru dari semua chiller
app.get(
  "/chillers/latest_data",
  asyncHandler(async (req, res) => {
    // Query ini sedikit kompleks di SQL murni dibandingkan dengan ORM.
    // Ini akan mengambil baris data terbaru untuk setiap chiller_id.
    const sql = `
        SELECT cd1.*
        FROM chiller_datas cd1
        LEFT JOIN chiller_datas cd2 ON (cd1.chiller_id = cd2.chiller_id AND cd1.timestamp < cd2.timestamp)
        WHERE cd2.timestamp IS NULL;
    `;
    const [rows] = await pool.query(sql);
    res.json(rows);
  })
);

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send("Something broke!");
});

app.listen(port, () => {
  console.log(`Server JavaScript berjalan di http://localhost:${port}`);
});
