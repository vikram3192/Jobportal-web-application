// ---------------- Common helpers ----------------
function showPageAlert(message, type = "error", timeout = 4000, selector = "pageAlert") {
  const el = document.getElementById(selector);
  if (!el) {
    alert(message);
    return;
  }
  el.textContent = message;
  el.className = "alert " + (type === "success" ? "alert-success" : "alert-error");
  el.style.display = "block";
  if (timeout > 0) setTimeout(() => (el.style.display = "none"), timeout);
}

// ---------------- Auto-hide alerts ----------------
setTimeout(() => {
  document.querySelectorAll(".alert").forEach((el) => (el.style.display = "none"));
}, 4000);

// ---------------- Fetch session (user profile) ----------------
async function fetchUserProfile() {
  try {
    const res = await fetch("/api/session", { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();
    if (data.success && data.user) {
      document.getElementById("userName").textContent = data.user.name || "-";
      document.getElementById("userEmail").textContent = data.user.email || "-";
      document.getElementById("userMobile").textContent = data.user.mobile || "-";
      if (data.user.profile_pic) {
        document.getElementById("profilePic").src =
          "/uploads/profile_pics/" + data.user.profile_pic;
      }
    }
  } catch (err) {
    console.error("Profile fetch error:", err);
  }
}

// ---------------- Profile Upload ----------------
document.getElementById("profileUpload")?.addEventListener("change", async function () {
  const file = this.files[0];
  if (!file) return;

  const allowed = ["image/png", "image/jpeg", "image/jpg"];
  if (!allowed.includes(file.type)) {
    showPageAlert("Only PNG/JPG allowed for profile picture");
    return;
  }

  const formData = new FormData();
  formData.append("profile_pic", this.files[0]);

  try {
    const res = await fetch("/api/upload-profile", {
      method: "POST",
      body: formData,
      credentials: "include",
    });
    const data = await res.json();
    if (res.ok && data.success) {
      document.getElementById("profilePic").src =
        "/uploads/profile_pics/" + data.filename;
      showPageAlert("Profile updated", "success");
    } else {
      showPageAlert(data.message || "Failed to upload profile picture");
    }
  } catch (err) {
    showPageAlert("Server error. Please try again.");
  }
});

// ---------------- Remove Profile ----------------
document.getElementById("removeProfileBtn")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/remove-profile", {
      method: "POST",
      credentials: "include",
    });
    const data = await res.json();
    if (res.ok && data.success) {
      document.getElementById("profilePic").src =
        "/static/images/default-user.png";
      showPageAlert("Profile picture removed", "success");
    } else {
      showPageAlert(data.message || "Failed to remove profile picture");
    }
  } catch (err) {
    showPageAlert("Server error. Please try again.");
  }
});

// ---------------- Logout ----------------
document.getElementById("logoutBtn")?.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST", credentials: "include" });
  window.location.href = "/login";
});

// ---------------- Job Listing ----------------
async function fetchJobs(q = "", page = 1) {
  try {
    const res = await fetch(`/api/jobs?q=${encodeURIComponent(q)}&page=${page}`, {
      credentials: "include",
    });
    const data = await res.json();
    const jobGrid = document.getElementById("jobGrid");
    jobGrid.innerHTML = "";

    if (res.ok && data.success && data.jobs && data.jobs.length) {
      data.jobs.forEach((job) => {
        const card = document.createElement("div");
        card.className = "job-card";

        card.innerHTML = `
          <div class="job-header">
            <div class="job-top">
              <div class="job-logo">
                <img src="${job.logo_url || "/static/images/default-logo.png"}" alt="Logo">
              </div>
              ${job.applied ? `<span class="applied-badge">Applied</span>` : ""}
            </div>
            <div class="job-info">
              <h4 title="${escapeHtml(job.title)}">${escapeHtml(job.title)}</h4>
              <p class="muted small"><b>Company:</b> ${escapeHtml(job.company)}</p>
              <p><b>Location:</b> ${escapeHtml(job.location)}</p>
              <p><b>Type:</b> ${escapeHtml(job.job_type)}</p>
              </div>
          </div>
          
          <div class="job-actions">
            <a class="btn" href="/job_detail/${job.id}">View Details</a>
          </div>
        `;

        jobGrid.appendChild(card);
      });

      // Pagination
      const pagination = document.getElementById("pagination");
      pagination.innerHTML = "";
      if (page > 1) {
        const prev = document.createElement("button");
        prev.textContent = "Previous";
        prev.className = "btn";
        prev.onclick = () => fetchJobs(q, page - 1);
        pagination.appendChild(prev);
      }
      if (data.has_next) {
        const next = document.createElement("button");
        next.textContent = "Next";
        next.className = "btn";
        next.onclick = () => fetchJobs(q, page + 1);
        pagination.appendChild(next);
      }
    } else {
      jobGrid.innerHTML = "<p>No jobs found.</p>";
    }
  } catch (err) {
    console.error("Fetch jobs error:", err);
    showPageAlert("Unable to load jobs right now");
  }
}

