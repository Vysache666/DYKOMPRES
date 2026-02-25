// Mengambil elemen-elemen penting dari halaman
const uploadBox = document.getElementById("uploadBox");
const fileInput = document.getElementById("fileInput");
const uploadText = document.getElementById("uploadText");

const qualityOptions = document.querySelectorAll(".quality-option");
const qualityInput = document.getElementById("qualityInput");
const methodSelect = document.getElementById("methodSelect");
const qualitySection = document.getElementById("qualitySection");

// Ketika area upload diklik, input file akan terbuka
uploadBox.addEventListener("click", () => fileInput.click());

// Menampilkan nama file yang dipilih oleh user
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    uploadText.textContent = fileInput.files[0].name;
    uploadText.style.fontWeight = "600";
  }
});

// Mengatur pilihan kualitas secara interaktif
qualityOptions.forEach((opt) => {
  opt.addEventListener("click", () => {
    qualityOptions.forEach((o) => o.classList.remove("selected"));
    opt.classList.add("selected");
    qualityInput.value = opt.dataset.value;
  });
});

// Menyembunyikan opsi kualitas jika metode lossless dipilih
function updateQualityVisibility() {
  qualitySection.style.display =
    methodSelect.value === "lossless" ? "none" : "block";
}

// Inisialisasi tampilan awal
updateQualityVisibility();

// Update tampilan ketika metode kompresi diubah
methodSelect.addEventListener("change", updateQualityVisibility);
