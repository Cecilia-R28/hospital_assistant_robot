const DEBUG = new URLSearchParams(location.search).has("debug");
let lastMenu = "home";

function show(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function showConfirm(title, text, debug) {
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-text").textContent = text;
  document.getElementById("confirm-debug").textContent = debug || "";
  show("confirm");
}

// Boutons de navigation (accueil, retour, annuler)
document.querySelectorAll("[data-goto]").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = btn.dataset.goto;
    if (target.startsWith("menu-")) lastMenu = target;
    show(target);
  });
});

// Retour depuis la confirmation : revient au dernier sous-menu
document.getElementById("confirm-back").addEventListener("click", () => show(lastMenu));

// Choix d'un élément (service, destination, sujet)
document.querySelectorAll("[data-item]").forEach(btn => {
  btn.addEventListener("click", async () => {
    const label = btn.dataset.label;
    if (btn.dataset.available !== "true") {
      showConfirm("En préparation", label + " n'est pas encore disponible.");
      return;
    }
    try {
      const response = await fetch("/api/request", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({category: btn.dataset.category, item: btn.dataset.item}),
      });
      const data = await response.json();
      if (data.ok) {
        showConfirm(data.title, data.message, DEBUG ? JSON.stringify(data.request) : "");
      } else {
        showConfirm("Erreur", data.error);
      }
    } catch (err) {
      showConfirm("Erreur", "Le serveur HIAR ne répond pas.");
    }
  });
});
