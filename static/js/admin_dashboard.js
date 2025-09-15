// ---------------- Helpers ----------------
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

// ---------------- Logout ----------------
document.getElementById("logoutBtn")?.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST", credentials: "include" });
  window.location.href = "/login";
});

// ---------------- Auto-hide alerts ----------------
setTimeout(() => {
  document.querySelectorAll(".alert").forEach(el => el.style.display = "none");
}, 4000);

// ---------------- API Form Handler ----------------
function handleFormWithAPI(formId, apiUrl, method = "POST") {
  const form = document.getElementById(formId);
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const btn = form.querySelector(".btn[type=submit]");
    if (btn) {
      btn.classList.add("loading");
      btn.disabled = true;
    }

    // Check if employer has logo
    const logoField = document.getElementById("logo");
    const logoFile = logoField?.files[0];
    const hasLogoGroup = document.getElementById("logoUploadGroup");

    try {
      if (logoFile && hasLogoGroup && hasLogoGroup.style.display !== "none") {
        // First-time logo upload
        const logoFormData = new FormData();
        logoFormData.append("logo", logoFile);

        const logoRes = await fetch("/api/admin/upload-logo", {
          method: "POST",
          body: logoFormData,
          credentials: "include",
        });

        const logoData = await logoRes.json();
        if (!logoRes.ok || !logoData.success) {
          showPageAlert(logoData.message || "Logo upload failed");
          return;
        }

        // Hide logo upload group permanently after success
        hasLogoGroup.style.display = "none";
        showPageAlert("Logo uploaded successfully", "success");

        // Update local session data so refresh not required
        if (window.sessionUser) {
          window.sessionUser.logo_filename = logoData.logo_url.split("/").pop();
        }
      }

      
      const formData = new FormData(form);
      formData.delete("logo"); // skip logo, already uploaded

      const res = await fetch(apiUrl, {
        method,
        body: formData, 
        credentials: "include",
      });

      const data = await res.json();
      if (res.ok && data.success) {
        showPageAlert(data.message || "Job posted successfully", "success");
        form.reset();
        fetchJobs();
      } else {
        showPageAlert(data.message || "Something went wrong");
      }
    } catch (err) {
      console.error("Network error:", err);
      showPageAlert("Network error: " + err.message);
    } finally {
      if (btn) {
        btn.classList.remove("loading");
        btn.disabled = false;
      }
    }
  });
}

// ---------------- Admin Profile ----------------
async function fetchAdminProfile() {
  try {
    const res = await fetch("/api/session", { credentials: "include" });
    if (!res.ok) return;
    const data = await res.json();

    if (data.success && data.user && data.user.role === "Employer") {
      window.sessionUser = data.user; // cache session
      document.getElementById("userName").textContent = data.user.organization_name || "-";
      document.getElementById("userEmail").textContent = data.user.organization_email || "-";
      document.getElementById("userMobile").textContent = data.user.mobile || "-";

      if (data.user.profile_pic) {
        document.getElementById("profilePic").src = "/uploads/profile_pics/" + data.user.profile_pic;
      }

      // Hide logo field if already uploaded
      if (data.user.logo_filename) {
        const logoGroup = document.getElementById("logoUploadGroup");
        if (logoGroup) logoGroup.style.display = "none";
      }
    }
  } catch (err) {
    console.error("Profile fetch error:", err);
  }
}

