(() => {
  "use strict";

  let elements = null;
  let activeRequest = null;
  let requestQueue = Promise.resolve();

  function createElement(tagName, className, text = "") {
    const element = document.createElement(tagName);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function ensureElements() {
    if (elements) return elements;

    const dialog = createElement("dialog", "dashboardDialog");
    dialog.id = "dashboardActionDialog";
    dialog.setAttribute("aria-labelledby", "dashboardActionDialogTitle");
    dialog.setAttribute("aria-describedby", "dashboardActionDialogMessage");

    const form = createElement("form", "dashboardDialogPanel");
    form.method = "dialog";
    const eyebrow = createElement("p", "dashboardDialogEyebrow", "Conferma operazione");
    const title = createElement("h2", "dashboardDialogTitle");
    title.id = "dashboardActionDialogTitle";
    const message = createElement("p", "dashboardDialogMessage");
    message.id = "dashboardActionDialogMessage";

    const field = createElement("label", "dashboardDialogField");
    const fieldLabel = createElement("span", "dashboardDialogFieldLabel");
    const input = createElement("input", "dashboardDialogInput");
    input.type = "text";
    const error = createElement("span", "dashboardDialogError");
    error.id = "dashboardActionDialogError";
    error.setAttribute("role", "alert");
    input.setAttribute("aria-describedby", error.id);
    field.append(fieldLabel, input, error);

    const actions = createElement("div", "dashboardDialogActions");
    const cancelButton = createElement("button", "dashboardDialogCancel", "Annulla");
    cancelButton.type = "button";
    const confirmButton = createElement("button", "dashboardDialogConfirm", "Conferma");
    confirmButton.type = "submit";
    actions.append(cancelButton, confirmButton);
    form.append(eyebrow, title, message, field, actions);
    dialog.append(form);

    const toastRegion = createElement("div", "dashboardToastRegion");
    toastRegion.id = "dashboardToastRegion";
    toastRegion.setAttribute("role", "status");
    toastRegion.setAttribute("aria-live", "polite");
    toastRegion.setAttribute("aria-atomic", "true");
    document.body.append(dialog, toastRegion);

    elements = {
      dialog,
      form,
      eyebrow,
      title,
      message,
      field,
      fieldLabel,
      input,
      error,
      actions,
      cancelButton,
      confirmButton,
      toastRegion,
    };

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      completeFromInput();
    });
    input.addEventListener("input", resetError);
    cancelButton.addEventListener("click", () => completeRequest(null));
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      completeRequest(null);
    });
    return elements;
  }

  function resetError() {
    const ui = ensureElements();
    ui.error.textContent = "";
    ui.error.hidden = true;
    ui.input.removeAttribute("aria-invalid");
  }

  function completeFromInput() {
    if (!activeRequest) return;
    const ui = ensureElements();
    if (activeRequest.mode === "confirm") {
      completeRequest(true);
      return;
    }
    if (activeRequest.mode === "message") {
      completeRequest(true);
      return;
    }
    const value = ui.input.value;
    const validationMessage = activeRequest.validate(value);
    if (validationMessage) {
      ui.error.textContent = validationMessage;
      ui.error.hidden = false;
      ui.input.setAttribute("aria-invalid", "true");
      ui.input.focus();
      return;
    }
    completeRequest(value);
  }

  function completeRequest(value) {
    if (!activeRequest) return;
    const ui = ensureElements();
    const request = activeRequest;
    activeRequest = null;
    if (ui.dialog.open) ui.dialog.close();
    resetError();
    request.resolve(
      request.mode === "confirm"
        ? value === true
        : request.mode === "message"
          ? undefined
          : value
    );
    setTimeout(() => request.restoreFocus?.focus?.(), 0);
  }

  function showDialog(options) {
    const ui = ensureElements();
    const mode = options.mode || "confirm";
    const restoreFocus = document.activeElement;
    ui.eyebrow.textContent = options.eyebrow || (
      mode === "prompt" ? "Dato richiesto" : mode === "message" ? "Informazione" : "Conferma operazione"
    );
    ui.title.textContent = options.title || (
      mode === "prompt" ? "Inserisci un valore" : mode === "message" ? "Operazione completata" : "Conferma"
    );
    ui.message.textContent = options.message || "";
    ui.field.hidden = mode !== "prompt";
    ui.fieldLabel.textContent = options.label || "Valore";
    ui.input.value = options.defaultValue || "";
    ui.input.placeholder = options.placeholder || "";
    ui.cancelButton.hidden = mode === "message";
    ui.cancelButton.textContent = options.cancelLabel || "Annulla";
    ui.confirmButton.textContent = options.confirmLabel || (mode === "message" ? "Chiudi" : "Conferma");
    ui.confirmButton.classList.toggle("danger", options.danger === true);
    ui.dialog.classList.toggle("dashboardDialogDanger", options.danger === true);
    resetError();

    return new Promise((resolve) => {
      activeRequest = {
        mode,
        resolve,
        restoreFocus,
        validate(value) {
          if (options.required && !String(value).trim()) {
            return options.requiredMessage || "Compila questo campo per continuare.";
          }
          return typeof options.validate === "function" ? options.validate(value) : "";
        },
      };
      if (typeof ui.dialog.showModal === "function") ui.dialog.showModal();
      else ui.dialog.setAttribute("open", "");
      setTimeout(() => {
        if (mode === "prompt") {
          ui.input.focus();
          ui.input.select?.();
        } else if (options.danger === true && !ui.cancelButton.hidden) {
          ui.cancelButton.focus();
        } else {
          ui.confirmButton.focus();
        }
      }, 0);
    });
  }

  function enqueue(options) {
    const pending = requestQueue.then(() => showDialog(options));
    requestQueue = pending.catch(() => undefined);
    return pending;
  }

  function confirm(options = {}) {
    return enqueue({ ...options, mode: "confirm" });
  }

  function prompt(options = {}) {
    return enqueue({ ...options, mode: "prompt" });
  }

  function message(options = {}) {
    return enqueue({ ...options, mode: "message" });
  }

  function toast(text, options = {}) {
    const ui = ensureElements();
    const item = createElement("div", `dashboardToast dashboardToast-${options.tone || "info"}`);
    item.textContent = String(text || "");
    ui.toastRegion.append(item);
    const duration = Number.isFinite(options.duration) ? Math.max(0, options.duration) : 4200;
    setTimeout(() => item.remove(), duration);
    return item;
  }

  const api = Object.freeze({
    confirm,
    prompt,
    message,
    toast,
  });
  globalThis.DashboardDialogs = api;
  if (globalThis.window && globalThis.window !== globalThis) {
    globalThis.window.DashboardDialogs = api;
  }
})();
