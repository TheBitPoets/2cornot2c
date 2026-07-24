from __future__ import annotations

from pathlib import Path
import subprocess
import textwrap


def run_dialogs_js(assertions: str) -> None:
    script = rf"""
    const assert = require("node:assert/strict");
    const fs = require("node:fs");
    const vm = require("node:vm");

    class FakeClassList {{
      constructor() {{ this.values = new Set(); }}
      toggle(value, force) {{
        const enabled = force === undefined ? !this.values.has(value) : Boolean(force);
        if (enabled) this.values.add(value);
        else this.values.delete(value);
        return enabled;
      }}
      contains(value) {{ return this.values.has(value); }}
    }}

    class FakeElement {{
      constructor(tagName = "") {{
        this.tagName = tagName.toUpperCase();
        this.children = [];
        this.parentElement = null;
        this.listeners = {{}};
        this.attributes = {{}};
        this.classList = new FakeClassList();
        this.className = "";
        this.id = "";
        this.hidden = false;
        this.open = false;
        this.value = "";
        this.textContent = "";
        this.type = "";
      }}
      append(...children) {{
        for (const child of children) {{
          child.parentElement = this;
          this.children.push(child);
        }}
      }}
      addEventListener(type, handler) {{
        this.listeners[type] = this.listeners[type] || [];
        this.listeners[type].push(handler);
      }}
      dispatchEvent(event) {{
        event.target ||= this;
        for (const handler of this.listeners[event.type] || []) handler(event);
      }}
      setAttribute(name, value) {{
        this.attributes[name] = String(value);
        if (name === "open") this.open = true;
      }}
      removeAttribute(name) {{
        delete this.attributes[name];
        if (name === "open") this.open = false;
      }}
      showModal() {{ this.open = true; }}
      close() {{ this.open = false; }}
      focus() {{ document.activeElement = this; }}
      select() {{ this.selected = true; }}
      remove() {{
        if (!this.parentElement) return;
        this.parentElement.children = this.parentElement.children.filter((child) => child !== this);
        this.parentElement = null;
      }}
    }}

    const document = {{
      body: new FakeElement("body"),
      activeElement: null,
      createElement(tagName) {{ return new FakeElement(tagName); }},
    }};
    const window = {{}};
    const context = {{
      assert,
      console,
      document,
      window,
      setTimeout(handler) {{ handler(); return 1; }},
    }};
    context.globalThis = context;
    const find = (root, predicate) => {{
      if (predicate(root)) return root;
      for (const child of root.children || []) {{
        const match = find(child, predicate);
        if (match) return match;
      }}
      return null;
    }};
    context.find = find;

    const source = fs.readFileSync("tools/dashboard_dialogs.js", "utf8");
    vm.runInNewContext(source, context);
    vm.runInNewContext(`(async () => {{
      const flush = async () => {{
        await Promise.resolve();
        await Promise.resolve();
        await Promise.resolve();
      }};
      {assertions}
    }})().catch((error) => {{
      console.error(error);
      process.exitCode = 1;
    }});`, context);
    """
    subprocess.run(["node", "-e", textwrap.dedent(script)], check=True)


def test_shared_dialog_supports_confirm_prompt_validation_and_queue() -> None:
    run_dialogs_js(
        """
        const opener = document.createElement("button");
        document.body.append(opener);
        opener.focus();

        const first = DashboardDialogs.confirm({
          title: "Elimina bozza",
          message: "Operazione irreversibile",
          confirmLabel: "Elimina",
          danger: true,
        });
        const second = DashboardDialogs.prompt({
          title: "Nome progetto",
          required: true,
        });
        await flush();

        const dialog = find(document.body, (item) => item.id === "dashboardActionDialog");
        const title = find(dialog, (item) => item.id === "dashboardActionDialogTitle");
        const form = find(dialog, (item) => item.tagName === "FORM");
        const confirmButton = find(dialog, (item) => item.className === "dashboardDialogConfirm");
        assert.equal(dialog.open, true);
        assert.equal(title.textContent, "Elimina bozza");
        assert.equal(confirmButton.classList.contains("danger"), true);
        form.dispatchEvent({ type: "submit", preventDefault() {} });
        assert.equal(await first, true);

        await flush();
        const input = find(dialog, (item) => item.className === "dashboardDialogInput");
        const error = find(dialog, (item) => item.id === "dashboardActionDialogError");
        assert.equal(title.textContent, "Nome progetto");
        form.dispatchEvent({ type: "submit", preventDefault() {} });
        assert.equal(dialog.open, true);
        assert.equal(error.hidden, false);

        input.value = "<script>test</script>";
        form.dispatchEvent({ type: "submit", preventDefault() {} });
        assert.equal(await second, "<script>test</script>");
        assert.equal(opener, document.activeElement);
        """
    )


def test_shared_dialog_escape_cancels_without_native_dialogs() -> None:
    run_dialogs_js(
        """
        const pending = DashboardDialogs.confirm({ title: "Conferma" });
        await flush();
        const dialog = find(document.body, (item) => item.id === "dashboardActionDialog");
        dialog.dispatchEvent({ type: "cancel", preventDefault() { this.prevented = true; } });
        assert.equal(await pending, false);
        assert.equal(dialog.open, false);
        """
    )


def test_dashboard_pages_load_shared_dialog_assets_before_application_scripts() -> None:
    for name, application_script in (
        ("course_board.html", "course_board.js"),
        ("assignment_dashboard.html", "assignment_dashboard.js"),
    ):
        html = (Path("tools") / name).read_text(encoding="utf-8")
        assert "dashboard_dialogs.css" in html
        assert html.index("dashboard_dialogs.js") < html.index(application_script)
