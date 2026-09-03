"use strict";

/**
 * Header canlı arama: kullanıcı yazarken /products/search/?q=... (JSON) çağrılır,
 * sonuçlar search-box'ın altında dropdown olarak listelenir. Bir sonuca
 * tıklanınca (veya Enter/ok tuşlarıyla seçilince) doğrudan o ürünün
 * sayfasına gidilir. Enter/ARA butonu, dropdown açık değilken hâlâ normal
 * form submit ile products:list?q=... sayfasına gönderir (mevcut davranış).
 *
 * Sayfada birden fazla arama kutusu olabilir (masaüstü header + mobil
 * sidebar) — her biri kendi bağımsız state/debounce'una sahip olacak
 * şekilde ayrı ayrı bağlanıyor (querySelectorAll + forEach), tek bir
 * querySelector değil.
 */
document.querySelectorAll("[data-search-container]").forEach((form) => {
  const input = form.querySelector("[data-search-input]");
  const resultsBox = form.querySelector("[data-search-results]");
  if (!input || !resultsBox) return;

  const MIN_CHARS = 2;
  const DEBOUNCE_MS = 300;

  let debounceTimer = null;
  let activeController = null;
  let activeIndex = -1;
  let currentItems = [];

  const escapeHtml = (str) =>
    String(str).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));

  const closeResults = () => {
    resultsBox.classList.remove("active");
    resultsBox.innerHTML = "";
    activeIndex = -1;
    currentItems = [];
  };

  const renderEmpty = () => {
    resultsBox.innerHTML = `<div class="search-empty">Sonuç bulunamadı</div>`;
    resultsBox.classList.add("active");
    currentItems = [];
    activeIndex = -1;
  };

  const renderResults = (results) => {
    currentItems = results;
    activeIndex = -1;

    resultsBox.innerHTML = results
      .map(
        (item) => `
        <a href="${escapeHtml(item.url)}" class="search-result-item" data-search-result>
          <i class="fa-solid fa-magnifying-glass"></i>
          <div class="search-result-text">
            <span class="search-result-name">${escapeHtml(item.name)}${item.is_sold_out ? " (Tükendi)" : ""}</span>
            <span class="search-result-category">${escapeHtml(item.category)}</span>
          </div>
        </a>`
      )
      .join("");

    resultsBox.classList.add("active");
  };

  const fetchResults = (query) => {
    if (activeController) activeController.abort();
    activeController = new AbortController();

    fetch(`/products/search/?q=${encodeURIComponent(query)}`, { signal: activeController.signal })
      .then((res) => res.json())
      .then((data) => {
        if (!data.results || data.results.length === 0) {
          renderEmpty();
        } else {
          renderResults(data.results);
        }
      })
      .catch((err) => {
        if (err.name !== "AbortError") closeResults();
      });
  };

  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearTimeout(debounceTimer);

    if (query.length < MIN_CHARS) {
      closeResults();
      return;
    }

    debounceTimer = setTimeout(() => fetchResults(query), DEBOUNCE_MS);
  });

  // Klavyeyle gezinme: ok aşağı/yukarı arasında seçim yapar, Enter seçileni açar.
  input.addEventListener("keydown", (e) => {
    const items = resultsBox.querySelectorAll("[data-search-result]");
    if (!items.length || !resultsBox.classList.contains("active")) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      activeIndex = (activeIndex - 1 + items.length) % items.length;
    } else if (e.key === "Enter" && activeIndex > -1) {
      e.preventDefault();
      window.location.href = items[activeIndex].getAttribute("href");
      return;
    } else if (e.key === "Escape") {
      closeResults();
      return;
    } else {
      return;
    }

    items.forEach((el, i) => el.classList.toggle("active", i === activeIndex));
  });

  // Dışarı tıklanınca kapansın.
  document.addEventListener("click", (e) => {
    if (!form.contains(e.target)) closeResults();
  });

  // Sonuca tıklamak zaten <a href> ile sayfaya gider; form submit'ini engellemeye gerek yok.
  input.addEventListener("focus", () => {
    if (input.value.trim().length >= MIN_CHARS && currentItems.length) {
      resultsBox.classList.add("active");
    }
  });
});