// ---------------- Jobs List ----------------
async function fetchJobs(query = "") {
  try {
    const res = await fetch(`/api/admin/jobs?q=${encodeURIComponent(query)}`, { credentials: "include" });
    if (!res.ok) {
      console.error("Fetch jobs error:", await res.text());
      showPageAlert("Error loading jobs");
      return;
    }

    const data = await res.json();
    const jobGrid = document.getElementById("jobGrid");
    jobGrid.innerHTML = "";

    if (data.success && data.jobs.length) {
      data.jobs.forEach(job => {
        const card = document.createElement("div");
        card.className = "job-card";

        card.innerHTML = `
          <div class="job-header">
            <div class="job-logo">
              <img src="${job.logo_url || "/static/images/default-logo.png"}" alt="Logo">
            </div>
            <span class="badge">${job.applications_count || 0} Applications</span>
          </div>
          <h4>${job.title}</h4>
          <p><b>Company:</b> ${job.company || "N/A"}</p>
          <p><b>Experience:</b> ${job.experience}</p>
          <p><b>Salary:</b> ${job.salary} LPA</p>
          <p><b>Job Type:</b> ${job.job_type}</p>
          <p><b>Deadline:</b> ${job.deadline ? new Date(job.deadline).toLocaleDateString() : "N/A"}</p>
          <p><b>Location:</b> ${job.location}</p>
          <div class="job-actions">
            <a href="/applications?id=${job.id}" class="btn">View Applications</a>
            <button class="btn deleteBtn" data-id="${job.id}">Delete</button>
          </div>
        `;

        jobGrid.appendChild(card);
      });

      // Delete buttons
      document.querySelectorAll(".deleteBtn").forEach(btn => {
        btn.addEventListener("click", async () => {
          if (!confirm("Delete this job?")) return;
          try {
            const res = await fetch(`/api/admin/jobs/${btn.dataset.id}`, {
              method: "DELETE",
              credentials: "include",
            });
            const result = await res.json();
            if (res.ok && result.success) {
              showPageAlert(result.message, "success");
              fetchJobs(query);
            } else {
              showPageAlert(result.message || "Failed to delete job");
            }
          } catch (err) {
            console.error("Delete job error:", err);
            showPageAlert("Error deleting job");
          }
        });
      });
    } else {
      jobGrid.innerHTML = "<p>No jobs found.</p>";
    }

  } catch (err) {
    console.error("Job fetch error:", err);
    showPageAlert("Error loading jobs");
  }
}

// ---------------- Applications Page ----------------
async function fetchApplications(jobId) {
  try {
    const res = await fetch(`/api/admin/applications/${jobId}`, { credentials: "include" });
    if (!res.ok) {
      console.error("Fetch applications failed:", await res.text());
      showPageAlert("Error loading applications");
      return;
    }
    const data = await res.json();

    const tbody = document.querySelector("#applicationsTable tbody");
    tbody.innerHTML = "";

    if (data.success) {
      if (data.job) {
        document.getElementById("employerName").textContent = data.job.employer_name || "-";
        document.getElementById("userName").textContent = data.job.organization_name || data.job.company || "-";
        document.getElementById("userEmail").textContent = data.job.organization_email || "-";
        document.getElementById("userMobile").textContent = data.job.organization_mobile || "-";

        if (data.job.logo_filename) {
          document.getElementById("profilePic").src = "/uploads/logos/" + data.job.logo_filename;
        } else {
          document.getElementById("profilePic").src = "/static/images/default-user.png";
        }
      }


      if (data.applicants.length) {
        data.applicants.forEach((app, i) => {
          const row = document.createElement("tr");
          row.innerHTML = `
            <td>${i + 1}</td>
            <td>${app.name} <br><small>${app.email}</small></td>
            <td>${data.job.title}</td>
            <td>${data.job.experience}</td>
            <td>${data.job.salary} LPA</td>
            <td>${data.job.job_type}</td>
            <td>${data.job.deadline ? new Date(data.job.deadline).toLocaleDateString() : "N/A"}</td>
            <td>${
              app.resume_filename
                ? `<a href="/api/admin/resumes/${app.resume_filename}" class="btn" target="_blank">Download</a>`
                : "<span class='no-resume'>No Resume</span>"
            }</td>
            <td>${new Date(app.applied_at).toLocaleString()}</td>
          `;
          tbody.appendChild(row);
        });
      } else {
        tbody.innerHTML = "<tr><td colspan='9'>No applications found</td></tr>";
      }
    } else {
      tbody.innerHTML = "<tr><td colspan='9'>No applications found</td></tr>";
    }
  } catch (err) {
    console.error("Applications fetch error:", err);
    showPageAlert("Error loading applications");
  }
}


// ---------------- Search (Debounced) ----------------
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        fetchJobs(query);
      }, 300);
    });
  }

  // Initialize dashboard
  handleFormWithAPI("jobPostForm", "/api/admin/jobs");

  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("id");

  if (window.location.pathname.includes("/applications") && jobId) {
    fetchApplications(jobId);
  } else {
    fetchAdminProfile();
    fetchJobs();
  }
});
