function normalizeProjectSearchText(value) {
    return String(value || "")
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
}

function showProjectTab(selector) {
    const trigger = document.querySelector('[href="' + selector + '"]');
    if (!trigger) {
        return;
    }

    if (window.bootstrap && window.bootstrap.Tab) {
        window.bootstrap.Tab.getOrCreateInstance(trigger).show();
        return;
    }

    trigger.click();
}

function setupProjectCardSearch() {
    const searchInput = document.getElementById("search");
    const cards = Array.from(document.querySelectorAll("[data-project-card]"));
    const noResult = document.getElementById("project-search-empty");
    const noResultTitle = document.getElementById("project-search-empty-title");
    const noResultMessage = document.getElementById("project-search-empty-message");
    const paginationSections = Array.from(
        document.querySelectorAll("#projects-section, #archived-projects-section")
    );

    if (!searchInput || !cards.length) {
        return;
    }

    function applyProjectSearch() {
        const query = normalizeProjectSearchText(searchInput.value);
        const hasQuery = Boolean(query);
        const matchCounts = { active: 0, archived: 0 };
        let totalMatches = 0;

        cards.forEach(function (card) {
            const searchText = normalizeProjectSearchText(card.dataset.searchText);
            const matches = !query || searchText.includes(query);
            card.style.display = matches ? "" : "none";

            if (matches) {
                totalMatches += 1;
                const paneKey = card.dataset.projectPane;
                if (paneKey && Object.prototype.hasOwnProperty.call(matchCounts, paneKey)) {
                    matchCounts[paneKey] += 1;
                }
            }
        });

        paginationSections.forEach(function (section) {
            section.style.display = hasQuery ? "none" : "";
        });

        if (!hasQuery || totalMatches > 0) {
            if (noResult) {
                noResult.style.display = "none";
            }
        } else if (noResult) {
            noResult.style.display = "block";
            if (noResultTitle) {
                noResultTitle.textContent = searchInput.value.trim() + " Not found";
            }
            if (noResultMessage) {
                noResultMessage.textContent =
                    "No projects matched that search, technician, name, or description.";
            }
        }

        if (hasQuery && totalMatches > 0) {
            const activePane = document.querySelector(".tab-pane.show.active");
            if (activePane) {
                const activeKey = activePane.id === "archived-projects" ? "archived" : "active";
                if (matchCounts[activeKey] === 0) {
                    if (matchCounts.active > 0) {
                        showProjectTab("#active-projects");
                    } else if (matchCounts.archived > 0) {
                        showProjectTab("#archived-projects");
                    }
                }
            }
        }
    }

    searchInput.addEventListener("input", applyProjectSearch);
}

function setupProjectDeleteButtons() {
    document.querySelectorAll(".delete-project").forEach(function (button) {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            const form = button.closest("form");
            if (form) {
                form.submit();
            }
        });
    });
}

function setupProjectFavouriteButtons() {
    document.querySelectorAll(".favourite-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            button.classList.toggle("active");
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    setupProjectFavouriteButtons();
    setupProjectDeleteButtons();
    setupProjectCardSearch();
});
