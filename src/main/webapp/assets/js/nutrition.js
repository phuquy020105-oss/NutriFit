(() => {
    'use strict';

    document.querySelectorAll('[data-recipe-image]').forEach(img => {
        const fallback = () => {
            if (img.dataset.fallbackApplied) return;
            img.dataset.fallbackApplied = 'true';
            img.src = img.dataset.fallback;
        };
        img.addEventListener('error', fallback);
        if (img.complete && img.naturalWidth === 0) fallback();
    });

    document.querySelectorAll('[data-recipe-form]').forEach(form => {
        const meal = form.querySelector('[data-meal-select]');
        const recipe = form.querySelector('[data-recipe-select]');
        const empty = form.querySelector('[data-empty-recipes]');
        const submit = form.querySelector('button[type="submit"]');
        if (!meal || !recipe) return;

        const sync = () => {
            const selected = recipe.value;
            let first = null;
            let keepSelected = false;
            for (const option of recipe.options) {
                const matches = option.dataset.meal === meal.value;
                option.hidden = !matches;
                option.disabled = !matches;
                if (matches) {
                    if (!first) first = option;
                    if (option.value === selected) keepSelected = true;
                }
            }
            recipe.value = keepSelected ? selected : first ? first.value : '';
            recipe.disabled = !first;
            if (submit) submit.disabled = !first;
            if (empty) empty.hidden = Boolean(first);
        };
        meal.addEventListener('change', sync);
        sync();
    });

    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', event => {
            if (!window.confirm(form.dataset.confirm)) event.preventDefault();
        });
    });

    document.querySelectorAll('form[data-submit-once]').forEach(form => {
        let submitted = false;
        form.addEventListener('submit', event => {
            if (event.defaultPrevented) return;
            if (submitted) { event.preventDefault(); return; }
            submitted = true;
            form.querySelectorAll('button[type="submit"]').forEach(button => { button.disabled = true; });
        });
    });
})();
