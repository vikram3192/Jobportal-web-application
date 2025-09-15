// ---------------- Sidebar & Overlay ----------------
const profileIcon = document.querySelector(".profile-icon");
const menuIcon = document.querySelector(".menu-icon");
const sidebar = document.getElementById("sidebar");
const closeBtn = document.querySelector(".close-btn");
const overlay = document.querySelector(".overlay");

// Toggle sidebar via profile icon
profileIcon?.addEventListener("click", () => {
  sidebar?.classList.toggle("active");
  overlay?.classList.toggle("active");
  // accessibility
  if (sidebar.classList.contains("active"))
    sidebar.setAttribute("aria-hidden", "false");
  else sidebar.setAttribute("aria-hidden", "true");
});

// Open sidebar via menu icon
menuIcon?.addEventListener("click", () => {
  sidebar?.classList.add("active");
  overlay?.classList.add("active");
  sidebar?.setAttribute("aria-hidden", "false");
});

// Close sidebar via close button
closeBtn?.addEventListener("click", () => {
  sidebar?.classList.remove("active");
  overlay?.classList.remove("active");
  sidebar?.setAttribute("aria-hidden", "true");
});

// Close sidebar by clicking on overlay
overlay?.addEventListener("click", () => {
  sidebar?.classList.remove("active");
  overlay?.classList.remove("active");
  sidebar?.setAttribute("aria-hidden", "true");
});

// Close sidebar if clicking outside
document.addEventListener("click", (e) => {
  if (
    sidebar &&
    !sidebar.contains(e.target) &&
    !profileIcon?.contains(e.target) &&
    !menuIcon?.contains(e.target)
  ) {
    sidebar.classList.remove("active");
    overlay?.classList.remove("active");
    sidebar.setAttribute("aria-hidden", "true");
  }
});

// Close with ESC key for accessibility
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    sidebar?.classList.remove("active");
    overlay?.classList.remove("active");
    sidebar?.setAttribute("aria-hidden", "true");
  }
});

// ---------------- Dark Mode Toggle ----------------
const darkModeToggle = document.getElementById("darkModeToggle");
if (darkModeToggle) {
  // Load preference
  if (localStorage.getItem("darkMode") === "enabled") {
    document.body.classList.add("dark-mode");
    darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
  }

  darkModeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const enabled = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", enabled ? "enabled" : "disabled");
    darkModeToggle.innerHTML = enabled
      ? '<i class="fas fa-sun"></i>'
      : '<i class="fas fa-moon"></i>';
  });
}
