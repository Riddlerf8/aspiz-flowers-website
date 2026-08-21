"use strict";

/**
 * Ürün detay sayfası: galeri (küçük resme tıklayınca ana görsel + sayaç
 * değişir), fiyat kademesi kutuları (tıklanınca adet inputunu doldurur;
 * adet elle değiştirilince de doğru kademeyi otomatik vurgular) ve
 * açıklama/kargo/ödeme accordion'ı.
 */
(() => {
  // --- Gallery ---
  const mainImg = document.querySelector("[data-gallery-main]");
  const counter = document.querySelector("[data-gallery-counter]");
  const thumbs = document.querySelectorAll("[data-gallery-thumb]");

  thumbs.forEach((thumb, idx) => {
    thumb.addEventListener("click", () => {
      if (mainImg && mainImg.tagName === "IMG") {
        mainImg.src = thumb.dataset.fullSrc;
      }
      thumbs.forEach((t) => t.classList.remove("thumb-active"));
      thumb.classList.add("thumb-active");
      if (counter) counter.textContent = `${idx + 1}/${thumbs.length}`;
    });
  });

  // --- Price tier selector ---
  const tierBoxes = document.querySelectorAll("[data-tier-select]");
  const qtyInput = document.querySelector("[data-qty-input]");

  const highlightTierForQty = (qty) => {
    let active = null;
    tierBoxes.forEach((box) => {
      box.classList.remove("tier-active");
      if (qty >= parseInt(box.dataset.tierMinQty, 10)) active = box;
    });
    active?.classList.add("tier-active");
  };

  tierBoxes.forEach((box) => {
    box.addEventListener("click", () => {
      if (qtyInput) qtyInput.value = box.dataset.tierMinQty;
      tierBoxes.forEach((t) => t.classList.remove("tier-active"));
      box.classList.add("tier-active");
    });
  });

  qtyInput?.addEventListener("input", () => {
    const qty = parseInt(qtyInput.value, 10) || 0;
    highlightTierForQty(qty);
  });

  // --- Accordion ---
  document.querySelectorAll("[data-accordion-trigger]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const panel = btn.nextElementSibling;
      if (!panel) return;
      const isOpen = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!isOpen));
      panel.style.maxHeight = isOpen ? null : `${panel.scrollHeight}px`;
      btn.querySelector("[data-accordion-icon], .accordion-icon")?.classList.toggle("rotate-180", !isOpen);
    });
  });
})();
