// Vanilla JS, sans dépendance : menu mobile, bascule de thème, apparition au
// scroll, copie de l'email.

document.documentElement.classList.add("js");

// --- Menu mobile ---
const navToggle = document.getElementById("nav-toggle");
const nav = document.getElementById("nav");

if (navToggle && nav) {
  navToggle.addEventListener("click", () => {
    const ouvert = nav.classList.toggle("nav-ouverte");
    navToggle.setAttribute("aria-expanded", String(ouvert));
  });

  nav.querySelectorAll("a").forEach((lien) => {
    lien.addEventListener("click", () => {
      nav.classList.remove("nav-ouverte");
      navToggle.setAttribute("aria-expanded", "false");
    });
  });
}

// --- Bascule de thème (persistée) ---
const themeToggle = document.getElementById("theme-toggle");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const clair = document.documentElement.dataset.theme === "light";
    if (clair) {
      delete document.documentElement.dataset.theme;
      localStorage.removeItem("theme");
    } else {
      document.documentElement.dataset.theme = "light";
      localStorage.setItem("theme", "light");
    }
  });
}

// --- Apparition au scroll ---
const elements = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window && elements.length) {
  const observateur = new IntersectionObserver(
    (entrees, obs) => {
      entrees.forEach((entree) => {
        if (entree.isIntersecting) {
          entree.target.classList.add("revele");
          obs.unobserve(entree.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );
  elements.forEach((el) => observateur.observe(el));
} else {
  elements.forEach((el) => el.classList.add("revele"));
}

// --- Copier l'email ---
const copyEmail = document.getElementById("copy-email");

if (copyEmail) {
  copyEmail.addEventListener("click", async () => {
    const email = copyEmail.dataset.email;
    const texteInitial = copyEmail.textContent;
    try {
      await navigator.clipboard.writeText(email);
      copyEmail.textContent = "Copié !";
      copyEmail.classList.add("copie");
    } catch {
      // Presse-papiers indisponible (permissions, contexte non sécurisé...) : on ignore.
      return;
    }
    setTimeout(() => {
      copyEmail.textContent = texteInitial;
      copyEmail.classList.remove("copie");
    }, 1500);
  });
}
