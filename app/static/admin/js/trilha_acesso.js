/**
 * Mostra/oculta o fieldset "Controle de Acesso por Grupo" conforme o
 * valor do campo #id_acesso na página de edição da Trilha.
 */
(function () {
  "use strict";

  function toggleGrupos() {
    var acessoField = document.getElementById("id_acesso");
    if (!acessoField) return;

    // O fieldset gerado pelo Django admin tem classe "module" e contém o campo .field-grupos.
    // Buscamos o fieldset pai do campo grupos para ocultar/exibir o bloco inteiro.
    var gruposField = document.querySelector(".field-grupos");
    if (!gruposField) return;

    var fieldset = gruposField.closest("fieldset");
    if (!fieldset) return;

    var visivel = acessoField.value === "PERMISSAO_ESPECIFICA";
    fieldset.style.display = visivel ? "" : "none";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var acessoField = document.getElementById("id_acesso");
    if (!acessoField) return;

    toggleGrupos();
    acessoField.addEventListener("change", toggleGrupos);
  });
})();
