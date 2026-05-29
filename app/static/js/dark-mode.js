/**
 * dark-mode.js — Gerencia alternância entre tema claro e escuro.
 *
 * - Usuários autenticados: preferência salva no banco via POST /contas/dark-mode/
 * - Usuários anônimos: preferência salva no localStorage
 * - A chave data-bs-theme no <html> é definida pelo servidor (authenticated)
 *   ou pelo JS na inicialização (anonymous).
 */

(function () {
  "use strict";

  const STORAGE_KEY = "devocional-dark-mode";
  const ENDPOINT = "/contas/dark-mode/";
  const html = document.documentElement;

  /** Obtém o cookie de CSRF para requests autenticados. */
  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  /** Aplica o tema ao elemento <html> e atualiza o ícone do botão. */
  function applyTheme(isDark) {
    html.setAttribute("data-bs-theme", isDark ? "dark" : "light");
    const icon = document.getElementById("dark-mode-icon");
    if (icon) {
      icon.className = isDark ? "bi bi-sun-fill" : "bi bi-moon-fill";
    }
  }

  /** Alterna o tema e persiste a preferência. */
  function toggleDarkMode() {
    const isDark = html.getAttribute("data-bs-theme") === "dark";
    const next = !isDark;

    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next ? "dark" : "light");

    // Persiste no banco se autenticado (falha silenciosa — localStorage já foi salvo)
    if (document.body.dataset.authenticated === "true") {
      fetch(ENDPOINT, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "Content-Type": "application/json",
        },
        credentials: "same-origin",
      }).catch(function () {});
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    const isAuthenticated = document.body.dataset.authenticated === "true";

    // Para usuários não autenticados, aplica preferência do localStorage
    if (!isAuthenticated) {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        applyTheme(saved === "dark");
      }
    }

    // Conecta o botão de toggle
    const btn = document.getElementById("btn-dark-mode");
    if (btn) {
      btn.addEventListener("click", toggleDarkMode);
    }
  });
})();
