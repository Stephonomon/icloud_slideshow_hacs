/**
 * iCloud Slideshow Card
 *
 * Renders the rotating camera image with a thin progress bar showing how long
 * is left before the next photo, and a fullscreen mode that keeps rotating.
 *
 * Shipped with the icloud_shared_album integration and registered
 * automatically — no Lovelace resource entry needed.
 */

const CARD_VERSION = "1.2.0";
const CARD_TAG = "icloud-slideshow-card";

const DEFAULTS = {
  fit: "cover",
  aspect_ratio: "16:9",
  show_progress: true,
  progress_position: "bottom",
  progress_height: 4,
  transition: 700,
  tap_action: "fullscreen",
};

const TEMPLATE = `
  <style>
    :host { display: block; }
    ha-card { overflow: hidden; position: relative; }
    .frame {
      position: relative;
      width: 100%;
      aspect-ratio: var(--ics-ratio, 16 / 9);
      background: #000;
      overflow: hidden;
    }
    .frame.tappable { cursor: pointer; }
    .layer {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: var(--ics-fit, cover);
      opacity: 0;
      transition: opacity var(--ics-transition, 700ms) ease-in-out;
    }
    .layer.show { opacity: 1; }
    .progress {
      position: absolute;
      left: 0;
      right: 0;
      height: var(--ics-progress-height, 4px);
      background: rgba(0, 0, 0, 0.35);
      box-shadow: inset 0 0 0 9999px rgba(255, 255, 255, 0.12);
      pointer-events: none;
    }
    .progress.bottom { bottom: 0; }
    .progress.top { top: 0; }
    .progress[hidden] { display: none; }
    .bar {
      height: 100%;
      width: 0%;
      background: var(--ics-progress-color, var(--primary-color, #03a9f4));
    }
    .message {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      text-align: center;
      color: var(--primary-text-color, #fff);
      background: var(--card-background-color, #111);
      font-family: var(--paper-font-body1_-_font-family, sans-serif);
    }
    .message[hidden] { display: none; }
    /* Fullscreen: fill the screen and letterbox instead of cropping. */
    .frame:fullscreen,
    .frame:-webkit-full-screen {
      aspect-ratio: auto;
      width: 100vw;
      height: 100vh;
    }
    .frame:fullscreen .layer,
    .frame:-webkit-full-screen .layer { object-fit: contain; }
  </style>
  <ha-card>
    <div class="frame" id="frame">
      <img class="layer" id="layer-a" alt="">
      <img class="layer" id="layer-b" alt="">
      <div class="progress" id="progress"><div class="bar" id="bar"></div></div>
      <div class="message" id="message" hidden></div>
    </div>
  </ha-card>
`;

class ICloudSlideshowCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
    this._raf = null;
    this._src = null;
    this._front = null;
    this._windowStart = null;
    this._windowEnd = null;
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states || {}).find(
      (id) =>
        id.startsWith("camera.") &&
        hass.states[id].attributes.rotation_interval !== undefined
    );
    return { entity: entity || "camera.icloud_shared_album" };
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("You need to define an entity");
    }
    if (!config.entity.startsWith("camera.")) {
      throw new Error("Entity must be a camera");
    }
    this._config = { ...DEFAULTS, ...config };
    this._build();
    this._applyStyle();
    if (this._hass) this._render();
  }

  getCardSize() {
    return 6;
  }

  set hass(hass) {
    this._hass = hass;
    if (this._built) this._render();
  }

  connectedCallback() {
    this._startTicking();
  }

  disconnectedCallback() {
    this._stopTicking();
  }

  // ------------------------------------------------------------------
  // DOM
  // ------------------------------------------------------------------

  _build() {
    if (this._built) return;
    this.shadowRoot.innerHTML = TEMPLATE;
    const $ = (id) => this.shadowRoot.getElementById(id);
    this._frame = $("frame");
    this._a = $("layer-a");
    this._b = $("layer-b");
    this._progress = $("progress");
    this._bar = $("bar");
    this._message = $("message");
    this._frame.addEventListener("click", () => this._onTap());
    this._built = true;
    this._startTicking();
  }

  _applyStyle() {
    const c = this._config;
    this.style.setProperty("--ics-ratio", this._parseRatio(c.aspect_ratio));
    this.style.setProperty("--ics-fit", c.fit);
    this.style.setProperty("--ics-transition", `${c.transition}ms`);
    this.style.setProperty("--ics-progress-height", `${c.progress_height}px`);
    if (c.progress_color) {
      this.style.setProperty("--ics-progress-color", c.progress_color);
    }
    this._progress.className = `progress ${
      c.progress_position === "top" ? "top" : "bottom"
    }`;
    this._progress.hidden = c.show_progress === false;
    this._frame.classList.toggle("tappable", c.tap_action !== "none");
  }

  _parseRatio(ratio) {
    if (typeof ratio === "number") return String(ratio);
    const match = String(ratio || "").match(/^\s*(\d*\.?\d+)\s*[:/]\s*(\d*\.?\d+)\s*$/);
    return match ? `${match[1]} / ${match[2]}` : "16 / 9";
  }

  // ------------------------------------------------------------------
  // State
  // ------------------------------------------------------------------

  _render() {
    const stateObj = this._hass.states[this._config.entity];

    if (!stateObj) {
      this._showMessage(`Entity not found: ${this._config.entity}`);
      return;
    }
    if (stateObj.state === "unavailable") {
      this._showMessage("Slideshow unavailable");
      return;
    }

    const picture = stateObj.attributes.entity_picture;
    if (!picture) {
      this._showMessage("Waiting for the first photo…");
      return;
    }

    this._showMessage(null);

    const changed = picture !== this._src;
    if (changed) this._swap(picture);
    this._syncTiming(stateObj.attributes, changed);
  }

  _showMessage(text) {
    this._message.hidden = !text;
    if (text) this._message.textContent = text;
  }

  _swap(src) {
    this._src = src;
    const incoming = this._front === this._a ? this._b : this._a;
    const outgoing = this._front;

    incoming.onload = () => {
      incoming.classList.add("show");
      if (outgoing && outgoing !== incoming) outgoing.classList.remove("show");
      this._front = incoming;
    };
    incoming.onerror = () => {
      // Keep the previous photo on screen rather than flashing a broken image.
      incoming.onload = null;
    };
    incoming.src = src;
  }

  /**
   * Work out the window the progress bar spans.
   *
   * On an actual photo change we anchor to the browser clock so the bar stays
   * accurate even if the HA host and this device disagree about the time; on
   * first paint we fall back to the timestamps the entity reports.
   */
  _syncTiming(attrs, changed) {
    const interval = Number(attrs.rotation_interval);
    if (!interval || interval <= 0) {
      this._windowStart = this._windowEnd = null;
      return;
    }

    if (changed || this._windowStart === null) {
      const start = Date.parse(attrs.last_change || "");
      const end = Date.parse(attrs.next_change || "");
      if (!changed && !Number.isNaN(start) && !Number.isNaN(end) && end > start) {
        this._windowStart = start;
        this._windowEnd = end;
      } else {
        this._windowStart = Date.now();
        this._windowEnd = this._windowStart + interval * 1000;
      }
    }
  }

  // ------------------------------------------------------------------
  // Progress bar
  // ------------------------------------------------------------------

  _startTicking() {
    if (this._raf !== null || !this._built) return;
    const tick = () => {
      this._paint();
      this._raf = requestAnimationFrame(tick);
    };
    this._raf = requestAnimationFrame(tick);
  }

  _stopTicking() {
    if (this._raf !== null) {
      cancelAnimationFrame(this._raf);
      this._raf = null;
    }
  }

  _paint() {
    if (!this._bar || this._windowStart === null || this._windowEnd === null) return;
    const span = this._windowEnd - this._windowStart;
    if (span <= 0) return;
    const progress = Math.min(1, Math.max(0, (Date.now() - this._windowStart) / span));
    this._bar.style.width = `${(progress * 100).toFixed(2)}%`;
  }

  // ------------------------------------------------------------------
  // Interaction
  // ------------------------------------------------------------------

  _onTap() {
    const action = this._config.tap_action;
    if (action === "none") return;
    if (action === "more-info") {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          detail: { entityId: this._config.entity },
          bubbles: true,
          composed: true,
        })
      );
      return;
    }
    this._toggleFullscreen();
  }

  _toggleFullscreen() {
    const active = document.fullscreenElement || document.webkitFullscreenElement;
    if (active) {
      const exit = document.exitFullscreen || document.webkitExitFullscreen;
      if (exit) exit.call(document);
      return;
    }
    const request =
      this._frame.requestFullscreen || this._frame.webkitRequestFullscreen;
    if (request) request.call(this._frame);
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, ICloudSlideshowCard);

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TAG,
    name: "iCloud Slideshow",
    description:
      "Photo slideshow with a rotation progress bar and a fullscreen view that keeps rotating.",
    documentationURL: "https://github.com/Stephonomon/icloud_slideshow_hacs#lovelace-dashboard",
  });

  console.info(
    `%c ICLOUD-SLIDESHOW-CARD %c ${CARD_VERSION} `,
    "color:#fff;background:#3a7bd5;font-weight:700",
    "color:#3a7bd5;background:#fff;font-weight:700"
  );
}
