// ------------------ Helper ------------------
function showError(elementId, message) {
  const box = document.getElementById(elementId);
  if (box) {
    box.textContent = message;
    box.style.display = "block";
    setTimeout(() => (box.style.display = "none"), 4000);
  } else {
    alert(message);
  }
}

// ------------------ Tabs ------------------
document.querySelectorAll(".tab-buttons button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-buttons button").forEach((b) =>
      b.classList.remove("active")
    );
    btn.classList.add("active");

    document.querySelectorAll(".form-tab").forEach((f) =>
      f.classList.remove("active")
    );
    document.getElementById(btn.dataset.target).classList.add("active");
  });
});

// ------------------ Redirect helper ------------------
function redirectByRole(user) {
  if (!user || !user.role) return;
  if (user.role === "User") {
    window.location.href = "/user_dashboard";
  } else if (user.role === "Employer") {
    window.location.href = "/admin_dashboard";
  }
}

// ------------------ User Login ------------------
const userLoginForm = document.getElementById("userLogin");
if (userLoginForm) {
  userLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const identifier = e.target.user_identifier.value.trim();
    const password = e.target.user_password.value.trim();
    const btn = e.target.querySelector("button");

    try {
      btn.classList.add("loading");
      btn.disabled = true;
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ identifier, password }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        redirectByRole(data.user);
      } else {
        showError("userError", data.message || "Login failed.");
      }
    } catch {
      showError("userError", "Server error. Try again.");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });
}

// ------------------ Employer Login ------------------
const employerLoginForm = document.getElementById("employerLogin");
if (employerLoginForm) {
  employerLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const identifier = e.target.emp_identifier.value.trim();
    const password = e.target.emp_password.value.trim();
    const btn = e.target.querySelector("button");

    try {
      btn.classList.add("loading");
      btn.disabled = true;
      const res = await fetch("/api/employer/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ identifier, password }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        redirectByRole(data.user);
      } else {
        showError("empError", data.message || "Login failed.");
      }
    } catch {
      showError("empError", "Server error. Try again.");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });
}

// ------------------ User Register ------------------
const userRegisterForm = document.getElementById("userRegister");
if (userRegisterForm) {
  userRegisterForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button");
    const data = {
      name: e.target.name.value.trim(),
      email: e.target.email.value.trim(),
      mobile: e.target.mobile.value.trim(),
      password: e.target.password.value.trim(),
      confirm_password: e.target.confirm_password.value.trim(),
    };

    if (data.password !== data.confirm_password) {
      showError("userRegError", "Passwords do not match!");
      return;
    }

    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(data.password)) {
      showError("userRegError", "Password must be at least 8 chars, include upper, lower, digit.");
      return;
    }

    try {
      btn.classList.add("loading");
      btn.disabled = true;
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await res.json();
      if (res.ok && result.success) {
        alert("Registration successful. Please login.");
        window.location.href = "/login?tab=user";  
      } else {
        showError("userRegError", result.message || "Registration failed.");
      }
    } catch {
      showError("userRegError", "Server error. Try again.");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });
}

// ------------------ Employer Register ------------------
const employerRegisterForm = document.getElementById("employerRegister");
if (employerRegisterForm) {
  employerRegisterForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button");
    const data = {
      employer_name: e.target.employer_name.value.trim(),
      organization_name: e.target.organization_name.value.trim(),
      organization_email: e.target.organization_email.value.trim(),
      mobile: e.target.mobile.value.trim(),
      password: e.target.password.value.trim(),
      confirm_password: e.target.confirm_password.value.trim(),
    };

    if (data.password !== data.confirm_password) {
      showError("empRegError", "Passwords do not match!");
      return;
    }

    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(data.password)) {
      showError("empRegError", "Password must be at least 8 chars, include upper, lower, digit.");
      return;
    }

    try {
      btn.classList.add("loading");
      btn.disabled = true;
      const res = await fetch("/api/employer/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await res.json();
      if (res.ok && result.success) {
        alert("Employer registered successfully. Please login.");
        window.location.href = "/login?tab=employer";   
      } else {
        showError("empRegError", result.message || "Registration failed.");
      }
    } catch {
      showError("empRegError", "Server error. Try again.");
    } finally {
      btn.classList.remove("loading");
      btn.disabled = false;
    }
  });
}

// ------------------ Handle ?tab=user|employer ------------------
window.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const tab = params.get("tab");

  if (tab === "employer") {
    document.querySelector('.tab-buttons button[data-target="employerLogin"]').click();
  } else if (tab === "user") {
    document.querySelector('.tab-buttons button[data-target="userLogin"]').click();
  }
});
