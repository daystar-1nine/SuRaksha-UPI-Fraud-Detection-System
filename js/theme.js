// frontend/js/theme.js
// Universal Dark/Light Theme Synchronizer & Persister

function initThemeAndProfile() {
    const toggleBtn = document.getElementById("theme-toggle");
    const icon = document.getElementById("theme-icon");

    function updateIcon(isDark) {
        if (icon) {
            icon.textContent = isDark ? "light_mode" : "dark_mode";
        }
    }

    // Set initial icon state
    const isDark = document.documentElement.classList.contains("dark");
    updateIcon(isDark);

    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            document.documentElement.classList.toggle("dark");
            const currentlyDark = document.documentElement.classList.contains("dark");
            localStorage.setItem("theme", currentlyDark ? "dark" : "light");
            updateIcon(currentlyDark);

            // Broadcast theme change to other open tabs
            window.dispatchEvent(new Event("themechanged"));
        });
    }

    // Synchronize theme changes across multiple open tabs in real-time
    window.addEventListener("storage", (e) => {
        if (e.key === "theme") {
            const isNewThemeDark = e.newValue === "dark";
            document.documentElement.classList.toggle("dark", isNewThemeDark);
            updateIcon(isNewThemeDark);
        }
    });

    // Populate copyright year automatically
    const yearEl = document.getElementById("year");
    if (yearEl) {
        yearEl.textContent = new Date().getFullYear();
    }

    // 👤 Universal Navbar Profile Sync & Navigation
    const profileBtn = document.getElementById("profile-settings-btn");
    const navbarImg = document.getElementById("navbar-profile-img");
    const navbarIcon = document.getElementById("navbar-profile-icon");

    function syncNavbarProfile() {
        const photo = localStorage.getItem("profile_photo");
        if (photo) {
            if (navbarImg) {
                navbarImg.src = photo;
                navbarImg.classList.remove("hidden");
            }
            if (navbarIcon) {
                navbarIcon.classList.add("hidden");
            }
        } else {
            if (navbarImg) {
                navbarImg.src = "";
                navbarImg.classList.add("hidden");
            }
            if (navbarIcon) {
                navbarIcon.classList.remove("hidden");
            }
        }
    }

    syncNavbarProfile();

    // Listen for custom profile changes (storage sync)
    window.addEventListener("storage", (e) => {
        if (e.key === "profile_photo") {
            syncNavbarProfile();
        }
    });
}

// 🌐 Global Profile Redirect
// Placed entirely outside init block to ensure it's available immediately to inline onclick handlers
window.openProfileRedirect = function(e) {
    if (e) e.preventDefault();
    window.location.href = "profile.html";
};

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeAndProfile);
} else {
    initThemeAndProfile();
}