// ---------------- Job Details Page ----------------
async function fetchJobDetail() {
  const pathParts = window.location.pathname.split("/");
  const jobId = pathParts[pathParts.length - 1];
  if (!jobId || isNaN(jobId)) return;

  try {
    const res = await fetch(`/api/job/${jobId}`, { credentials: "include" });
    const data = await res.json();
    if (res.ok && data.success && data.job) {
      const job = data.job;

      // Fill details
      document.getElementById("jobTitle").textContent = job.title;
      document.getElementById("jobCompany").textContent = job.company;
      document.getElementById("jobLocation").textContent = job.location;
      document.getElementById("jobExperience").textContent = job.experience || "-";
      document.getElementById("jobSalary").textContent = job.salary ? `${job.salary} LPA` : "-";
      document.getElementById("jobType").textContent = job.job_type || "-";
      document.getElementById("jobDeadline").textContent = job.deadline
        ? new Date(job.deadline).toLocaleDateString()
        : "-";
      document.getElementById("jobDescription").textContent = job.description || "";
      if (job.logo_url) document.getElementById("jobLogo").src = job.logo_url;

      // 🔹 Handle Apply Section
      if (job.applied) {
        document.getElementById("applySection").style.display = "none";
        document.getElementById("alreadyAppliedMsg").style.display = "block";
      }
    } else {
      showPageAlert(data.message || "Job not found");
    }
  } catch (err) {
    console.error("Job detail error:", err);
    showPageAlert("Unable to load job details");
  }

  // Apply form
  const applyForm = document.getElementById("applyForm");
  if (applyForm) {
    applyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formBtn = applyForm.querySelector("button[type=submit]");
      const resumeInput = document.getElementById("resume");
      if (!resumeInput.files.length) {
        showPageAlert("Please select a resume file.");
        return;
      }

      formBtn.disabled = true;
      formBtn.classList.add("loading");

      const formData = new FormData(applyForm);
      try {
        const res = await fetch(`/api/apply/${pathParts[pathParts.length - 1]}`, {
          method: "POST",
          body: formData,
          credentials: "include",
        });
        const resp = await res.json();
        if (res.ok && resp.success) {
          alert(resp.message || "Applied successfully");
          window.location.href = "/user_dashboard";
        } else {
          showPageAlert(resp.message || "Application failed");
        }
      } catch (err) {
        console.error("Apply error:", err);
        showPageAlert("Server error. Please try again.");
      } finally {
        formBtn.disabled = false;
        formBtn.classList.remove("loading");
      }
    });
  }
}

// ---------------- Helper: escape html ----------------
function escapeHtml(str = "") {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ---------------- Init & bindings ----------------
document.getElementById("searchBtn")?.addEventListener("click", () => {
  const query = document.getElementById("searchInput").value;
  fetchJobs(query);
});

// ---------------- Search (Debounced) ----------------
const searchInput = document.getElementById("searchInput");
if (searchInput) {
  let debounceTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const q = searchInput.value.trim();
      fetchJobs(q);
    }, 300);
  });
}

fetchUserProfile();
if (document.getElementById("jobGrid")) fetchJobs();
if (document.getElementById("jobTitle")) fetchJobDetail();
