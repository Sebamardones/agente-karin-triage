/* Karin Triage · interacción del puesto de trabajo.
   Abre casos en el panel sin recargar, muestra a qué bandeja pasó cada caso,
   abre el siguiente, toma la cita de descarte desde la selección del relato y
   ofrece atajos de teclado. Ninguna acción decide sola: los atajos llevan el
   foco al botón y la persona confirma con Enter. Detalle en
   docs/plan-interaccion.md. */
(function () {
  "use strict";
  var escritorio = window.matchMedia("(min-width: 64rem)");
  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)");

  function porId(id) { return document.getElementById(id); }

  // --- A8: avisos de paso entre bandejas -----------------------------------
  function avisar(texto) {
    var zona = porId("avisos");
    if (!zona || !texto) return;
    var item = document.createElement("p");
    item.className = "aviso-flotante";
    // Icono del sprite de la página: «check» para confirmaciones, «info» para indicaciones.
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "icono");
    svg.setAttribute("aria-hidden", "true");
    var uso = document.createElementNS("http://www.w3.org/2000/svg", "use");
    uso.setAttribute("href", /^Selecciona/.test(texto) ? "#i-info" : "#i-check");
    svg.appendChild(uso);
    item.appendChild(svg);
    item.appendChild(document.createTextNode(texto));
    zona.appendChild(item);
    setTimeout(function () {
      item.classList.add("saliendo");
      setTimeout(function () { item.remove(); }, reducido.matches ? 0 : 250);
    }, 4000);
  }

  // --- A5: errores del servidor (htmx no intercambia respuestas 4xx/5xx) ----
  document.addEventListener("htmx:responseError", function (e) {
    var aviso = porId("aviso-revision");
    if (!aviso) return;
    var texto = "No se pudo registrar la revisión.";
    try { texto = JSON.parse(e.detail.xhr.responseText).detail || texto; } catch (_) {}
    aviso.textContent = texto;
    aviso.hidden = true;
    void aviso.offsetWidth; // reinicia la animación si el error se repite
    aviso.hidden = false;
    aviso.scrollIntoView({ block: "nearest" });
  });

  // --- Selección de la tarjeta abierta --------------------------------------
  function marcarSeleccion() {
    var panel = porId("panel-caso");
    var actual = panel ? panel.getAttribute("data-caso") : null;
    document.querySelectorAll(".tarjeta-caso").forEach(function (tarjeta) {
      var elegida = tarjeta.getAttribute("data-id") === actual;
      tarjeta.classList.toggle("seleccionada", elegida);
      var enlace = tarjeta.querySelector(".tarjeta-enlace");
      if (!enlace) return;
      if (elegida) enlace.setAttribute("aria-current", "true");
      else enlace.removeAttribute("aria-current");
    });
  }

  // --- A6: abrir un caso en el panel ----------------------------------------
  function abrirCaso(id, bandeja, enfocarPanel, reemplazar) {
    var consulta = bandeja ? "?bandeja=" + encodeURIComponent(bandeja) : "";
    return htmx.ajax("GET", "/casos/" + id + "/panel" + consulta,
      { target: "#panel", swap: "innerHTML" }).then(function () {
      history[reemplazar ? "replaceState" : "pushState"]({ caso: id }, "", "/casos/" + id + consulta);
      var puesto = document.querySelector(".puesto");
      if (puesto) puesto.classList.add("con-caso");
      var titulo = porId("titulo-caso");
      if (titulo) document.title = porId("panel-caso").querySelector(".antetitulo").textContent.split(" · ")[0] + " · Karin Triage";
      marcarSeleccion();
      // Si la persona venía de abajo (formulario de decisión), vuelve al veredicto.
      var arriba = porId("panel").getBoundingClientRect().top;
      if (arriba < 0) window.scrollTo({ top: window.scrollY + arriba - 16, behavior: reducido.matches ? "auto" : "smooth" });
      if (enfocarPanel) porId("panel").focus({ preventScroll: true });
    });
  }

  document.addEventListener("click", function (e) {
    var enlace = e.target.closest(".tarjeta-enlace");
    if (!enlace || !escritorio.matches || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    abrirCaso(enlace.getAttribute("data-caso"), enlace.getAttribute("data-bandeja"), false);
  });
  window.addEventListener("popstate", function () { window.location.reload(); });

  // --- A7 + A8: la revisión quedó registrada ---------------------------------
  document.addEventListener("revisionRegistrada", function (e) {
    var datos = e.detail || {};
    var bandeja = datos.bandeja || "";
    var destino = datos.siguiente ? "/casos/" + datos.siguiente + "?bandeja=" + bandeja : "/?bandeja=" + bandeja;
    if (!escritorio.matches || !porId("bandeja-viva")) {
      try { sessionStorage.setItem("karin-aviso", datos.mensaje || ""); } catch (_) {}
      window.location.href = destino;
      return;
    }
    avisar(datos.mensaje);
    var tarjeta = document.querySelector('.tarjeta-caso[data-id="' + datos.caso + '"]');
    function continuar() {
      htmx.trigger(porId("bandeja-viva"), "refrescar");
      if (datos.siguiente) {
        abrirCaso(datos.siguiente, bandeja, true);
      } else {
        porId("panel").innerHTML = '<div class="panel-vacio"><h2>Bandeja al día</h2>' +
          "<p>No quedan casos en esta bandeja. Buen trabajo.</p></div>";
        history.pushState({}, "", "/?bandeja=" + bandeja);
      }
    }
    if (tarjeta && !reducido.matches) {
      tarjeta.classList.add("saliendo");
      setTimeout(continuar, 250);
    } else {
      continuar();
    }
  });

  // --- Acciones de decisión: Corregir y Descartar se despliegan en el panel --
  function desplegar(id, boton) {
    ["form-corregir", "form-descartar"].forEach(function (otro) {
      var form = porId(otro);
      if (!form) return;
      form.hidden = otro === id ? !form.hidden : true;
    });
    document.querySelectorAll("[data-abre]").forEach(function (b) {
      var form = porId(b.getAttribute("data-abre"));
      b.setAttribute("aria-expanded", form && !form.hidden ? "true" : "false");
    });
    var abierto = porId(id);
    if (abierto && !abierto.hidden) {
      var primero = abierto.querySelector("input:not([type=hidden]), textarea, select");
      if (primero) primero.focus();
      abierto.scrollIntoView({ block: "nearest", behavior: reducido.matches ? "auto" : "smooth" });
    }
  }
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-abre]");
    if (boton) desplegar(boton.getAttribute("data-abre"), boton);
  });

  // --- Cita de descarte desde la selección del relato ------------------------
  function seleccionEnRelato() {
    var seleccion = window.getSelection();
    var relato = porId("relato");
    if (!seleccion || seleccion.isCollapsed || !relato) return "";
    if (!relato.contains(seleccion.anchorNode) || !relato.contains(seleccion.focusNode)) return "";
    return seleccion.toString().replace(/\s+/g, " ").trim();
  }
  function usarSeleccion() {
    var texto = seleccionEnRelato();
    var campo = porId("cita-respaldo");
    var form = porId("form-descartar");
    if (!texto || !campo || !form || form.hidden) return false;
    campo.value = texto;
    campo.classList.remove("recien-llenado");
    void campo.offsetWidth;
    campo.classList.add("recien-llenado");
    return true;
  }
  document.addEventListener("mouseup", function (e) {
    if (e.target.closest && e.target.closest("#relato")) usarSeleccion();
  });
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-usar-seleccion]") && !usarSeleccion()) {
      avisar("Selecciona primero una frase del relato.");
    }
  });

  // --- A9: resaltar la cita al pasar por su número en la lista ---------------
  function resaltarCita(e, activo) {
    var item = e.target.closest && e.target.closest(".citas li[data-cita]");
    if (!item) return;
    var marca = porId("cita-" + item.getAttribute("data-cita"));
    if (marca) marca.classList.toggle("activa", activo);
  }
  document.addEventListener("mouseover", function (e) { resaltarCita(e, true); });
  document.addEventListener("mouseout", function (e) { resaltarCita(e, false); });

  // --- A3: tarjetas nuevas tras el refresco, y foco conservado ---------------
  var previas = null;
  var focoPrevio = null;
  document.addEventListener("htmx:beforeSwap", function (e) {
    if (!e.detail.target || e.detail.target.id !== "bandeja-viva") return;
    previas = new Set(Array.from(e.detail.target.querySelectorAll(".tarjeta-caso"),
      function (t) { return t.getAttribute("data-id"); }));
    var activo = document.activeElement;
    focoPrevio = activo && e.detail.target.contains(activo) && activo.getAttribute("href")
      ? activo.getAttribute("href") : null;
  });
  document.addEventListener("htmx:afterSettle", function (e) {
    if (previas) {
      document.querySelectorAll("#bandeja-viva .tarjeta-caso").forEach(function (t) {
        if (!previas.has(t.getAttribute("data-id"))) t.classList.add("fila-nueva");
      });
      if (focoPrevio) {
        var destino = document.querySelector('#bandeja-viva a[href="' + focoPrevio + '"]');
        if (destino) destino.focus({ preventScroll: true });
      }
      previas = null;
      focoPrevio = null;
    }
    marcarSeleccion();
  });

  // --- Ventana de bienvenida: una vez por sesión y por rol, y a pedido -------
  function abrirGuia() {
    var guia = porId("guia");
    if (!guia || guia.open) return false;
    guia.showModal();
    return true;
  }
  function mostrarGuiaSiCorresponde() {
    var guia = porId("guia");
    if (!guia) return;
    var pedida = new URLSearchParams(window.location.search).get("guia") === "1";
    var clave = "karin-guia-" + guia.getAttribute("data-rol");
    var vista = false;
    try { vista = sessionStorage.getItem(clave) === "1"; } catch (_) {}
    if (pedida || !vista) {
      abrirGuia();
      try { sessionStorage.setItem(clave, "1"); } catch (_) {}
      if (pedida) history.replaceState(history.state, "", window.location.pathname);
    }
  }
  document.addEventListener("click", function (e) {
    var enlace = e.target.closest("[data-abrir-guia]");
    if (enlace && abrirGuia()) e.preventDefault();
  });

  // --- Menú principal: plegable en pantallas angostas; submenús se cierran solos
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-menu]");
    if (boton) {
      var abierto = boton.getAttribute("aria-expanded") === "true";
      boton.setAttribute("aria-expanded", abierto ? "false" : "true");
      porId("menu-principal").classList.toggle("abierto", !abierto);
      return;
    }
    document.querySelectorAll(".menu-grupo[open]").forEach(function (grupo) {
      if (!grupo.contains(e.target)) grupo.open = false;
    });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.querySelectorAll(".menu-grupo[open]").forEach(function (grupo) {
      grupo.open = false;
      grupo.querySelector("summary").focus();
    });
  });

  // --- Atajos de teclado ------------------------------------------------------
  function enfocarAccion(id) {
    var boton = porId(id);
    if (!boton) return;
    boton.focus();
    boton.scrollIntoView({ block: "nearest" });
    if (boton.hasAttribute("data-abre")) boton.click();
  }
  function moverEnCola(paso) {
    var enlaces = Array.from(document.querySelectorAll(".tarjeta-enlace"));
    if (!enlaces.length) return;
    var actual = enlaces.findIndex(function (a) {
      return a.closest(".tarjeta-caso").classList.contains("seleccionada");
    });
    var indice = actual < 0 ? 0 : Math.min(enlaces.length - 1, Math.max(0, actual + paso));
    var enlace = enlaces[indice];
    enlace.focus();
    if (escritorio.matches) abrirCaso(enlace.getAttribute("data-caso"), enlace.getAttribute("data-bandeja"), false);
  }
  function alternarAyuda() {
    var dialogo = porId("ayuda-atajos");
    if (!dialogo) return;
    if (dialogo.open) dialogo.close(); else dialogo.showModal();
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-abrir-ayuda]")) alternarAyuda();
  });
  document.addEventListener("keydown", function (e) {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target.closest && e.target.closest("input, textarea, select, [contenteditable]")) return;
    if (e.key === "?") { e.preventDefault(); alternarAyuda(); return; }
    var dialogo = porId("ayuda-atajos");
    if (dialogo && dialogo.open) return;
    if (e.key === "j" || e.key === "k") { e.preventDefault(); moverEnCola(e.key === "j" ? 1 : -1); }
    else if (e.key === "c") { e.preventDefault(); enfocarAccion("accion-confirmar"); }
    else if (e.key === "e") { e.preventDefault(); enfocarAccion("accion-corregir"); }
    else if (e.key === "d") { e.preventDefault(); enfocarAccion("accion-descartar"); }
  });

  // --- A1: estado de envío en los formularios que ejecutan la IA -------------
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form.matches("[data-carga]") || !form.checkValidity()) return;
    var boton = form.querySelector("button");
    form.classList.add("enviando");
    form.setAttribute("aria-busy", "true");
    if (boton) {
      boton.textContent = form.getAttribute("data-carga");
      setTimeout(function () { boton.disabled = true; }, 0);
    }
  });

  // --- Ingreso de caso: contador de caracteres y relato de ejemplo ------------
  var EJEMPLO_RELATO = "Trabajo como vendedora en la sucursal del centro desde enero. Desde hace tres " +
    "meses, el jefe de local me grita y me descalifica frente a clientes y compañeros, me asigna " +
    "los peores turnos sin explicación y dice en las reuniones que no sirvo para el puesto. " +
    "Ocurre casi todas las semanas y dos compañeros lo han presenciado. No ha habido contacto " +
    "físico ni amenazas, pero estoy con licencia por estrés desde la semana pasada.";
  function contarRelato() {
    var campo = porId("relato-ingreso");
    var contador = porId("contador-relato");
    if (campo && contador) contador.textContent = campo.value.length + " de 6000 caracteres";
  }
  document.addEventListener("input", function (e) {
    if (e.target.id === "relato-ingreso") contarRelato();
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest("[data-ejemplo-relato]")) return;
    var campo = porId("relato-ingreso");
    if (!campo) return;
    campo.value = EJEMPLO_RELATO;
    contarRelato();
    campo.focus();
  });

  // --- Al cargar: aviso pendiente (móvil) y selección inicial ----------------
  // --- Entrada inicial: orden del escalonado y cifras que cuentan hasta su valor
  function prepararEntrada() {
    [".metrica", ".pestana", ".tarjeta-caso", ".bloque-ingreso", ".pie-interior > *"].forEach(function (selector) {
      document.querySelectorAll(selector).forEach(function (el, i) { el.style.setProperty("--i", i); });
    });
    if (!reducido.matches) {
      document.querySelectorAll(".metrica .cifra, .metrica .metrica-valor").forEach(function (el) {
        var texto = el.textContent.trim();
        var final = parseInt(texto, 10);
        if (isNaN(final) || final <= 0) return;
        var sufijo = texto.replace(/^\d+/, "");
        var inicio = null;
        function paso(t) {
          if (inicio === null) inicio = t;
          var avance = Math.min(1, (t - inicio) / 700);
          el.textContent = Math.round(final * (1 - Math.pow(1 - avance, 3))) + sufijo;
          if (avance < 1) requestAnimationFrame(paso);
        }
        requestAnimationFrame(paso);
      });
    }
    // Las entradas solo corren al cargar: los refrescos de la cola no se animan de nuevo.
    setTimeout(function () { document.body.classList.remove("entrada-inicial"); }, 1600);
  }

  document.addEventListener("DOMContentLoaded", function () {
    prepararEntrada();
    try {
      var pendiente = sessionStorage.getItem("karin-aviso");
      if (pendiente) { sessionStorage.removeItem("karin-aviso"); avisar(pendiente); }
    } catch (_) {}
    marcarSeleccion();
    mostrarGuiaSiCorresponde();
  });
})();
