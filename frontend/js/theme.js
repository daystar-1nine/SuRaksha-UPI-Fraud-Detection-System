// frontend/js/theme.js
// Universal Dark/Light Theme Synchronizer & Persister

document.addEventListener("DOMContentLoaded", () => {
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
});
