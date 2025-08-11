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
  if (
    typeof google === "undefined" ||
    typeof google.charts === "undefined" ||
    !google.charts.hasOwnProperty("visualization")
  ) {
    console.error(
      "Google Charts API has not been loaded. Please ensure you call google.charts.load() and setOnLoadCallback correctly."
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
    greenFrom: 0, // Optional green zone
    greenTo: 120,
    minorTicks: 5,
    majorTicks: ["0", "50", "100", "150", "200"],
  };

  const finalOptions = { ...defaultOptions, ...options };

  var data = google.visualization.arrayToDataTable([
    ["Label", "Value"],
    [label, value],
  ]);

  var chartOptions = {
    width: finalOptions.width,
    height: finalOptions.height,
    min: finalOptions.min,
    max: finalOptions.max,
    redFrom: finalOptions.redFrom,
    redTo: finalOptions.redTo,
    yellowFrom: finalOptions.yellowFrom,
    yellowTo: finalOptions.yellowTo,
    greenFrom: finalOptions.greenFrom,
    greenTo: finalOptions.greenTo,
    minorTicks: finalOptions.minorTicks,
    majorTicks: finalOptions.majorTicks,
    chartArea: { left: 20, top: 20, width: "90%", height: "90%" },
    backgroundColor: { fill: "transparent" }, // Transparent background
    titleTextStyle: { color: "#333", fontName: "Roboto", fontSize: 16 },
    legend: { position: "none" },
    // Advanced styling for the gauge
    redColor: "#E74C3C",
    yellowColor: "#F1C40F",
    greenColor: "#2ECC71",
    // Needle styling
    animation: {
        duration: 500,
        easing: 'inAndOut',
    },
  };

  var chartContainer = document.getElementById(containerId);
  if (!chartContainer) {
    console.error(`DIV element with ID '${containerId}' not found.`);
    return;
  }

  var chart = new google.visualization.Gauge(chartContainer);
  chart.draw(data, chartOptions);

  return chart;
}
