// googleGaugeComponent.js

/**
 * Fungsi untuk membuat dan merender gauge Google Charts.
 * Fungsi ini harus dipanggil HANYA SETELAH google.charts.load() selesai.
 *
 * @param {string} containerId ID dari elemen DIV tempat gauge akan dirender.
 * @param {string} label Label yang akan muncul di bawah nilai gauge (misal: 'Speed', 'Fuel').
 * @param {number} value Nilai yang akan ditampilkan pada gauge.
 * @param {object} [options={}] Objek opsi tambahan untuk konfigurasi gauge.
 * - width: Lebar gauge (default: 400)
 * - height: Tinggi gauge (default: 200)
 * - min: Nilai minimum gauge (default: 0)
 * - max: Nilai maksimum gauge (default: 200)
 * - redFrom: Mulai rentang merah
 * - redTo: Akhir rentang merah
 * - yellowFrom: Mulai rentang kuning
 * - yellowTo: Akhir rentang kuning
 * - greenFrom: Mulai rentang hijau (opsional, Google Charts akan menggunakan warna default jika tidak ada zona lain)
 * - greenTo: Akhir rentang hijau
 * - minorTicks: Jumlah tick kecil (default: 5)
 */
function createGoogleGauge(containerId, label, value, options = {}) {
  // Memastikan Google Charts API sudah dimuat sebelum mencoba menggambar chart
  if (
    typeof google === "undefined" ||
    typeof google.charts === "undefined" ||
    !google.charts.hasOwnProperty("visualization")
  ) {
    console.error(
      "Google Charts API belum dimuat. Pastikan Anda memanggil google.charts.load() dan setOnLoadCallback dengan benar."
    );
    return;
  }

  const defaultOptions = {
    width: 400,
    height: 200,
    min: 0,
    max: 200,
    redFrom: 160,
    redTo: 200,
    yellowFrom: 120,
    yellowTo: 160,
    // greenFrom dan greenTo bisa ditambahkan jika ingin zona hijau eksplisit
    minorTicks: 5,
  };

  // Menggabungkan opsi default dengan opsi yang diberikan. Opsi yang diberikan akan menimpa default.
  const finalOptions = { ...defaultOptions, ...options };

  var data = google.visualization.arrayToDataTable([
    ["Label", "Value"],
    [label, value], // Menggunakan label dan value yang dinamis
  ]);

  // Membuat objek opsi untuk chart
  var chartOptions = {
    width: finalOptions.width,
    height: finalOptions.height,
    min: finalOptions.min,
    max: finalOptions.max,
    redFrom: finalOptions.redFrom,
    redTo: finalOptions.redTo,
    yellowFrom: finalOptions.yellowFrom,
    yellowTo: finalOptions.yellowTo,
    minorTicks: finalOptions.minorTicks,
  };

  // Menambahkan zona hijau jika didefinisikan
  if (
    finalOptions.greenFrom !== undefined &&
    finalOptions.greenTo !== undefined
  ) {
    chartOptions.greenFrom = finalOptions.greenFrom;
    chartOptions.greenTo = finalOptions.greenTo;
  }

  var chartContainer = document.getElementById(containerId);
  if (!chartContainer) {
    console.error(`Elemen DIV dengan ID '${containerId}' tidak ditemukan.`);
    return;
  }

  // Pastikan container memiliki gaya lebar/tinggi jika belum ada
  // Ini penting agar chart memiliki ruang untuk dirender.
  // Jika Anda sudah mengatur ini di CSS atau HTML, baris ini bisa diabaikan.
  // chartContainer.style.width = `${finalOptions.width}px`;
  // chartContainer.style.height = `${finalOptions.height}px`;

  var chart = new google.visualization.Gauge(chartContainer);
  chart.draw(data, chartOptions);

  // Mengembalikan objek chart agar bisa dimanipulasi (misal: update nilai)
  return chart;
}
